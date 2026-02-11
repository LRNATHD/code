"""
MP3 Sync - Flask app for YouTube Music sync service.
Provides config API + sync control + web UI.
"""

import os
from functools import wraps
from flask import Flask, render_template, jsonify, request
import config
import sync_engine

app = Flask(__name__)
app.secret_key = os.urandom(24)


def require_password(f):
    """Decorator to require password for API actions."""
    @wraps(f)
    def decorated(*args, **kwargs):
        password = request.headers.get('X-Password', '')
        if not config.ACCESS_PASSWORD:
            return jsonify({'success': False, 'message': 'Password not configured'}), 500
        if password != config.ACCESS_PASSWORD:
            return jsonify({'success': False, 'message': 'Invalid password'}), 401
        return f(*args, **kwargs)
    return decorated


# ── Health ──────────────────────────────────────────
@app.route('/api/status')
def api_status():
    """Health check endpoint (required by service_manager)."""
    sync = sync_engine.get_sync_status()
    return jsonify({
        'status': 'ok',
        'sync_running': sync['running'],
        'last_sync': sync['last_sync'],
    })


# ── Config API (generic pattern: GET/POST /api/config) ──
@app.route('/api/config', methods=['GET'])
def api_get_config():
    """Return current sync configuration."""
    return jsonify(sync_engine.load_sync_config())


@app.route('/api/config', methods=['POST'])
@require_password
def api_set_config():
    """Update sync configuration."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400

    current = sync_engine.load_sync_config()
    # Only update known keys
    for key in ['download_folder', 'sync_liked_music', 'sync_all_playlists']:
        if key in data:
            current[key] = data[key]

    sync_engine.save_sync_config(current)
    return jsonify({'success': True, 'message': 'Config saved', 'config': current})


# ── Sync control ────────────────────────────────────
@app.route('/api/sync', methods=['POST'])
@require_password
def api_start_sync():
    """Trigger a manual sync."""
    success, message = sync_engine.start_sync()
    return jsonify({'success': success, 'message': message})


@app.route('/api/sync/stop', methods=['POST'])
@require_password
def api_stop_sync():
    """Stop a running sync."""
    success, message = sync_engine.stop_sync()
    return jsonify({'success': success, 'message': message})


@app.route('/api/sync/status')
def api_sync_status():
    """Get detailed sync progress."""
    return jsonify(sync_engine.get_sync_status())


# ── Web UI ──────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    print(f"MP3 Sync running on http://localhost:{config.PORT}")
    app.run(host=config.HOST, port=config.PORT, debug=False)
