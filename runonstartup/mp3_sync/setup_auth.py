import os
import sys

try:
    from ytmusicapi import YTMusic
except ImportError:
    print("Error: ytmusicapi not installed.")
    sys.exit(1)

# Paths
APP_DATA = os.environ.get('APPDATA', '')
OAUTH_DIR = os.path.join(APP_DATA, 'MP3SyncOAuth')
BROWSER_FILE = os.path.join(OAUTH_DIR, 'browser.json')
OAUTH_FILE = os.path.join(OAUTH_DIR, 'oauth.json')

if not os.path.exists(OAUTH_DIR):
    os.makedirs(OAUTH_DIR)

print("\n=== YouTube Music Auth Setup ===")
print("Your current authentication seems to be invalid or expired.")
print("We recommend using OAuth as it is more stable and does not expire as quickly.")
print("\nOptions:")
print("1. Setup OAuth (Recommended) - Login with Google account")
print("2. Setup Browser Headers - Copy headers from browser network tab")
print("3. Delete existing auth files (Reset)")

choice = input("\nEnter choice (1/2/3): ").strip()

if choice == '1':
    print(f"\nSetting up OAuth in: {OAUTH_FILE}")
    print("Please follow the instructions to authenticate via Google.")
    # Renaming existing browser.json if it exists to avoid conflicts since sync prioritizes it
    if os.path.exists(BROWSER_FILE):
        backup = BROWSER_FILE + ".bak"
        try:
            os.rename(BROWSER_FILE, backup)
            print(f"Renamed existing browser.json to {os.path.basename(backup)} to prioritize OAuth.")
        except Exception as e:
            print(f"Warning: Could not rename browser.json: {e}")

    try:
        # Use setup_oauth for modern ytmusicapi
        if hasattr(YTMusic, 'setup_oauth'):
            YTMusic.setup_oauth(filepath=OAUTH_FILE)
        else:
            # Fallback for older versions if any
            print("Using legacy setup...")
            YTMusic.setup(filepath=OAUTH_FILE)
        print(f"\nSuccess! OAuth credentials saved to {OAUTH_FILE}")
    except Exception as e:
        print(f"\nError setting up OAuth: {e}")

elif choice == '2':
    print(f"\nSetting up Browser Headers in: {BROWSER_FILE}")
    print("Instructions: Open YouTube Music in browser, open DevTools (F12), go to Network tab,")
    print("play a song, look for a request (e.g. 'browse' or 'next'), copy the request headers.")
    print("Paste the headers below and press Enter, then Ctrl+Z (Windows) or Ctrl+D (Linux/Mac) and Enter to save.")
    try:
        YTMusic.setup(filepath=BROWSER_FILE)
        print(f"\nSuccess! Browser headers saved to {BROWSER_FILE}")
    except Exception as e:
        print(f"\nError setting up headers: {e}")

elif choice == '3':
    confirm = input("Are you sure you want to delete all auth files? (y/n): ")
    if confirm.lower() == 'y':
        if os.path.exists(BROWSER_FILE):
            os.remove(BROWSER_FILE)
            print(f"Deleted {BROWSER_FILE}")
        if os.path.exists(OAUTH_FILE):
            os.remove(OAUTH_FILE)
            print(f"Deleted {OAUTH_FILE}")
        print("Auth files reset.")

else:
    print("Invalid choice.")

input("\nPress Enter to exit...")
