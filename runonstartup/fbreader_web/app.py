"""FBReader Web Reader - Flask Application."""
import os
import time
import hashlib
import functools
from datetime import datetime, timedelta
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    session,
    send_file,
    abort,
    make_response,
)
from flask_cors import CORS

import config
from fbreader_client import get_client, Book

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
CORS(app)

# Use ProxyFix to handle Cloudflare headers correctly
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Store authenticated IPs with their expiry times
authenticated_ips: dict[str, datetime] = {}


def get_client_ip() -> str:
    """Get the client's IP address."""
    # Check for proxy headers
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr or "unknown"


def is_authenticated() -> bool:
    """Check if current request is authenticated."""
    client_ip = get_client_ip()
    
    # Check session-based auth
    if session.get('authenticated'):
        return True
    
    # Check IP-based auth
    if client_ip in authenticated_ips:
        if authenticated_ips[client_ip] > datetime.now():
            return True
        else:
            # Expired, remove it
            del authenticated_ips[client_ip]
    
    return False


def require_auth(f):
    """Decorator to require authentication."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not is_authenticated():
            if request.is_json:
                return jsonify({"error": "Not authenticated"}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


@app.route('/')
def index():
    """Redirect to library or login."""
    if is_authenticated():
        return redirect(url_for('library'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with password authentication."""
    error = None
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        if password == config.ACCESS_PASSWORD:
            client_ip = get_client_ip()
            
            # Set session auth
            session['authenticated'] = True
            session.permanent = bool(remember)
            
            # Also set IP-based auth
            hours = config.SESSION_TIMEOUT_HOURS if remember else 1
            authenticated_ips[client_ip] = datetime.now() + timedelta(hours=hours)
            
            return redirect(url_for('library'))
        else:
            error = "Invalid password"
    
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    """Log out and clear authentication."""
    session.clear()
    client_ip = get_client_ip()
    if client_ip in authenticated_ips:
        del authenticated_ips[client_ip]
    return redirect(url_for('login'))


@app.route('/library')
@require_auth
def library():
    """Main library view."""
    return render_template('library.html')


@app.route('/api/books')
@require_auth
def api_books():
    """Get list of books."""
    client = get_client()
    books = client.get_local_library()
    return jsonify({
        "books": [b.to_dict() for b in books],
        "count": len(books)
    })


@app.route('/api/book/<int:book_id>')
@require_auth
def api_book(book_id: int):
    """Get details for a specific book."""
    client = get_client()
    books = client.get_local_library()
    book = next((b for b in books if b.book_id == book_id), None)
    
    if not book:
        return jsonify({"error": "Book not found"}), 404
    
    return jsonify(book.to_dict())


@app.route('/api/book/<int:book_id>/content')
@require_auth
def api_book_content(book_id: int):
    """Get book file content."""
    client = get_client()
    content = client.get_book_content(book_id)
    
    if not content:
        return jsonify({"error": "Book content not available"}), 404
    
    # Determine content type
    books = client.get_local_library()
    book = next((b for b in books if b.book_id == book_id), None)
    mime_type = book.mime_type if book else "application/epub+zip"
    
    response = make_response(content)
    response.headers['Content-Type'] = mime_type
    response.headers['Content-Disposition'] = f'inline; filename="book_{book_id}.epub"'
    return response


@app.route('/api/book/<int:book_id>/cover')
@require_auth  
def api_book_cover(book_id: int):
    """Get book cover image."""
    client = get_client()
    books = client.get_local_library()
    book = next((b for b in books if b.book_id == book_id), None)
    
    if not book or not book.cover_url:
        # Return a placeholder
        return redirect('/static/img/no-cover.svg')
    
    # Proxy the cover image
    try:
        response = client.session.get(book.cover_url, timeout=30)
        if response.status_code == 200:
            resp = make_response(response.content)
            resp.headers['Content-Type'] = response.headers.get('Content-Type', 'image/jpeg')
            resp.headers['Cache-Control'] = 'public, max-age=86400'
            return resp
    except Exception as e:
        print(f"Error fetching cover: {e}")
    
    return redirect('/static/img/no-cover.svg')


@app.route('/api/book/<int:book_id>/position', methods=['POST'])
@require_auth
def api_update_position(book_id: int):
    """Update reading position."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    paragraph = data.get('paragraph', 0)
    word = data.get('word', 0)
    char = data.get('char', 0)
    progress = data.get('progress', 0)  # Percentage 0-100
    
    client = get_client()
    success = client.update_reading_position(book_id, paragraph, word, char, progress)
    
    return jsonify({"success": success})


@app.route('/read/<int:book_id>')
@require_auth
def read_book(book_id: int):
    """Reader page for a book."""
    client = get_client()
    books = client.get_local_library()
    book = next((b for b in books if b.book_id == book_id), None)
    
    if not book:
        abort(404)
    
    return render_template('reader.html', book=book.to_dict())


@app.route('/api/status')
def api_status():
    """Get API status (public endpoint for health checks)."""
    return jsonify({
        "status": "ok",
        "authenticated": is_authenticated(),
        "timestamp": datetime.now().isoformat()
    })


if __name__ == '__main__':
    print(f"Starting FBReader Web Reader on http://{config.HOST}:{config.PORT}")
    print(f"FBReader data path: {config.FBREADER_DATA}")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
