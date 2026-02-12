import requests
import os

# Create a test script to hit the auth endpoint
password = os.environ.get("STARTUP_APPS_PASSWORD")
if not password:
    print("STARTUP_APPS_PASSWORD not found")
    exit(1)

url = "http://localhost:9870/api/mp3_sync/auth"

# Minimal valid-looking headers for ytmusicapi
fake_headers = """
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Cookie: SID=123; HSID=456;
"""

try:
    resp = requests.post(url, json={"headers": fake_headers}, headers={"X-Password": password})
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as e:
    print(f"Error: {e}")
