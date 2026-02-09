"""Configuration for Google Tasks Custom App."""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Server settings
HOST = "0.0.0.0"
PORT = int(os.environ.get("SERVICE_PORT", 9872))
DEBUG = False

# Authentication - Shared password for all startup apps
ACCESS_PASSWORD = os.environ.get("STARTUP_APPS_PASSWORD")

# Session settings
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")
SESSION_TIMEOUT_HOURS = 24 * 30  # 1 month

# Google Tasks API settings - credentials stored in APPDATA (outside repo)
GOOGLE_OAUTH_DIR = Path(os.environ.get("APPDATA", "")) / "GoogleTasksOAuth"
GOOGLE_OAUTH_DIR.mkdir(parents=True, exist_ok=True)
GOOGLE_CREDENTIALS_FILE = GOOGLE_OAUTH_DIR / "credentials.json"
GOOGLE_TOKEN_FILE = GOOGLE_OAUTH_DIR / "token.json"
SCOPES = ["https://www.googleapis.com/auth/tasks"]

# Data storage
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Rules file for custom task automations
RULES_FILE = DATA_DIR / "rules.json"

# Allowed IPs (empty means all IPs allowed after password auth)
ALLOWED_IPS = []  # e.g., ["192.168.1.100", "10.0.0.5"]
