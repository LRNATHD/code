"""
Service Manager Dashboard
Web UI for managing startup services.
"""

import os
from functools import wraps
from flask import Flask, render_template, jsonify, request
import requests
import manager

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Load port and password from config/env
config = manager.load_config()
PORT = config.get('manager', {}).get('port', 9870)

# Password from environment (same as other startup apps)
def get_password():
    # Try env first
    pwd = os.environ.get('STARTUP_APPS_PASSWORD')
    if pwd:
        return pwd
    # Try Windows registry
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment")
        pwd, _ = winreg.QueryValueEx(key, "STARTUP_APPS_PASSWORD")
        winreg.CloseKey(key)
        return pwd
    except:
        return None


def require_password(f):
    """Decorator to require password for API actions."""
    @wraps(f)
    def decorated(*args, **kwargs):
        password = request.headers.get('X-Password', '')
        expected = get_password()
        
        if not expected:
            return jsonify({'success': False, 'message': 'Password not configured on server'})
        
        if password != expected:
            return jsonify({'success': False, 'message': 'Invalid password'})
        
        return f(*args, **kwargs)
    return decorated


@app.route('/')
def index():
    """Dashboard home page."""
    return render_template('index.html')


@app.route('/api/status')
def api_status():
    """Get status of all services as JSON."""
    statuses = manager.get_all_status()
    return jsonify({
        'services': [
            {
                'id': s.id,
                'name': s.name,
                'running': s.running,
                'healthy': s.healthy,
                'port': s.port,
                'pid': s.pid
            }
            for s in statuses
        ],
        'tasks': manager.get_all_tasks()
    })


@app.route('/api/service/<service_id>/start', methods=['POST'])
@require_password
def api_start_service(service_id):
    """Start a service."""
    success, message = manager.start_service(service_id)
    return jsonify({'success': success, 'message': message})


@app.route('/api/service/<service_id>/stop', methods=['POST'])
@require_password
def api_stop_service(service_id):
    """Stop a service."""
    success, message = manager.stop_service(service_id)
    return jsonify({'success': success, 'message': message})


@app.route('/api/service/<service_id>/restart', methods=['POST'])
@require_password
def api_restart_service(service_id):
    """Restart a service."""
    success, message = manager.restart_service(service_id)
    return jsonify({'success': success, 'message': message})


@app.route('/api/task/<task_id>/run', methods=['POST'])
@require_password
def api_run_task(task_id):
    """Run a task."""
    success, message = manager.run_task(task_id)
    return jsonify({'success': success, 'message': message})


@app.route('/api/voles')
def api_voles():
    """Fetch non-NSFW image posts from r/voles."""
    try:
        resp = requests.get(
            'https://www.reddit.com/r/voles.json?limit=50',
            headers={'User-Agent': 'ServiceManager/1.0'}
        )
        data = resp.json()
        images = []
        for post in data.get('data', {}).get('children', []):
            p = post.get('data', {})
            if p.get('over_18'):
                continue
            url = p.get('url', '')
            if url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                images.append(url)
            # Check for Reddit-hosted images
            preview = p.get('preview', {}).get('images', [])
            if preview:
                src = preview[0].get('source', {}).get('url', '').replace('&amp;', '&')
                if src:
                    images.append(src)
        return jsonify({'images': list(set(images))})
    except Exception as e:
        return jsonify({'images': [], 'error': str(e)})


if __name__ == '__main__':
    print(f"Service Manager Dashboard running on http://localhost:{PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
