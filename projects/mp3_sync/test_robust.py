
import os
import json
import subprocess
import time

OAUTH_FILE = 'oauth.json'

def get_authenticated_api():
    from ytmusicapi import YTMusic
    if os.path.exists(OAUTH_FILE):
        return YTMusic(auth=OAUTH_FILE)
    return None

def main():
    print("Testing Robust Strategy...")
    yt = get_authenticated_api()
    if not yt:
        print("No oauth.json found! Run setup_auth.py first.")
        return

    # Try to fetch Liked Music metadata
    print("Fetching Liked Music (limit 5)...")
    try:
        # Note: 'get_liked_songs' returns list of tracks directly
        tracks = yt.get_liked_songs(limit=5)
        print(f"Found {len(tracks)} tracks.")
        
        for track in tracks:
            title = track.get('title')
            artists = track.get('artists')
            artist_name = artists[0]['name'] if artists else 'Unknown'
            video_id = track.get('videoId')
            print(f"  Confirming access to: {title} - {artist_name} ({video_id})")
            
            # Simple check if public download works
            cmd = ['yt-dlp', '--simulate', f'https://music.youtube.com/watch?v={video_id}']
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"    [OK] Publicly accessible.")
            except:
                print(f"    [RESTRICTED] Private/Premium only. Will use search fallback.")
                
    except Exception as e:
        print(f"Error fetching Liked Music: {e}")

if __name__ == "__main__":
    try:
        main()
    except ImportError:
        print("Please install ytmusicapi first (pip install ytmusicapi)")
