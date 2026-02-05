"""Google Photos API authentication and photo fetching."""

import pickle
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import requests

from config import (
    SCOPES,
    CREDENTIALS_FILE,
    TOKEN_FILE,
    DOWNLOADS_DIR,
    SUPPORTED_FORMATS,
)


class GooglePhotosClient:
    """Client for interacting with Google Photos API."""
    
    def __init__(self):
        self.credentials: Optional[Credentials] = None
        self.service = None
    
    def is_authenticated(self) -> bool:
        """Check if we have valid credentials."""
        if self.credentials and self.credentials.valid:
            return True
        
        if self.credentials and self.credentials.expired and self.credentials.refresh_token:
            try:
                self.credentials.refresh(Request())
                self._save_credentials()
                return True
            except Exception:
                return False
        
        return self._load_credentials()
    
    def _load_credentials(self) -> bool:
        """Load credentials from token file."""
        if TOKEN_FILE.exists():
            try:
                with open(TOKEN_FILE, "rb") as token:
                    self.credentials = pickle.load(token)
                
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                    self._save_credentials()
                
                return self.credentials is not None and self.credentials.valid
            except Exception:
                return False
        return False
    
    def _save_credentials(self):
        """Save credentials to token file."""
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(self.credentials, token)
    
    def authenticate(self, redirect_uri: str = "http://localhost:5000/oauth2callback") -> str:
        """Start OAuth flow and return authorization URL."""
        if not CREDENTIALS_FILE.exists():
            raise FileNotFoundError(
                f"Client secrets file not found at {CREDENTIALS_FILE}. "
                "Please download it from Google Cloud Console."
            )
        
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_FILE),
            SCOPES,
            redirect_uri=redirect_uri
        )
        
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent"
        )
        
        return auth_url
    
    def complete_authentication(self, authorization_response: str, redirect_uri: str = "http://localhost:5000/oauth2callback"):
        """Complete OAuth flow with authorization response."""
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_FILE),
            SCOPES,
            redirect_uri=redirect_uri
        )
        
        flow.fetch_token(authorization_response=authorization_response)
        self.credentials = flow.credentials
        self._save_credentials()
        
        self.service = build("photoslibrary", "v1", credentials=self.credentials, static_discovery=False)
    
    def _ensure_service(self):
        """Ensure the service is initialized."""
        if not self.service:
            if not self.is_authenticated():
                raise RuntimeError("Not authenticated. Please authenticate first.")
            self.service = build("photoslibrary", "v1", credentials=self.credentials, static_discovery=False)
    
    def list_albums(self, page_size: int = 50) -> List[Dict[str, Any]]:
        """List all albums in the user's library."""
        self._ensure_service()
        
        albums = []
        next_page_token = None
        
        while True:
            results = self.service.albums().list(
                pageSize=page_size,
                pageToken=next_page_token
            ).execute()
            
            albums.extend(results.get("albums", []))
            next_page_token = results.get("nextPageToken")
            
            if not next_page_token:
                break
        
        return albums
    
    def list_media_items(self, page_size: int = 100, album_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List media items, optionally filtered by album."""
        self._ensure_service()
        
        items = []
        next_page_token = None
        
        while True:
            if album_id:
                body = {
                    "albumId": album_id,
                    "pageSize": page_size,
                }
                if next_page_token:
                    body["pageToken"] = next_page_token
                
                results = self.service.mediaItems().search(body=body).execute()
            else:
                results = self.service.mediaItems().list(
                    pageSize=page_size,
                    pageToken=next_page_token
                ).execute()
            
            items.extend(results.get("mediaItems", []))
            next_page_token = results.get("nextPageToken")
            
            if not next_page_token or len(items) >= 500:  # Limit for demo
                break
        
        return items
    
    def download_photo(self, media_item: Dict[str, Any], output_dir: Optional[Path] = None) -> Optional[Path]:
        """Download a photo from Google Photos."""
        if output_dir is None:
            output_dir = DOWNLOADS_DIR
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = media_item.get("filename", f"photo_{media_item.get('id', 'unknown')}.jpg")
        
        # Check if supported format
        ext = Path(filename).suffix.lower()
        if ext not in SUPPORTED_FORMATS:
            print(f"Skipping unsupported format: {filename}")
            return None
        
        # Construct download URL with full resolution
        base_url = media_item.get("baseUrl")
        if not base_url:
            return None
        
        # Add parameters for full resolution download
        download_url = f"{base_url}=d"
        
        try:
            response = requests.get(download_url, timeout=60)
            response.raise_for_status()
            
            output_path = output_dir / filename
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            return output_path
        except Exception as e:
            print(f"Error downloading {filename}: {e}")
            return None
    
    def search_photos(
        self,
        date_range: Optional[Dict] = None,
        content_filter: Optional[Dict] = None,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """Search for photos with filters."""
        self._ensure_service()
        
        body = {"pageSize": page_size}
        
        filters = {}
        
        if date_range:
            filters["dateFilter"] = {
                "ranges": [date_range]
            }
        
        if content_filter:
            filters["contentFilter"] = content_filter
        
        if filters:
            body["filters"] = filters
        
        items = []
        next_page_token = None
        
        while True:
            if next_page_token:
                body["pageToken"] = next_page_token
            
            results = self.service.mediaItems().search(body=body).execute()
            items.extend(results.get("mediaItems", []))
            next_page_token = results.get("nextPageToken")
            
            if not next_page_token or len(items) >= 500:
                break
        
        return items


# Global client instance
photos_client = GooglePhotosClient()
