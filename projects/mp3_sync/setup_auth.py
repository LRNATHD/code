
import os
import sys

OAUTH_DIR = os.path.join(os.environ.get('APPDATA', ''), 'MP3SyncOAuth')
OAUTH_FILE = os.path.join(OAUTH_DIR, 'oauth.json')
BROWSER_FILE = os.path.join(OAUTH_DIR, 'browser.json')

def setup_browser_auth():
    """Setup authentication using browser request headers (simpler, but expires)."""
    from ytmusicapi import setup as ytmusic_setup
    
    print("\n=== Browser Header Authentication ===")
    print("1. Open YouTube Music (music.youtube.com) in Firefox and log in.")
    print("2. Open Developer Tools (F12) -> Network tab.")
    print("3. Click on any item / scroll to trigger requests.")
    print("4. Find a POST request to music.youtube.com (e.g. 'browse').")
    print("5. Right-click the request -> Copy -> Copy Request Headers.")
    print("6. Paste below, then press Enter on an empty line, then Ctrl+Z and Enter.")
    print()

    os.makedirs(OAUTH_DIR, exist_ok=True)
    
    # Use ytmusicapi's setup to parse the headers
    ytmusic_setup(filepath=BROWSER_FILE)
    
    if os.path.exists(BROWSER_FILE):
        print(f"\nSuccess! Browser auth saved to: {BROWSER_FILE}")
        print("Note: These credentials typically last ~2 years unless you log out.")
        # Remove old oauth.json if switching methods
        if os.path.exists(OAUTH_FILE):
            os.remove(OAUTH_FILE)
            print("(Removed old oauth.json)")
    else:
        print("Error: browser.json was not created. Please try again.")


def setup_oauth():
    """Setup OAuth authentication (more reliable, auto-refreshes)."""
    from ytmusicapi import setup_oauth as ytmusic_setup_oauth
    
    print("\n=== OAuth Authentication ===")
    print("This requires a Google Cloud project with YouTube Data API enabled.")
    print("1. Go to https://console.cloud.google.com/")
    print("2. Create a project (or use existing).")
    print("3. Enable 'YouTube Data API v3'.")
    print("4. Go to Credentials -> Create Credentials -> OAuth client ID.")
    print("5. Application type: 'TVs and Limited Input devices'.")
    print("6. Copy the Client ID and Client Secret.")
    print()
    
    client_id = input("Client ID: ").strip()
    client_secret = input("Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("Error: Both Client ID and Client Secret are required.")
        return
    
    os.makedirs(OAUTH_DIR, exist_ok=True)
    
    ytmusic_setup_oauth(
        filepath=OAUTH_FILE,
        client_id=client_id,
        client_secret=client_secret,
        open_browser=True
    )
    
    if os.path.exists(OAUTH_FILE):
        print(f"\nSuccess! OAuth tokens saved to: {OAUTH_FILE}")
        # Remove old browser.json if switching methods
        if os.path.exists(BROWSER_FILE):
            os.remove(BROWSER_FILE)
            print("(Removed old browser.json)")
    else:
        print("Error: OAuth setup failed.")


def main():
    print("MP3 Sync - YouTube Music Authentication Setup")
    print("=" * 50)
    
    # Show current status
    has_browser = os.path.exists(BROWSER_FILE)
    has_oauth = os.path.exists(OAUTH_FILE)
    if has_browser:
        print(f"  Current auth: Browser headers ({BROWSER_FILE})")
    elif has_oauth:
        print(f"  Current auth: OAuth ({OAUTH_FILE})")
    else:
        print("  Current auth: NONE (not authenticated)")
    
    print()
    print("Choose authentication method:")
    print("  [1] Browser Headers  (quick - copy/paste from dev tools)")
    print("  [2] OAuth            (robust - requires Google Cloud project)")
    print()
    
    choice = input("Enter 1 or 2: ").strip()
    
    if choice == '1':
        setup_browser_auth()
    elif choice == '2':
        setup_oauth()
    else:
        print("Invalid choice.")
        return
    
    # Quick test
    print("\nTesting authentication...")
    try:
        from ytmusicapi import YTMusic
        if os.path.exists(BROWSER_FILE):
            yt = YTMusic(BROWSER_FILE)
        elif os.path.exists(OAUTH_FILE):
            yt = YTMusic(OAUTH_FILE)
        else:
            print("No auth file found!")
            return
        
        playlists = yt.get_library_playlists(limit=3)
        print(f"  OK! Found {len(playlists)} playlists.")
        for p in playlists[:3]:
            print(f"    - {p.get('title', '?')}")
        print("\nAuthentication is working!")
    except Exception as e:
        print(f"  Test failed: {e}")
        print("  You may need to re-run setup.")


if __name__ == "__main__":
    main()
