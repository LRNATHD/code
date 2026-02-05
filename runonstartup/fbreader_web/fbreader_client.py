"""Client for interacting with FBReader Book Network."""
import sqlite3
import http.cookiejar
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import hashlib
import shutil

import config


@dataclass
class Book:
    """Represents a book from the library."""
    book_id: int
    title: str
    authors: list[str]
    cover_url: Optional[str]
    file_url: Optional[str]
    file_path: Optional[str]
    mime_type: str
    language: str
    series: Optional[str] = None
    series_index: Optional[str] = None
    annotation: Optional[str] = None
    progress: float = 0.0
    
    def to_dict(self):
        return {
            "book_id": self.book_id,
            "title": self.title,
            "authors": self.authors,
            "cover_url": self.cover_url,
            "file_url": self.file_url,
            "file_path": self.file_path,
            "mime_type": self.mime_type,
            "language": self.language,
            "series": self.series,
            "series_index": self.series_index,
            "annotation": self.annotation,
            "progress": self.progress,
        }


class FBReaderClient:
    """Client for accessing FBReader Book Network."""
    
    def __init__(self):
        self.session = requests.Session()
        self._load_cookies()
        
    def _load_cookies(self):
        """Load cookies from FBReader's cookie file."""
        if not config.FBREADER_COOKIES.exists():
            print(f"Warning: Cookie file not found at {config.FBREADER_COOKIES}")
            return
            
        # Parse Netscape cookie file format
        cookie_jar = http.cookiejar.MozillaCookieJar()
        try:
            cookie_jar.load(str(config.FBREADER_COOKIES), ignore_discard=True, ignore_expires=True)
            self.session.cookies.update(cookie_jar)
            print(f"Loaded {len(cookie_jar)} cookies from FBReader")
        except Exception as e:
            print(f"Error loading cookies: {e}")
            # Fallback: manually parse the cookie file
            self._parse_cookies_manually()
    
    def _parse_cookies_manually(self):
        """Manually parse the cookie file if the standard loader fails."""
        try:
            with open(config.FBREADER_COOKIES, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = line.split('\t')
                    if len(parts) >= 7:
                        domain = parts[0].lstrip('#HttpOnly_')
                        name = parts[5]
                        value = parts[6]
                        self.session.cookies.set(name, value, domain=domain)
                        print(f"Loaded cookie: {name} for {domain}")
        except Exception as e:
            print(f"Error manually parsing cookies: {e}")
    
    def get_local_library(self) -> list[Book]:
        """Get books from the local FBReader SQLite database."""
        if not config.FBREADER_DB.exists():
            print(f"Database not found at {config.FBREADER_DB}")
            return []
            
        books = []
        conn = sqlite3.connect(str(config.FBREADER_DB))
        cursor = conn.cursor()
        
        # Query all books with their metadata
        query = """
        SELECT 
            b.book_id,
            b.title,
            b.language,
            bf.path as file_path,
            bf.location,
            bf.mime,
            bc.path as cover_path,
            COALESCE(bp.progress_numerator * 100.0 / NULLIF(bp.progress_denominator, 0), 0) as progress,
            ba_text.text as annotation,
            s.title as series_title,
            bs.book_index as series_index
        FROM Book b
        LEFT JOIN BookFile bf ON b.book_id = bf.book_id
        LEFT JOIN BookCover bc ON b.book_id = bc.book_id
        LEFT JOIN BookPosition bp ON b.book_id = bp.book_id
        LEFT JOIN BookAnnotation ba_text ON b.book_id = ba_text.book_id
        LEFT JOIN BookSeries bs ON b.book_id = bs.book_id
        LEFT JOIN Series s ON bs.series_id = s.series_id
        ORDER BY b.title
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        for row in rows:
            book_id = row[0]
            
            # Get authors
            cursor.execute("""
                SELECT a.name FROM Author a
                JOIN BookAuthor ba ON a.author_id = ba.author_id
                WHERE ba.book_id = ?
                ORDER BY ba.author_index
            """, (book_id,))
            authors = [r[0] for r in cursor.fetchall()]
            
            file_path = row[3]
            location = row[4]
            cover_path = row[6]
            
            # Determine file source based on location type
            file_url = None
            local_path = None
            cover_url = None
            
            if location == 'e':
                # External/remote URL (public books from data.fbreader.org)
                file_url = file_path
                cover_url = cover_path
            elif location == 'l':
                # Local file - parse the FBReader local file format
                # Format is: "version;length;path"
                if file_path and ';' in file_path:
                    parts = file_path.split(';', 2)
                    if len(parts) >= 3:
                        local_path = parts[2]
                else:
                    local_path = file_path
            elif location and location.startswith('c#'):
                # Cloud storage (Google Drive via books.fbreader.org)
                # Format: c#email@example.com
                if file_path:
                    file_url = f"https://books.fbreader.org{file_path}"
                if cover_path:
                    cover_url = f"https://books.fbreader.org{cover_path}"
            
            book = Book(
                book_id=book_id,
                title=row[1],
                authors=authors,
                language=row[2] or "en",
                file_url=file_url,
                file_path=local_path,
                mime_type=row[5] or "application/epub+zip",
                cover_url=cover_url,
                progress=row[7] or 0.0,
                annotation=row[8],
                series=row[9],
                series_index=row[10],
            )
            books.append(book)
        
        conn.close()
        return books
    
    def fetch_opds_catalog(self) -> Optional[str]:
        """Fetch the OPDS catalog from FBReader Book Network."""
        try:
            response = self.session.get(
                config.FBREADER_OPDS_URL,
                headers={
                    "Accept": "application/atom+xml",
                    "User-Agent": "FBReader/3.0"
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.text
            else:
                print(f"OPDS fetch failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error fetching OPDS: {e}")
            return None
    
    def download_book(self, book: Book) -> Optional[Path]:
        """Download a book to local cache, prioritizing local files."""
        # First, check if there's a local file
        if book.file_path:
            local_path = Path(book.file_path)
            if local_path.exists():
                print(f"Using local file: {book.title}")
                return local_path
        
        # No URL to download from
        if not book.file_url:
            print(f"No file source for: {book.title}")
            return None
        
        # Create cache filename based on URL hash
        url_hash = hashlib.md5(book.file_url.encode()).hexdigest()
        ext = ".epub" if "epub" in book.mime_type.lower() else ".fb2"
        cache_path = config.CACHE_DIR / f"{url_hash}{ext}"
        
        if cache_path.exists():
            print(f"Using cached: {book.title}")
            return cache_path
        
        try:
            print(f"Downloading: {book.title} from {book.file_url[:60]}...")
            
            # Set up headers - more headers for books.fbreader.org
            headers = {
                "User-Agent": "FBReader/3.0",
                "Accept": "application/epub+zip, application/octet-stream, */*",
            }
            
            # For books.fbreader.org, add referer
            if "books.fbreader.org" in book.file_url:
                headers["Referer"] = "https://books.fbreader.org/"
                headers["Origin"] = "https://books.fbreader.org"
            
            response = self.session.get(
                book.file_url,
                headers=headers,
                stream=True,
                timeout=120,
                allow_redirects=True
            )
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                # Make sure we're getting actual book content, not HTML error page
                if 'html' in content_type.lower():
                    print(f"Got HTML instead of book (authentication issue?)")
                    return None
                    
                with open(cache_path, 'wb') as f:
                    shutil.copyfileobj(response.raw, f)
                print(f"Downloaded successfully: {cache_path}")
                return cache_path
            elif response.status_code == 401 or response.status_code == 403:
                print(f"Authentication required - cookies may have expired")
                return None
            else:
                print(f"Download failed with status {response.status_code}")
                return None
        except Exception as e:
            print(f"Error downloading book: {e}")
            return None
    
    def get_book_content(self, book_id: int) -> Optional[bytes]:
        """Get the content of a book by ID."""
        books = self.get_local_library()
        
        # Find all entries for this book (could be multiple with different locations)
        matching_books = [b for b in books if b.book_id == book_id]
        
        if not matching_books:
            return None
        
        # Try each entry, preferring local files
        local_books = [b for b in matching_books if b.file_path]
        cloud_books = [b for b in matching_books if b.file_url]
        
        # Try local files first
        for book in local_books:
            path = self.download_book(book)
            if path and path.exists():
                return path.read_bytes()
        
        # Then try cloud/remote files
        for book in cloud_books:
            path = self.download_book(book)
            if path and path.exists():
                return path.read_bytes()
        
        return None
    
    def update_reading_position(self, book_id: int, paragraph: int, word: int = 0, char: int = 0, progress: float = 0):
        """Update reading position in the local database."""
        if not config.FBREADER_DB.exists():
            return False
            
        try:
            conn = sqlite3.connect(str(config.FBREADER_DB), timeout=5)
            cursor = conn.cursor()
            
            import time
            timestamp = int(time.time())
            
            # Calculate progress as percentage (0-100 mapped to numerator/100)
            progress_num = int(progress)
            progress_den = 100
            
            # Check if position exists
            cursor.execute("SELECT book_id FROM BookPosition WHERE book_id = ?", (book_id,))
            if cursor.fetchone():
                cursor.execute("""
                    UPDATE BookPosition 
                    SET paragraph = ?, word = ?, char = ?, 
                        progress_numerator = ?, progress_denominator = ?,
                        timestamp = ?
                    WHERE book_id = ?
                """, (paragraph, word, char, progress_num, progress_den, timestamp, book_id))
            else:
                cursor.execute("""
                    INSERT INTO BookPosition 
                    (book_id, paragraph, word, char, progress_numerator, progress_denominator, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (book_id, paragraph, word, char, progress_num, progress_den, timestamp))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating position: {e}")
            return False


# Singleton instance
_client = None

def get_client() -> FBReaderClient:
    global _client
    if _client is None:
        _client = FBReaderClient()
    return _client
