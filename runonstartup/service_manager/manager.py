"""
Service Manager - Process management for startup services.
Reads services.json, manages processes, checks health.
"""

import json
import os
import subprocess
import time
import requests
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

BASE_DIR = Path(__file__).parent
SERVICES_FILE = BASE_DIR / "services.json"

# Track running processes by service ID
_processes: dict[str, subprocess.Popen] = {}


@dataclass
class ServiceStatus:
    id: str
    name: str
    running: bool
    healthy: bool
    port: int
    pid: Optional[int] = None
    error: Optional[str] = None
    description: Optional[str] = None


def load_config() -> dict:
    """Load services.json config."""
    with open(SERVICES_FILE, 'r') as f:
        return json.load(f)


def get_service_by_id(service_id: str) -> Optional[dict]:
    """Get a service definition by ID."""
    config = load_config()
    for svc in config.get('services', []):
        if svc['id'] == service_id:
            return svc
    return None


def get_task_by_id(task_id: str) -> Optional[dict]:
    """Get a task definition by ID."""
    config = load_config()
    for task in config.get('tasks', []):
        if task['id'] == task_id:
            return task
    return None


def check_port_in_use(port: int) -> bool:
    """Check if a port is in use."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0


def check_health(service: dict) -> bool:
    """Check if a service is responding to health checks."""
    port = service.get('internal_port', service.get('port'))
    health_url = service.get('health_url', '/')
    try:
        resp = requests.get(f"http://127.0.0.1:{port}{health_url}", timeout=2)
        return resp.status_code < 500
    except:
        return False


def start_service(service_id: str) -> tuple[bool, str]:
    """Start a service by ID. Returns (success, message)."""
    service = get_service_by_id(service_id)
    if not service:
        return False, f"Service '{service_id}' not found"
    
    port = service.get('internal_port', service.get('port'))
    
    # Check if already running
    if check_port_in_use(port):
        return False, f"Port {port} already in use"
    
    # Resolve directory
    service_dir = (BASE_DIR / service['dir']).resolve()
    if not service_dir.exists():
        return False, f"Directory not found: {service_dir}"
    
    # Set up environment with password
    env = os.environ.copy()
    # Try to get password from user env
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment")
        password, _ = winreg.QueryValueEx(key, "STARTUP_APPS_PASSWORD")
        env["STARTUP_APPS_PASSWORD"] = password
        winreg.CloseKey(key)
    except:
        pass  # May already be in environment
    
    # Also set the port in env so apps can use it
    env["SERVICE_PORT"] = str(port)
    
    try:
        proc = subprocess.Popen(
            service['start_cmd'],
            shell=True,
            cwd=str(service_dir),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        _processes[service_id] = proc
        time.sleep(1)  # Give it a moment to start
        
        if proc.poll() is not None:
            return False, f"Process exited immediately with code {proc.returncode}"
        
        return True, f"Started {service['name']} on port {port}"
    except Exception as e:
        return False, f"Failed to start: {e}"


def stop_service(service_id: str) -> tuple[bool, str]:
    """Stop a service by ID."""
    service = get_service_by_id(service_id)
    if not service:
        return False, f"Service '{service_id}' not found"
    
    port = service.get('internal_port', service.get('port'))
    
    # Try tracked process first
    if service_id in _processes:
        proc = _processes[service_id]
        try:
            proc.terminate()
            proc.wait(timeout=5)
            del _processes[service_id]
            return True, f"Stopped {service['name']}"
        except:
            proc.kill()
            del _processes[service_id]
            return True, f"Killed {service['name']}"
    
    # Fallback: find by port
    if check_port_in_use(port):
        # Use netstat to find PID
        try:
            result = subprocess.run(
                f'netstat -ano | findstr :{port}',
                shell=True, capture_output=True, text=True
            )
            for line in result.stdout.strip().split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    pid = line.strip().split()[-1]
                    subprocess.run(f'taskkill /F /PID {pid}', shell=True)
                    return True, f"Killed process {pid} on port {port}"
        except:
            pass
        return False, f"Could not stop process on port {port}"
    
    return True, f"{service['name']} was not running"


def restart_service(service_id: str) -> tuple[bool, str]:
    """Restart a service."""
    stop_service(service_id)
    time.sleep(1)
    return start_service(service_id)


def run_task(task_id: str) -> tuple[bool, str]:
    """Run a one-off task."""
    task = get_task_by_id(task_id)
    if not task:
        return False, f"Task '{task_id}' not found"
    
    try:
        result = subprocess.run(
            task['cmd'],
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            return True, result.stdout or "Task completed"
        else:
            return False, result.stderr or f"Task failed with code {result.returncode}"
    except subprocess.TimeoutExpired:
        return False, "Task timed out after 60 seconds"
    except Exception as e:
        return False, f"Task error: {e}"


def get_all_status() -> list[ServiceStatus]:
    """Get status of all services."""
    config = load_config()
    statuses = []
    
    for svc in config.get('services', []):
        port = svc.get('internal_port', svc.get('port'))
        running = check_port_in_use(port)
        healthy = check_health(svc) if running else False
        pid = None
        
        if svc['id'] in _processes:
            proc = _processes[svc['id']]
            if proc.poll() is None:
                pid = proc.pid
        
        statuses.append(ServiceStatus(
            id=svc['id'],
            name=svc['name'],
            running=running,
            healthy=healthy,
            port=port,
            pid=pid,
            description=svc.get('description', '')
        ))
    
    return statuses


def get_all_tasks() -> list[dict]:
    """Get all tasks from config."""
    config = load_config()
    return config.get('tasks', [])


# ── Generic Config Proxy ─────────────────────────────────
# Any service with "has_config": true in services.json and
# GET/POST /api/config endpoints gets config management for free.

def get_service_config(service_id: str) -> tuple[bool, dict | str]:
    """Fetch config from a running service's /api/config endpoint."""
    service = get_service_by_id(service_id)
    if not service:
        return False, f"Service '{service_id}' not found"
    if not service.get('has_config'):
        return False, f"Service '{service_id}' has no config endpoint"

    port = service.get('internal_port', service.get('port'))
    try:
        resp = requests.get(f"http://127.0.0.1:{port}/api/config", timeout=5)
        return True, resp.json()
    except Exception as e:
        return False, f"Config fetch failed: {e}"


def set_service_config(service_id: str, data: dict, password: str = "") -> tuple[bool, dict | str]:
    """Post config update to a running service's /api/config endpoint."""
    service = get_service_by_id(service_id)
    if not service:
        return False, f"Service '{service_id}' not found"
    if not service.get('has_config'):
        return False, f"Service '{service_id}' has no config endpoint"

    port = service.get('internal_port', service.get('port'))
    try:
        resp = requests.post(
            f"http://127.0.0.1:{port}/api/config",
            json=data,
            headers={'X-Password': password},
            timeout=5
        )
        return True, resp.json()
    except Exception as e:
        return False, f"Config update failed: {e}"


def get_services_with_config() -> list[str]:
    """Return list of service IDs that have config endpoints."""
    config = load_config()
    return [s['id'] for s in config.get('services', []) if s.get('has_config')]

