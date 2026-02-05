"""Configuration for FBReader Web Reader."""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Server settings
HOST = "0.0.0.0"
PORT = 5555
DEBUG = True

# Authentication
# Password for accessing the web reader (change this!)
ACCESS_PASSWORD = os.environ.get("FBREADER_PASSWORD")

# Session settings
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")
SESSION_TIMEOUT_HOURS = 24 * 7  # 1 week

# FBReader paths (Windows UWP app)
FBREADER_BASE = Path(os.environ.get(
    "FBREADER_PATH",
    r"C:\Users\LRNA\AppData\Local\Packages\FBReader_n0j83cvmz1mee"
))
FBREADER_DATA = FBREADER_BASE / "LocalCache" / "Roaming" / "FBReader.ORG Limited" / "FBReader"
FBREADER_COOKIES = FBREADER_DATA / "cookies.txt"
FBREADER_DB = FBREADER_DATA / "books.sqlite"

# FBReader Book Network URLs
FBREADER_OPDS_URL = "https://books.fbreader.org/opds"
FBREADER_WEB_URL = "https://books.fbreader.org"

# Local cache for downloaded books
CACHE_DIR = BASE_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# Allowed IPs (empty means all IPs allowed after password auth)
ALLOWED_IPS = []  # e.g., ["192.168.1.100", "10.0.0.5"]
