import requests
import json
import os
import time

API_URL = "http://localhost:9870/api/log"
PASSWORD = os.environ.get("STARTUP_APPS_PASSWORD", "")

def log(msg, source="test"):
    headers = {"X-Password": PASSWORD, "Content-Type": "application/json"}
    data = {"source": source, "message": msg}
    try:
        resp = requests.post(API_URL, json=data, headers=headers)
        print(f"Sent: {msg} -> {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    for i in range(5):
        log(f"Test message {i}", "tester")
        time.sleep(0.5)
