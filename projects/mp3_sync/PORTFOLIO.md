---
portfolio: software/mp3_sync
title: MP3 Sync Tool
---
# MP3 Sync Tool

Automatically sync music from YouTube playlists to your MP3 player via Google Drive.

## Features

- Downloads from YouTube using yt-dlp
- Syncs to Google Drive for easy access on mobile devices
- Handles authentication via OAuth
- Configurable via `config.json`

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Run `setup_auth.py` to authorize Google Drive access
3. Configure your playlist URLs in `config.json`
4. Run `run_sync.bat` to start syncing

## Files

- `sync_manager.py` - Main sync logic
- `sync_worker.py` - Background worker for downloading
- `config.json` - Configuration file
