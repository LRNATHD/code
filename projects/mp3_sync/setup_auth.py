
import os
import json
import time

def main():
    print("This script helps you set up authentication for YouTube Music.")
    print("It uses ytmusicapi to fetch your playlists.")
    print("NOTE: You will need to copy request headers from your browser (Firefox/Chrome).")
    print("1. Open YouTube Music in your browser.")
    print("2. Open Developer Tools (F12) -> Network tab.")
    print("3. Refresh the page.")
    print("4. Right click any request to 'music.youtube.com' (e.g. 'browse').")
    print("5. Copy -> Copy Request Headers.")
    print("6. Paste them below when prompted and press Enter, then Ctrl+Z (Windows) or Ctrl+D (Linux/Mac) and Enter.")
    
    try:
        from ytmusicapi import setup
        print("\nStarting setup...")
        # Check if file exists
        if os.path.exists('oauth.json'):
            print("oauth.json already exists!")
            choice = input("Do you want to re-authenticate? (y/N): ")
            if choice.lower() != 'y':
                return

        # setup function from ytmusicapi.setup module
        setup(filepath="oauth.json")
        print("Success! oauth.json created.")
        
    except ImportError:
        print("Error: ytmusicapi not installed. Please run: pip install ytmusicapi")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
