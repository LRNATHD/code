# MP3 Auto-Sync Project

This project automatically syncs your YouTube Music playlists to your MP3 player when connected to your computer.

## Setup

1.  **Edit `config.json`**:
    *   `drive_label`: The Volume Label of your MP3 player (e.g., "MY_MP3" or "WALKMAN"). You can find this in "This PC" next to the drive letter.
    *   `playlists`: Add the URLs of the YouTube Music playlists you want to sync.
        *   Example: `["https://music.youtube.com/playlist?list=PL...", "https://music.youtube.com/playlist?list=PL..."]`
    *   `music_root_folder`: The folder on your MP3 player where music should go (default: "Music").
    *   `browser_for_cookies`: The browser you use for YouTube Music (e.g., "chrome", "firefox", "edge"). This allows the script to access your private playlists and premium quality.

2.  **Run the Script**:
    *   Open a terminal in this folder.
    *   Run: `python sync_manager.py` (or click on `run_sync.bat` if you create one).
    *   The script will wait for your MP3 player to be connected.

## How it works

*   The script runs in a loop checking for the drive label you specified.
*   When detected, it downloads new songs from the configured playlists using `yt-dlp`.
*   It organizes songs into folders: `MP3_PLAYER/Music/PlaylistName/Song.mp3`.
*   It remembers downloaded songs in a `download_archive.txt` file on the device so it only downloads new ones.

## Dependencies

*   Python 3.x
*   `yt-dlp`
*   `psutil`

To install dependencies:
```bash
pip install yt-dlp psutil
```
