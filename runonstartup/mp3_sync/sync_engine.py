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
    """Try browser.json first, then oauth.json."""
    if os.path.exists(BROWSER_FILE):
        try:
            return YTMusic(BROWSER_FILE)
        except Exception as e:
            _update_state(errors=_sync_state["errors"] + [f"Browser auth error: {e}"])
    if os.path.exists(OAUTH_FILE):
        try:
            return YTMusic(OAUTH_FILE)
        except Exception as e:
            _update_state(errors=_sync_state["errors"] + [f"OAuth error: {e}"])
    return None


def _sanitize_filename(name):
    return "".join([c for c in name if c.isalpha() or c.isdigit() or c in ' .-_()']).strip()


def _download_track(track, folder_path):
    """Download a single track via yt-dlp. Returns True on success."""
    title = track.get('title', 'Unknown Title')
    artists = track.get('artists', [])
    artist_name = artists[0]['name'] if artists else 'Unknown Artist'
    video_id = track.get('videoId')

    if not video_id:
        return False

    sanitized = _sanitize_filename(f"{artist_name} - {title}")
    filename = f"{sanitized}.mp3"
    filepath = os.path.join(folder_path, filename)

    # Already exists
    if os.path.exists(filepath):
        return True

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
        return True
    except subprocess.CalledProcessError:
        pass

    # Attempt 2: Search fallback
    search_query = f"ytsearch1:{artist_name} - {title} audio"
    try:
        subprocess.run(cmd_base + [search_query], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                       creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    except subprocess.CalledProcessError as e:
        _update_state(errors=_sync_state["errors"] + [f"Failed: {title}"])
        return False


def _sync_worker():
    """Main sync logic. Runs in a background thread."""
    config = load_sync_config()
    download_folder = config.get("download_folder", "")

    if not download_folder:
        _update_state(running=False, errors=["No download folder configured"])
        return

    os.makedirs(download_folder, exist_ok=True)

    yt = _get_authenticated_api()
    if not yt:
        _update_state(running=False, errors=_sync_state["errors"] + ["No YouTube Music auth. Run setup_auth.py"])
        return

    tasks = []

    # Fetch liked music
    if config.get("sync_liked_music", True):
        _update_state(current_playlist="Fetching Liked Music...")
        try:
            liked = yt.get_liked_songs(limit=None)
            tracks = liked.get('tracks', [])
            tasks.append({'name': 'Liked Music', 'tracks': tracks})
        except Exception as e:
            _update_state(errors=_sync_state["errors"] + [f"Liked Music fetch error: {e}"])

    # Fetch all playlists
    if config.get("sync_all_playlists", True):
        _update_state(current_playlist="Fetching playlists...")
        try:
            playlists = yt.get_library_playlists(limit=None)
            for p in playlists:
                pid = p.get('playlistId')
                title = p.get('title')
                if pid and title:
                    try:
                        pl_data = yt.get_playlist(pid, limit=None)
                        tracks = pl_data.get('tracks', [])
                        tasks.append({'name': title, 'tracks': tracks})
                    except Exception as e:
                        _update_state(errors=_sync_state["errors"] + [f"Playlist '{title}' error: {e}"])
        except Exception as e:
            _update_state(errors=_sync_state["errors"] + [f"Library fetch error: {e}"])

    # Count total tracks
    total_tracks = sum(len(t['tracks']) for t in tasks)
    _update_state(playlists_total=len(tasks), tracks_total=total_tracks)

    done = 0
    for pi, task in enumerate(tasks):
        folder_name = _sanitize_filename(task['name'])
        folder_path = os.path.join(download_folder, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        _update_state(current_playlist=task['name'], playlists_done=pi)

        for track in task['tracks']:
            if not _sync_state["running"]:
                return  # Cancelled
            _download_track(track, folder_path)
            done += 1
            _update_state(tracks_done=done)

    _update_state(
        running=False,
        current_track="",
        current_playlist="",
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
    return True, "Sync stopping..."
