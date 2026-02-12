"""
Sync Engine - Downloads YouTube Music playlists/liked songs to a local folder.
Runs as a background thread, reports progress via shared state.
"""

import os
import json
import subprocess
import threading
import time
from ytmusicapi import YTMusic

# Shared sync state (thread-safe reads)
_sync_state = {
    "running": False,
    "current_track": "",
    "current_playlist": "",
    "tracks_done": 0,
    "tracks_total": 0,
    "errors": [],
    "last_sync": None,
    "playlists_done": 0,
    "playlists_total": 0,
}
_sync_lock = threading.Lock()

# Auth paths in APPDATA
OAUTH_DIR = os.path.join(os.environ.get('APPDATA', ''), 'MP3SyncOAuth')
OAUTH_FILE = os.path.join(OAUTH_DIR, 'oauth.json')
BROWSER_FILE = os.path.join(OAUTH_DIR, 'browser.json')

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'sync_config.json')


def load_sync_config():
    """Load sync_config.json."""
    if not os.path.exists(CONFIG_FILE):
        return {
            "download_folder": os.path.join(os.path.expanduser("~"), "Music", "YTMusic"),
            "sync_liked_music": True,
            "sync_all_playlists": True,
        }
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)


def save_sync_config(data):
    """Save sync_config.json."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=4)


def get_sync_status():
    """Return current sync state (safe to call from any thread)."""
    with _sync_lock:
        return dict(_sync_state)


def _update_state(**kwargs):
    with _sync_lock:
        _sync_state.update(kwargs)


def _get_authenticated_api():
    """Try browser.json first, then oauth.json. Verifies auth works."""
    if os.path.exists(BROWSER_FILE):
        try:
            yt = YTMusic(BROWSER_FILE)
            # Verify auth works by making a simple authenticated call
            yt.get_liked_songs(limit=1)
            return yt
        except Exception as e:
            msg = f"Browser auth invalid/expired (falling back): {e}"
            log_to_manager(msg)
            _update_state(errors=_sync_state["errors"] + [msg])

    if os.path.exists(OAUTH_FILE):
        try:
            yt = YTMusic(OAUTH_FILE)
            # Verify auth works
            yt.get_liked_songs(limit=1)
            return yt
        except Exception as e:
            msg = f"OAuth invalid: {e}"
            log_to_manager(msg)
            _update_state(errors=_sync_state["errors"] + [msg])
            
    return None


def _sanitize_filename(name):
    return "".join([c for c in name if c.isalpha() or c.isdigit() or c in ' .-_()']).strip()


def _download_track(track, folder_path, video_id, cached_tracks):
    """Download a single track via yt-dlp. Returns status string."""
    title = track.get('title', 'Unknown Title')
    artists = track.get('artists', [])
    artist_name = artists[0]['name'] if artists else 'Unknown Artist'
    
    if not video_id:
        return 'failed'

    sanitized = _sanitize_filename(f"{artist_name} - {title}")
    filename = f"{sanitized}.mp3"
    filepath = os.path.join(folder_path, filename)

    # Fast skip check
    if video_id in cached_tracks:
        if os.path.exists(filepath):
            return 'cached'
        # If file missing but in cache, we should re-download, proceed.

    # Regular exists check (in case file exists but not in cache)
    if os.path.exists(filepath):
        return 'exists'

    _update_state(current_track=f"{artist_name} - {title}")

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
        '--output', filepath,
    ]

    # Attempt 1: Direct URL
    try:
        subprocess.run(cmd_base + [url], check=True,
                        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                        creationflags=subprocess.CREATE_NO_WINDOW)
        return 'downloaded'
    except subprocess.CalledProcessError:
        pass

    # Attempt 2: Search fallback
    search_query = f"ytsearch1:{artist_name} - {title} audio"
    try:
        subprocess.run(cmd_base + [search_query], check=True,
                        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                        creationflags=subprocess.CREATE_NO_WINDOW)
        return 'downloaded'
    except subprocess.CalledProcessError as e:
        _update_state(errors=_sync_state["errors"] + [f"Failed: {title}"])
        return 'failed'


def log_to_manager(msg):
    """Send log to Service Manager console."""
    try:
        url = "http://localhost:9870/api/log"
        password = os.environ.get("STARTUP_APPS_PASSWORD", "")
        import requests
        requests.post(url, json={"source": "mp3_sync", "message": msg}, headers={"X-Password": password}, timeout=1)
    except:
        pass


def _sync_worker():
    """Main sync logic. Runs in a background thread."""
    log_to_manager("Sync started")
    config = load_sync_config()
    download_folder = config.get("download_folder", "")

    if not download_folder:
        msg = "No download folder configured"
        _update_state(running=False, errors=[msg])
        log_to_manager(msg)
        return

    os.makedirs(download_folder, exist_ok=True)
    log_to_manager(f"Download folder: {download_folder}")

    # Load cache
    cache_file = os.path.join(download_folder, 'sync_cache.json')
    sync_cache = {"playlists": {}, "tracks": {}}
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                sync_cache = json.load(f)
        except: pass

    yt = _get_authenticated_api()
    if not yt:
        msg = "No YouTube Music auth. Run setup_auth.py"
        _update_state(running=False, errors=_sync_state["errors"] + [msg])
        log_to_manager(msg)
        return

    tasks = []

    # Helper to process playlist
    def process_playlist_meta(pid, p_title, fetch_func):
        # Check cache metadata first if possible (some APIs don't give modification date easily without fetch)
        # We will fetch tracks anyway to be robust, but we can skip download loop if checksum matches.
        
        try:
            data = fetch_func()
            tracks = data.get('tracks', [])
            
            # Calculate checksum: hash of sorted video IDs
            # Use ordered list of IDs to detect reordering if desired, but set is safer for just "content"
            # Let's use ordered list to detect any changes
            video_ids = [t.get('videoId', '') for t in tracks if t.get('videoId')]
            import hashlib
            checksum = hashlib.md5("".join(video_ids).encode('utf-8')).hexdigest()
            
            cached_pl = sync_cache["playlists"].get(pid, {})
            
            # If checksum matches and we are sure files exist (we assume so if cache says so, but user said 'robust'...)
            # To be robust, we rely on checksum. 
            if cached_pl.get('checksum') == checksum and cached_pl.get('count') == len(video_ids):
                log_to_manager(f"Skipping '{p_title}' (Unchanged)")
                return None # Skip this task
            
            return {'id': pid, 'name': p_title, 'tracks': tracks, 'checksum': checksum}
        except Exception as e:
            msg = f"Error fetching '{p_title}': {e}"
            _update_state(errors=_sync_state["errors"] + [msg])
            log_to_manager(msg)
            return None

    if config.get("sync_liked_music", True):
        log_to_manager("Checking Liked Music...")
        task = process_playlist_meta('LM', 'Liked Music', lambda: yt.get_liked_songs(limit=None))
        if task: tasks.append(task)

    if config.get("sync_all_playlists", True):
        log_to_manager("Checking Playlists...")
        try:
            playlists = yt.get_library_playlists(limit=None)
            for p in playlists:
                if not _sync_state["running"]: break
                pid = p.get('playlistId')
                title = p.get('title')
                if pid and title:
                    task = process_playlist_meta(pid, title, lambda: yt.get_playlist(pid, limit=None))
                    if task: tasks.append(task)
        except Exception as e:
            log_to_manager(f"Library fetch error: {e}")

    # Count total tracks
    total_tracks = sum(len(t['tracks']) for t in tasks)
    log_to_manager(f"Total tracks to process: {total_tracks}")
    _update_state(playlists_total=len(tasks), tracks_total=total_tracks)

    done = 0
    # Pre-load track cache checks
    cached_tracks = set(sync_cache.get("tracks", {}).keys())

    for pi, task in enumerate(tasks):
        if not _sync_state["running"]: break
        folder_name = _sanitize_filename(task['name'])
        folder_path = os.path.join(download_folder, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        _update_state(current_playlist=task['name'], playlists_done=pi)
        log_to_manager(f"Syncing: {task['name']}")

        track_success_count = 0
        for track in task['tracks']:
            if not _sync_state["running"]: return
            
            vid = track.get('videoId')
            title = track.get('title', 'Unknown')
            
            # Fast skip: if in cache and file exists
            if vid in cached_tracks:
                # We trust cache mostly, but verify filename if possible?
                # Actually, simply checking if vid is in cache is often enough if we trust our cache.
                # But let's check file existence in _download_track logic.
                pass

            status = _download_track(track, folder_path, vid, cached_tracks)
            
            if status == 'downloaded':
                log_to_manager(f"Downloaded: {title}")
                track_success_count += 1
                if vid: sync_cache["tracks"][vid] = 1
            elif status == 'cached':
                log_to_manager(f"Skipped (Cached): {title}")
                track_success_count += 1
                if vid: sync_cache["tracks"][vid] = 1 
            elif status == 'exists':
                log_to_manager(f"Skipped (Exists): {title}")
                track_success_count += 1
                if vid: sync_cache["tracks"][vid] = 1
            else:
                log_to_manager(f"Failed: {title}")

            done += 1
            _update_state(tracks_done=done)

        # Update playlist cache
        sync_cache["playlists"][task['id']] = {
            'checksum': task['checksum'],
            'count': len(task['tracks']),
            'last_synced': time.time()
        }
        
        # Save cache periodically
        with open(cache_file, 'w') as f:
            json.dump(sync_cache, f)

    log_to_manager("Sync completed")
    
    # Final save
    with open(cache_file, 'w') as f:
        json.dump(sync_cache, f)

    _update_state(
        running=False,
        current_track="",
        current_playlist="Idle",
        playlists_done=len(tasks),
        last_sync=time.strftime("%Y-%m-%d %H:%M:%S"),
    )


def start_sync():
    """Start a sync in a background thread. Returns (success, message)."""
    if _sync_state["running"]:
        return False, "Sync already running"

    _update_state(
        running=True,
        current_track="",
        current_playlist="Starting...",
        tracks_done=0,
        tracks_total=0,
        errors=[],
        playlists_done=0,
        playlists_total=0,
    )

    t = threading.Thread(target=_sync_worker, daemon=True)
    t.start()
    return True, "Sync started"


def stop_sync():
    """Signal the sync to stop."""
    if not _sync_state["running"]:
        return False, "No sync running"
    _update_state(running=False)
    log_to_manager("Stopping sync...")
    return True, "Sync stopping..."
