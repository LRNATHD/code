"""Flask web application for Instagram Watermark Remover."""

import os
import json
import threading
from pathlib import Path
from typing import Optional
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    send_from_directory,
    session,
)
from flask_cors import CORS

from config import (
    FLASK_SECRET_KEY,
    FLASK_DEBUG,
    DOWNLOADS_DIR,
    PROCESSED_DIR,
    CREDENTIALS_FILE,
    WATERMARK_POSITION,
)
from google_photos import photos_client
from watermark_remover import watermark_remover

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = FLASK_SECRET_KEY
CORS(app)

# Processing state
processing_state = {
    "is_processing": False,
    "current": 0,
    "total": 0,
    "status": "idle",
    "results": None,
}


@app.route("/")
def index():
    """Render the main page."""
    is_authenticated = photos_client.is_authenticated()
    has_credentials = CREDENTIALS_FILE.exists()
    
    return render_template(
        "index.html",
        is_authenticated=is_authenticated,
        has_credentials=has_credentials,
    )


@app.route("/api/status")
def api_status():
    """Get current application status."""
    return jsonify({
        "authenticated": photos_client.is_authenticated(),
        "has_credentials": CREDENTIALS_FILE.exists(),
        "iopaint_available": watermark_remover.iopaint_available,
        "processing": processing_state,
    })


@app.route("/auth/login")
def auth_login():
    """Start OAuth flow."""
    try:
        redirect_uri = request.url_root.rstrip("/") + "/oauth2callback"
        auth_url = photos_client.authenticate(redirect_uri)
        return redirect(auth_url)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/oauth2callback")
def oauth_callback():
    """Handle OAuth callback."""
    try:
        redirect_uri = request.url_root.rstrip("/") + "/oauth2callback"
        photos_client.complete_authentication(request.url, redirect_uri)
        return redirect(url_for("index"))
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/auth/logout")
def auth_logout():
    """Log out and clear credentials."""
    from config import TOKEN_FILE
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
    return redirect(url_for("index"))


@app.route("/api/albums")
def api_albums():
    """Get list of albums."""
    if not photos_client.is_authenticated():
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        albums = photos_client.list_albums()
        return jsonify({"albums": albums})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/photos")
def api_photos():
    """Get list of photos."""
    if not photos_client.is_authenticated():
        return jsonify({"error": "Not authenticated"}), 401
    
    album_id = request.args.get("album_id")
    page_size = int(request.args.get("page_size", 50))
    
    try:
        items = photos_client.list_media_items(page_size=page_size, album_id=album_id)
        # Filter to only images
        photos = [
            item for item in items
            if item.get("mimeType", "").startswith("image/")
        ]
        return jsonify({"photos": photos})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/download", methods=["POST"])
def api_download():
    """Download selected photos."""
    if not photos_client.is_authenticated():
        return jsonify({"error": "Not authenticated"}), 401
    
    data = request.get_json()
    photo_ids = data.get("photo_ids", [])
    
    if not photo_ids:
        return jsonify({"error": "No photos selected"}), 400
    
    try:
        # Get full media items for selected photos
        downloaded = []
        for photo_id in photo_ids:
            # Fetch photo details
            item = photos_client.service.mediaItems().get(mediaItemId=photo_id).execute()
            path = photos_client.download_photo(item)
            if path:
                downloaded.append(str(path))
        
        return jsonify({
            "success": True,
            "downloaded": len(downloaded),
            "files": downloaded
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/local-photos")
def api_local_photos():
    """Get list of downloaded photos."""
    photos = []
    
    for img_path in DOWNLOADS_DIR.glob("*"):
        if img_path.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
            photos.append({
                "name": img_path.name,
                "path": str(img_path),
                "size": img_path.stat().st_size,
                "modified": datetime.fromtimestamp(img_path.stat().st_mtime).isoformat(),
            })
    
    return jsonify({"photos": photos})


@app.route("/api/processed-photos")
def api_processed_photos():
    """Get list of processed photos."""
    photos = []
    
    for img_path in PROCESSED_DIR.glob("*"):
        if img_path.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
            photos.append({
                "name": img_path.name,
                "path": str(img_path),
                "size": img_path.stat().st_size,
                "modified": datetime.fromtimestamp(img_path.stat().st_mtime).isoformat(),
            })
    
    return jsonify({"photos": photos})


def processing_callback(current, total, status):
    """Callback for batch processing progress."""
    processing_state["current"] = current
    processing_state["total"] = total
    processing_state["status"] = status


def run_batch_processing(image_paths, position):
    """Run batch processing in background thread."""
    global processing_state
    
    processing_state["is_processing"] = True
    processing_state["current"] = 0
    processing_state["total"] = len(image_paths)
    processing_state["status"] = "Starting..."
    
    try:
        results = watermark_remover.batch_process(
            image_paths,
            position=position,
            callback=processing_callback
        )
        processing_state["results"] = results
        processing_state["status"] = "Complete"
    except Exception as e:
        processing_state["status"] = f"Error: {str(e)}"
        processing_state["results"] = {"error": str(e)}
    finally:
        processing_state["is_processing"] = False


@app.route("/api/process", methods=["POST"])
def api_process():
    """Start processing downloaded photos."""
    global processing_state
    
    if processing_state["is_processing"]:
        return jsonify({"error": "Processing already in progress"}), 400
    
    data = request.get_json() or {}
    file_names = data.get("files")  # Optional: specific files to process
    position = data.get("position", WATERMARK_POSITION)
    
    # Get files to process
    if file_names:
        image_paths = [DOWNLOADS_DIR / f for f in file_names if (DOWNLOADS_DIR / f).exists()]
    else:
        image_paths = list(DOWNLOADS_DIR.glob("*"))
        image_paths = [p for p in image_paths if p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]]
    
    if not image_paths:
        return jsonify({"error": "No images to process"}), 400
    
    # Start background processing
    thread = threading.Thread(
        target=run_batch_processing,
        args=(image_paths, position)
    )
    thread.start()
    
    return jsonify({
        "success": True,
        "message": f"Started processing {len(image_paths)} images",
        "total": len(image_paths)
    })


@app.route("/api/process/status")
def api_process_status():
    """Get processing status."""
    return jsonify(processing_state)


@app.route("/api/process/single", methods=["POST"])
def api_process_single():
    """Process a single image (for preview/testing)."""
    data = request.get_json()
    file_name = data.get("file")
    position = data.get("position", "auto")
    
    if not file_name:
        return jsonify({"error": "No file specified"}), 400
    
    # Check in downloads first, then use as full path
    image_path = DOWNLOADS_DIR / file_name
    if not image_path.exists():
        image_path = Path(file_name)
    
    if not image_path.exists():
        return jsonify({"error": "File not found"}), 404
    
    try:
        output_path = watermark_remover.remove_watermark(image_path, position=position)
        
        if output_path and output_path.exists():
            return jsonify({
                "success": True,
                "output": str(output_path),
                "output_name": output_path.name
            })
        else:
            return jsonify({"error": "Processing failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/detect-watermark", methods=["POST"])
def api_detect_watermark():
    """Detect watermark region in an image."""
    data = request.get_json()
    file_name = data.get("file")
    
    if not file_name:
        return jsonify({"error": "No file specified"}), 400
    
    image_path = DOWNLOADS_DIR / file_name
    if not image_path.exists():
        image_path = Path(file_name)
    
    if not image_path.exists():
        return jsonify({"error": "File not found"}), 404
    
    try:
        region = watermark_remover.detect_watermark_region(image_path, "auto")
        
        if region:
            return jsonify({
                "success": True,
                "region": {
                    "x1": region[0],
                    "y1": region[1],
                    "x2": region[2],
                    "y2": region[3],
                }
            })
        else:
            return jsonify({"error": "Could not detect watermark"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/images/downloads/<path:filename>")
def serve_download(filename):
    """Serve downloaded images."""
    return send_from_directory(DOWNLOADS_DIR, filename)


@app.route("/images/processed/<path:filename>")
def serve_processed(filename):
    """Serve processed images."""
    return send_from_directory(PROCESSED_DIR, filename)


@app.route("/api/upload", methods=["POST"])
def api_upload():
    """Upload local images for processing."""
    if "files" not in request.files:
        return jsonify({"error": "No files provided"}), 400
    
    files = request.files.getlist("files")
    uploaded = []
    
    for file in files:
        if file.filename:
            # Save to downloads directory
            filepath = DOWNLOADS_DIR / file.filename
            file.save(filepath)
            uploaded.append(file.filename)
    
    return jsonify({
        "success": True,
        "uploaded": len(uploaded),
        "files": uploaded
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=FLASK_DEBUG)
