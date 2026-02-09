"""
Parts Inventory Server with Authentication.
Flask-based server with STARTUP_APPS_PASSWORD authentication.
"""

import os
import json
import functools
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, redirect, url_for, session, send_from_directory, render_template_string

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "parts-inventory-secret-key")

PORT = int(os.environ.get("SERVICE_PORT", 9873))
DB_FILE = os.path.join(os.path.dirname(__file__), 'db.json')

# Store authenticated IPs with their expiry times
authenticated_ips: dict[str, datetime] = {}

# Password from environment
def get_password():
    pwd = os.environ.get('STARTUP_APPS_PASSWORD')
    if pwd:
        return pwd
    # Try Windows registry as fallback
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment")
        pwd, _ = winreg.QueryValueEx(key, "STARTUP_APPS_PASSWORD")
        winreg.CloseKey(key)
        return pwd
    except:
        return None


def get_client_ip() -> str:
    """Get the client's IP address."""
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
            del authenticated_ips[client_ip]
    
    return False


def require_auth(f):
    """Decorator to require authentication."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not is_authenticated():
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({"error": "Not authenticated"}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Parts Inventory - Login</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #000; color: #fff;
            min-height: 100vh; display: flex; align-items: center; justify-content: center;
        }
        .login-box {
            background: #111; border: 1px solid #333; border-radius: 12px;
            padding: 2rem; width: 100%; max-width: 360px;
        }
        h1 { font-size: 1.5rem; margin-bottom: 1.5rem; text-align: center; }
        .error { background: #3a1515; color: #ff6b6b; padding: 0.75rem; border-radius: 6px; margin-bottom: 1rem; text-align: center; }
        label { display: block; font-size: 0.875rem; color: #888; margin-bottom: 0.5rem; }
        input[type="password"] {
            width: 100%; padding: 0.75rem; background: #222; border: 1px solid #444;
            border-radius: 6px; color: #fff; font-size: 1rem; margin-bottom: 1rem;
        }
        input[type="password"]:focus { outline: none; border-color: #0af; }
        .remember { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1.5rem; cursor: pointer; }
        .remember input { width: 18px; height: 18px; }
        button {
            width: 100%; padding: 0.75rem; background: #0af; border: none;
            border-radius: 6px; color: #000; font-size: 1rem; font-weight: 600; cursor: pointer;
        }
        button:hover { background: #0cf; }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>🔧 Parts Inventory</h1>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="post">
            <label for="password">Password</label>
            <input type="password" id="password" name="password" required autofocus>
            <label class="remember">
                <input type="checkbox" name="remember" value="1">
                Remember this device
            </label>
            <button type="submit">Log In</button>
        </form>
    </div>
</body>
</html>
"""


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with password authentication."""
    error = None
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        expected = get_password()
        
        if not expected:
            error = "Password not configured on server"
        elif password == expected:
            client_ip = get_client_ip()
            session['authenticated'] = True
            session.permanent = bool(remember)
            hours = 24 * 30 if remember else 1
            authenticated_ips[client_ip] = datetime.now() + timedelta(hours=hours)
            return redirect(url_for('index'))
        else:
            error = "Invalid password"
    
    return render_template_string(LOGIN_HTML, error=error)


@app.route('/logout')
def logout():
    """Log out and clear authentication."""
    session.clear()
    client_ip = get_client_ip()
    if client_ip in authenticated_ips:
        del authenticated_ips[client_ip]
    return redirect(url_for('login'))


@app.route('/')
@require_auth
def index():
    """Serve main page."""
    return send_from_directory('.', 'index.html')


@app.route('/api/inventory', methods=['GET'])
@require_auth
def get_inventory():
    """Get inventory data."""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            try:
                data = f.read()
                if not data:
                    data = "[]"
            except:
                data = "[]"
        return data, 200, {'Content-Type': 'application/json'}
    return '[]', 200, {'Content-Type': 'application/json'}


@app.route('/api/inventory', methods=['POST'])
@require_auth
def save_inventory():
    """Save inventory data."""
    try:
        json_data = request.get_json()
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/status')
def api_status():
    """Health check endpoint (public)."""
    return jsonify({
        "status": "ok",
        "authenticated": is_authenticated(),
        "timestamp": datetime.now().isoformat()
    })


@app.route('/<path:filename>')
@require_auth
def serve_static(filename):
    """Serve static files (CSS, JS)."""
    return send_from_directory('.', filename)


if __name__ == '__main__':
    print(f"Starting Parts Inventory Server on http://localhost:{PORT}")
    print(f"Data file: {DB_FILE}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
