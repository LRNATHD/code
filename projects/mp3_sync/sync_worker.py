
import os
import json
import subprocess
import glob
import time
import sys
from ytmusicapi import YTMusic

CONFIG_FILE = 'config.json'
OAUTH_FILE = 'oauth.json'

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def run_sync(drive_letter):
    config = load_config()
    music_root = config.get('music_root_folder', 'Music')
    
    # 1. Liked Music
    if config.get('sync_liked_music', True):
        print("\nSyncing Liked Music...")
        # Use yt-dlp on LM playlist
        cmd = [
            'yt-dlp',
            '--cookies-from-browser', config.get('browser_for_cookies', 'librewolf'),
            '--extract-audio',
            '--audio-format', 'mp3',
            '--audio-quality', '0',
            '--embed-thumbnail',
            '--embed-metadata',
            '--download-archive', os.path.join(drive_letter, music_root, 'download_archive.txt'),
            '--output', os.path.join(drive_letter, music_root, 'Liked Music/%(title)s.%(ext)s'),
            'https://music.youtube.com/playlist?list=LM'
        ]
        subprocess.run(cmd)

    # 2. All Playlists
    if config.get('sync_all_playlists', True):
        print("\nFetching All Playlists...")
        if not os.path.exists(OAUTH_FILE):
             print("Error: Oauth file not found. Run setup_auth.py first.")
        else:
            try:
                yt = YTMusic(OAUTH_FILE)
                playlists = yt.get_library_playlists(limit=None)
                print(f"Found {len(playlists)} playlists.")
                
                for p in playlists:
                    print(f"Syncing: {p['title']}")
                    cmd = [
                        'yt-dlp',
                        '--cookies-from-browser', config.get('browser_for_cookies', 'librewolf'),
                        '--extract-audio',
                        '--audio-format', 'mp3',
                        '--audio-quality', '0',
                        '--embed-thumbnail',
                        '--embed-metadata',
                        '--download-archive', os.path.join(drive_letter, music_root, 'download_archive.txt'),
                        '--output', os.path.join(drive_letter, music_root, f"{p['title']}/%(title)s.%(ext)s"),
                        f"https://music.youtube.com/playlist?list={p['playlistId']}"
                    ]
                    subprocess.run(cmd)
            except Exception as e:
                print(f"Error fetching playlists: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        drive = sys.argv[1]
        run_sync(drive)
    else:
        print("Usage: python sync_manager.py <drive_letter>")
