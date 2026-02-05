"""Configuration settings for the Instagram Watermark Remover app."""

import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file (if it exists)
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).parent
CREDENTIALS_DIR = BASE_DIR / "credentials"
DOWNLOADS_DIR = BASE_DIR / "downloads"
PROCESSED_DIR = BASE_DIR / "processed"
TEMP_DIR = BASE_DIR / "temp"

# Create directories if they don't exist
for dir_path in [CREDENTIALS_DIR, DOWNLOADS_DIR, PROCESSED_DIR, TEMP_DIR]:
    dir_path.mkdir(exist_ok=True)

# Google API settings - NO defaults, must be configured by user
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
CREDENTIALS_FILE = CREDENTIALS_DIR / "client_secret.json"
TOKEN_FILE = CREDENTIALS_DIR / "token.pickle"

# Google Photos API scopes
SCOPES = [
    "https://www.googleapis.com/auth/photoslibrary.readonly",
]

# Flask settings
# Auto-generate a random secret key if not provided (safe for dev, but sessions won't persist across restarts)
# For production, set FLASK_SECRET_KEY in your .env file
_env_secret = os.getenv("FLASK_SECRET_KEY")
if _env_secret:
    FLASK_SECRET_KEY = _env_secret
else:
    # Generate a random key at runtime - completely safe, no secrets in code
    FLASK_SECRET_KEY = secrets.token_hex(32)

FLASK_DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"

# Processing settings
USE_GPU = os.getenv("USE_GPU", "true").lower() == "true"
WATERMARK_POSITION = os.getenv("WATERMARK_POSITION", "auto")

# Watermark detection settings
# Instagram watermarks are typically in bottom corners
WATERMARK_REGIONS = {
    "bottom_right": {"x_start": 0.7, "y_start": 0.85, "x_end": 1.0, "y_end": 1.0},
    "bottom_left": {"x_start": 0.0, "y_start": 0.85, "x_end": 0.3, "y_end": 1.0},
    "top_right": {"x_start": 0.7, "y_start": 0.0, "x_end": 1.0, "y_end": 0.15},
    "top_left": {"x_start": 0.0, "y_start": 0.0, "x_end": 0.3, "y_end": 0.15},
}

# Image processing settings
MAX_IMAGE_SIZE = 4096  # Max dimension for processing
SUPPORTED_FORMATS = [".jpg", ".jpeg", ".png", ".webp"]

