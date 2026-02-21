"""
Service Manager Dashboard
Web UI for managing startup services.
"""

import os
import json
from functools import wraps
from flask import Flask, render_template, jsonify, request
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
                'pid': s.pid,
                'description': s.description
            }
            for s in statuses
        ],
        'tasks': manager.get_all_tasks()
    })


LAYOUT_FILE = os.path.join(os.path.dirname(__file__), 'layout.json')

@app.route('/api/layout', methods=['GET'])
def api_get_layout():
    """Get saved card layout positions."""
    try:
        with open(LAYOUT_FILE, 'r') as f:
            return jsonify(json.load(f))
    except:
        return jsonify({})

@app.route('/api/layout', methods=['POST'])
@require_password
def api_save_layout():
    """Save card layout positions (password required)."""
    import json as json_mod
    data = request.get_json()
    with open(LAYOUT_FILE, 'w') as f:
        json_mod.dump(data, f)
    return jsonify({'success': True})


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


# ── Generic Config Proxy (reusable by any service) ──────
# Services with "has_config": true in services.json and
# GET/POST /api/config endpoints are automatically supported.

@app.route('/api/services/meta')
def api_services_meta():
    """Return metadata about services (which ones have config, etc).
    Dashboard uses this to decide which buttons to show."""
    config = manager.load_config()
    meta = {}
    for svc in config.get('services', []):
        meta[svc['id']] = {
            'has_config': svc.get('has_config', False),
            'path': svc.get('path', ''),
            'internal_port': svc.get('internal_port', svc.get('port')),
        }
    return jsonify(meta)


@app.route('/api/service/<service_id>/config', methods=['GET'])
def api_get_service_config(service_id):
    """Proxy: fetch config from a running service."""
    success, result = manager.get_service_config(service_id)
    if success:
        return jsonify(result)
    return jsonify({'success': False, 'message': result}), 400


@app.route('/api/service/<service_id>/config', methods=['POST'])
@require_password
def api_set_service_config(service_id):
    """Proxy: update config on a running service."""
    data = request.get_json()
    password = request.headers.get('X-Password', '')
    success, result = manager.set_service_config(service_id, data, password)
    if success:
        return jsonify(result)
    return jsonify({'success': False, 'message': result}), 400


# ── Generic Action Proxy (reusable by any service) ──────
# Forward arbitrary API calls to a running service.
# Dashboard uses this for service-specific actions (e.g., sync triggers).

@app.route('/api/service/<service_id>/proxy/<path:subpath>', methods=['GET', 'POST'])
def api_service_proxy(service_id, subpath):
    """Proxy any API call to a running service's internal port."""
    import requests as req
    service = manager.get_service_by_id(service_id)
    if not service:
        return jsonify({'success': False, 'message': f"Service '{service_id}' not found"}), 404

    port = service.get('internal_port', service.get('port'))
    target_url = f"http://127.0.0.1:{port}/{subpath}"

    try:
        headers = {}
        pw = request.headers.get('X-Password', '')
        if pw:
            headers['X-Password'] = pw

        if request.method == 'POST':
            if request.is_json:
                headers['Content-Type'] = 'application/json'
                resp = req.post(target_url, json=request.get_json(), headers=headers, timeout=10)
            else:
                resp = req.post(target_url, headers=headers, timeout=10)
        else:
            resp = req.get(target_url, headers=headers, timeout=10)

        return jsonify(resp.json())
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 502


# ── Log / Console API ────────────────────────────────
# Simple in-memory log store for the "Console" block.

LOG_FILE = os.path.join(os.path.dirname(__file__), 'service_manager.log')
LOG_HISTORY = []
MAX_LOGS = 1000

# Load logs on startup
if os.path.exists(LOG_FILE):
    try:
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()
            # Tailwind load last MAX_LOGS
            count = len(lines)
            start = count - MAX_LOGS if count > MAX_LOGS else 0
            for line in lines[start:]:
                try:
                    LOG_HISTORY.append(json.loads(line))
                except: pass
    except: pass

@app.route('/api/log', methods=['POST'])
@require_password
def api_post_log():
    """Accept a log message from any local script."""
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'success': False, 'message': 'Missing message'}), 400
    
    import time
    entry = {
        'timestamp': time.time(),
        'source': data.get('source', 'unknown'),
        'message': data['message']
    }
    
    LOG_HISTORY.append(entry)
    if len(LOG_HISTORY) > MAX_LOGS:
        LOG_HISTORY.pop(0)

    # Persist to file
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    except: pass
        
    return jsonify({'success': True})

@app.route('/api/logs', methods=['DELETE'])
@require_password
def api_clear_logs():
    """Clear all logs."""
    global LOG_HISTORY
    LOG_HISTORY = []
    # Clear file too
    try:
        open(LOG_FILE, 'w').close()
    except: pass
    return jsonify({'success': True})

@app.route('/api/mp3_sync/auth', methods=['POST'])
@require_password
def api_mp3_sync_auth():
    """Update auth headers for MP3 Sync task."""
    data = request.get_json()
    headers_raw = data.get('headers', '')
    if not headers_raw:
        return jsonify({'success': False, 'message': 'No headers provided'}), 400

    try:
        import ytmusicapi
        # Path to auth file
        app_data = os.environ.get('APPDATA', '')
        oauth_dir = os.path.join(app_data, 'MP3SyncOAuth')
        if not os.path.exists(oauth_dir):
            os.makedirs(oauth_dir)
        browser_file = os.path.join(oauth_dir, 'browser.json')
        
        # simple check to see if it looks like headers or json
        # ytmusicapi.setup handles raw headers string by converting to json
        ytmusicapi.setup(filepath=browser_file, headers_raw=headers_raw)
        
        return jsonify({'success': True, 'message': 'Auth headers saved'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f"Auth error: {str(e)}"}), 500



@app.route('/api/logs', methods=['GET'])
def api_get_logs():
    """Get logs, optionally filtered by timestamp."""
    after = request.args.get('after', type=float, default=0)
    # Return only logs newer than 'after'
    new_logs = [l for l in LOG_HISTORY if l['timestamp'] > after]
    return jsonify({'logs': new_logs})


if __name__ == '__main__':
    print(f"Service Manager Dashboard running on http://localhost:{PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
