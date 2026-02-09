"""Google Tasks Custom App - Flask Application."""
import os
import uuid
import functools
from datetime import datetime, timedelta

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    session,
    abort,
)
from flask_cors import CORS

import config
from tasks_client import (
    get_tasks_client, 
    get_rules_manager, 
    TaskRule,
    extract_and_increment_value
)

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
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr or "unknown"


def is_authenticated() -> bool:
    """Check if current request is authenticated."""
    client_ip = get_client_ip()
    
    if session.get('authenticated'):
        return True
    
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
            if request.is_json:
                return jsonify({"error": "Not authenticated"}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


@app.route('/')
def index():
    """Redirect to dashboard or login."""
    if is_authenticated():
        return redirect(url_for('dashboard'))
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
            
            session['authenticated'] = True
            session.permanent = bool(remember)
            
            hours = config.SESSION_TIMEOUT_HOURS if remember else 1
            authenticated_ips[client_ip] = datetime.now() + timedelta(hours=hours)
            
            return redirect(url_for('dashboard'))
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


@app.route('/dashboard')
@require_auth
def dashboard():
    """Main dashboard view."""
    try:
        client = get_tasks_client()
        task_lists = client.get_task_lists()
        rules_manager = get_rules_manager()
        rules = rules_manager.get_all_rules()
        
        return render_template('dashboard.html', 
                             task_lists=task_lists, 
                             rules=[r.to_dict() for r in rules])
    except FileNotFoundError as e:
        return render_template('setup.html', error=str(e))
    except Exception as e:
        return render_template('error.html', error=str(e))


@app.route('/setup')
@require_auth
def setup():
    """Setup page for Google OAuth."""
    return render_template('setup.html')


# ============ API Endpoints ============

@app.route('/api/task-lists')
@require_auth
def api_task_lists():
    """Get all task lists."""
    try:
        client = get_tasks_client()
        lists = client.get_task_lists()
        return jsonify({"task_lists": lists})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/tasks/<task_list_id>')
@require_auth
def api_tasks(task_list_id: str):
    """Get all tasks from a task list."""
    try:
        client = get_tasks_client()
        show_completed = request.args.get('completed', 'false').lower() == 'true'
        tasks = client.get_tasks(task_list_id, show_completed=show_completed)
        return jsonify({"tasks": tasks})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/task/<task_list_id>/<task_id>')
@require_auth
def api_task(task_list_id: str, task_id: str):
    """Get a specific task."""
    try:
        client = get_tasks_client()
        task = client.get_task(task_list_id, task_id)
        if task:
            return jsonify({"task": task})
        return jsonify({"error": "Task not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/task/<task_list_id>/<task_id>', methods=['PATCH'])
@require_auth
def api_update_task(task_list_id: str, task_id: str):
    """Update a task."""
    try:
        client = get_tasks_client()
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        task = client.update_task(task_list_id, task_id, data)
        if task:
            return jsonify({"task": task})
        return jsonify({"error": "Failed to update task"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/task/<task_list_id>', methods=['POST'])
@require_auth
def api_create_task(task_list_id: str):
    """Create a new task."""
    try:
        client = get_tasks_client()
        data = request.get_json()
        if not data or 'title' not in data:
            return jsonify({"error": "Title is required"}), 400
        
        due = None
        if 'due' in data:
            due = datetime.fromisoformat(data['due'].replace('Z', '+00:00'))
        
        task = client.create_task(
            task_list_id, 
            data['title'], 
            due=due,
            notes=data.get('notes')
        )
        if task:
            return jsonify({"task": task}), 201
        return jsonify({"error": "Failed to create task"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/task/<task_list_id>/<task_id>', methods=['DELETE'])
@require_auth
def api_delete_task(task_list_id: str, task_id: str):
    """Delete a task."""
    try:
        client = get_tasks_client()
        if client.delete_task(task_list_id, task_id):
            return jsonify({"success": True})
        return jsonify({"error": "Failed to delete task"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============ Rules API ============

@app.route('/api/rules')
@require_auth
def api_rules():
    """Get all rules."""
    rules_manager = get_rules_manager()
    rules = rules_manager.get_all_rules()
    return jsonify({"rules": [r.to_dict() for r in rules]})


@app.route('/api/rules', methods=['POST'])
@require_auth
def api_create_rule():
    """Create a new rule."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    required_fields = ['name', 'task_pattern', 'task_list_id', 'increment_type', 'increment_value']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    rule = TaskRule(
        rule_id=str(uuid.uuid4()),
        name=data['name'],
        task_pattern=data['task_pattern'],
        task_list_id=data['task_list_id'],
        increment_type=data['increment_type'],
        increment_value=float(data['increment_value']),
        enabled=data.get('enabled', True)
    )
    
    rules_manager = get_rules_manager()
    rules_manager.add_rule(rule)
    
    return jsonify({"rule": rule.to_dict()}), 201


@app.route('/api/rules/<rule_id>', methods=['PATCH'])
@require_auth
def api_update_rule(rule_id: str):
    """Update a rule."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    rules_manager = get_rules_manager()
    if rules_manager.update_rule(rule_id, data):
        rule = rules_manager.get_rule(rule_id)
        return jsonify({"rule": rule.to_dict()})
    return jsonify({"error": "Rule not found"}), 404


@app.route('/api/rules/<rule_id>', methods=['DELETE'])
@require_auth
def api_delete_rule(rule_id: str):
    """Delete a rule."""
    rules_manager = get_rules_manager()
    if rules_manager.delete_rule(rule_id):
        return jsonify({"success": True})
    return jsonify({"error": "Rule not found"}), 404


@app.route('/api/rules/<rule_id>/test', methods=['POST'])
@require_auth
def api_test_rule(rule_id: str):
    """Test a rule against a sample task title."""
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({"error": "Title is required for testing"}), 400
    
    rules_manager = get_rules_manager()
    rule = rules_manager.get_rule(rule_id)
    if not rule:
        return jsonify({"error": "Rule not found"}), 404
    
    new_title = extract_and_increment_value(
        data['title'],
        rule.task_pattern,
        rule.increment_type,
        rule.increment_value
    )
    
    return jsonify({
        "original": data['title'],
        "result": new_title,
        "matched": new_title is not None
    })


@app.route('/api/apply-rule', methods=['POST'])
@require_auth
def api_apply_rule():
    """Apply a rule to a specific task (update its title with incremented value)."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    required_fields = ['task_list_id', 'task_id', 'rule_id']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    rules_manager = get_rules_manager()
    rule = rules_manager.get_rule(data['rule_id'])
    if not rule:
        return jsonify({"error": "Rule not found"}), 404
    
    client = get_tasks_client()
    task = client.get_task(data['task_list_id'], data['task_id'])
    if not task:
        return jsonify({"error": "Task not found"}), 404
    
    new_title = extract_and_increment_value(
        task['title'],
        rule.task_pattern,
        rule.increment_type,
        rule.increment_value
    )
    
    if not new_title:
        return jsonify({"error": "Rule did not match task title"}), 400
    
    updated_task = client.update_task(
        data['task_list_id'],
        data['task_id'],
        {"title": new_title}
    )
    
    if updated_task:
        return jsonify({
            "success": True,
            "old_title": task['title'],
            "new_title": new_title,
            "task": updated_task
        })
    
    return jsonify({"error": "Failed to update task"}), 500



@app.route('/api/check-recurring', methods=['POST'])
@require_auth
def api_check_recurring():
    """Manually trigger detailed recurring task check."""
    try:
        client = get_tasks_client()
        rules_manager = get_rules_manager()
        messages = client.check_daily_progressions(rules_manager)
        return jsonify({"success": True, "messages": messages})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Background thread for periodic checks (Automation Loop)
def automation_loop():
    import time
    
    # Initial wait to let server start
    time.sleep(10)
    
    while True:
        try:
            with app.app_context():
                print(f"[{datetime.now().strftime('%H:%M')}] Running periodic automation check...")
                client = get_tasks_client()
                rules_manager = get_rules_manager()
                
                # Check for completed tasks and create next day's versions
                messages = client.check_daily_progressions(rules_manager)
                
                for msg in messages:
                    print(f"[Auto-Task] {msg}")
                    
        except Exception as e:
            print(f"[Auto-Task Error] {e}")
            
        # Wait 1 hour before next check
        # This acts as the "polling" mechanism to detect changes made on your phone
        time.sleep(3600)

from threading import Thread
automation_thread = Thread(target=automation_loop)
automation_thread.daemon = True
automation_thread.start()


@app.route('/api/status')
def api_status():
    """Get API status (public endpoint for health checks)."""
    return jsonify({
        "status": "ok",
        "authenticated": is_authenticated(),
        "timestamp": datetime.now().isoformat()
    })


if __name__ == '__main__':
    print(f"Starting Google Tasks Custom App on http://{config.HOST}:{config.PORT}")
    app.run(host=config.HOST, port=config.PORT, debug=False)
