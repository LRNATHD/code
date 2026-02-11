
import os
import time
import json
import subprocess
import psutil
import sys
import ctypes
from ytmusicapi import YTMusic

CONFIG_FILE = 'config.json'
# Auth credentials stored in APPDATA (outside repo for security)
OAUTH_DIR = os.path.join(os.environ.get('APPDATA', ''), 'MP3SyncOAuth')
OAUTH_FILE = os.path.join(OAUTH_DIR, 'oauth.json')
BROWSER_FILE = os.path.join(OAUTH_DIR, 'browser.json')
DEFAULT_CONFIG = {
    "drive_label": "MP3PLAYER",
    "music_root_folder": "Music",
    "playlists": [],
    "sync_liked_music": True,
    "sync_all_playlists": True,
    "fallback_to_search": True
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def get_volume_label(drive_letter):
    try:
        kernel32 = ctypes.windll.kernel32
        volumeNameBuffer = ctypes.create_unicode_buffer(1024)
        fileSystemNameBuffer = ctypes.create_unicode_buffer(1024)
        drive_path = drive_letter if drive_letter.endswith('\\') else drive_letter + '\\'
        success = kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p(drive_path),
            volumeNameBuffer,
            ctypes.sizeof(volumeNameBuffer),
            None,
            None,
            None,
            fileSystemNameBuffer,
            ctypes.sizeof(fileSystemNameBuffer)
        )
        if success:
            return volumeNameBuffer.value
    except Exception:
        pass
    return None

def find_drive_by_label(target_label):
    drives = psutil.disk_partitions()
    for drive in drives:
        label = get_volume_label(drive.device)
        if label and target_label.lower() == label.lower():
            return drive.device
    return None

def get_authenticated_api():
    """Try browser.json first, then oauth.json."""
    # Preferred: browser headers auth
    if os.path.exists(BROWSER_FILE):
        try:
            return YTMusic(BROWSER_FILE)
        except Exception as e:
            print(f"Error with browser auth: {e}")
    # Fallback: OAuth tokens
    if os.path.exists(OAUTH_FILE):
        try:
            return YTMusic(OAUTH_FILE)
        except Exception as e:
            print(f"Error with OAuth auth: {e}")
    print("No auth found! Run: python setup_auth.py")
    return None

def sanitize_filename(name):
    # Basic sanitize
    return "".join([c for c in name if c.isalpha() or c.isdigit() or c in ' .-_()']).strip()

def download_track(track, folder_path, archive_file):
    """
    Downloads a single track using yt-dlp.
    Tries direct ID first, falls back to search if configured.
    """
    title = track.get('title', 'Unknown Title')
    artists = track.get('artists', [])
    artist_name = artists[0]['name'] if artists else 'Unknown Artist'
    video_id = track.get('videoId')
    
    if not video_id:
        return
        
    # Construct filename
    sanitized_title = sanitize_filename(title)
    filename = f"{sanitized_title}.mp3"
    filepath = os.path.join(folder_path, filename)

    # Simple check if file already exists (ignoring archive file for now as it's partial)
    if os.path.exists(filepath):
        #print(f"Skipping {title} (already exists).")
        return

    print(f"Downloading: {title} - {artist_name}")
    
    # Attempt 1: Direct Video ID (fastest, most accurate)
    url = f"https://music.youtube.com/watch?v={video_id}"
    
    cmd_base = [
        'yt-dlp',
        '--extract-audio',
        '--audio-format', 'mp3',
        '--audio-quality', '0',
        '--embed-thumbnail',
        '--embed-metadata',
        '--no-progress',
        '--cookies-from-browser', 'firefox',
        '--remote-components', 'ejs:github',
        '--output', filepath, # Direct output to file
    ]
    
    try:
        subprocess.run(cmd_base + [url], check=True, stderr=subprocess.PIPE)
        print(f"  [Direct] Success.")
        return
    except subprocess.CalledProcessError:
        # direct download failed
        pass

    # Attempt 2: Search (robuster)
    print(f"  [Direct] Failed. Trying search fallback...")
    search_query = f"ytsearch1:{artist_name} - {title} audio"
    
    try:
        subprocess.run(cmd_base + [search_query], check=True, stderr=subprocess.PIPE)
        print(f"  [Search] Success.")
    except subprocess.CalledProcessError as e:
        print(f"  [Error] Failed to download {title}: {e}")

def sync_items(drive_letter, config):
    music_root = os.path.join(drive_letter, config.get('music_root_folder', 'Music'))
    if not os.path.exists(music_root):
        os.makedirs(music_root, exist_ok=True)
        
    yt = get_authenticated_api()
    if not yt and config.get('sync_all_playlists'):
        print("Warning: No OAuth file. Can't access library playlists.")

    tasks = []

    # 1. Liked Music
    if config.get('sync_liked_music', False) and yt:
        print("Fetching 'Liked Music' list...")
        try:
            # get_liked_songs returns a playlist dict, tracks are in 'tracks' key
            liked_music_info = yt.get_liked_songs(limit=None)
            tracks = liked_music_info.get('tracks', [])
            tasks.append({'name': 'Liked Music', 'tracks': tracks})
            print(f"  Found {len(tracks)} songs.")
        except Exception as e:
            print(f"  Error fetching Liked Music: {e}")

    # 2. All Library Playlists
    if config.get('sync_all_playlists', False) and yt:
        print("Fetching Library Playlists...")
        try:
            playlists = yt.get_library_playlists(limit=None)
            for p in playlists:
                pid = p.get('playlistId')
                title = p.get('title')
                if pid and title:
                    # Get tracks for this playlist
                    # We might need to iterate pages if it's huge, 
                    # but get_playlist(pid, limit=None) usually handles it
                    try:
                        pl_data = yt.get_playlist(pid, limit=None)
                        tracks = pl_data.get('tracks', [])
                        tasks.append({'name': title, 'tracks': tracks})
                        print(f"  Found '{title}': {len(tracks)} songs.")
                    except Exception as e:
                        print(f"  Error fetching playlist '{title}': {e}")
        except Exception as e:
            print(f"  Error fetching library: {e}")

    # Process Tasks
    archive_file = os.path.join(music_root, 'download_archive.txt')
    
    print(f"\nProcessing {len(tasks)} playlists...")
    
    for task in tasks:
        folder_name = sanitize_filename(task['name'])
        folder_path = os.path.join(music_root, folder_name)
        
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            
        print(f"\nSyncing: {task['name']} ({len(task['tracks'])} tracks)")
        
        for track in task['tracks']:
             download_track(track, folder_path, archive_file)

def main():
    print("MP3 Sync Service Started (Robust Mode)...")
    config = load_config()
    target_label = config.get('drive_label', 'MP3PLAYER')
    print(f"Waiting for drive: {target_label} ...")
    
    last_drive = None
    
    while True:
        try:
            config = load_config()
            target_label = config.get('drive_label', 'MP3PLAYER')
            drive = find_drive_by_label(target_label)
            
            if drive:
                if drive != last_drive:
                    print(f"\n>> Drive detected: {drive} (Label: {target_label})")
                    print(">> Starting sync...")
                    try:
                        sync_items(drive, config)
                        print("\n>> Sync complete!")
                    except Exception as e:
                        print(f"Critical error during sync: {e}")
                    last_drive = drive
            else:
                last_drive = None
                
            time.sleep(5)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
