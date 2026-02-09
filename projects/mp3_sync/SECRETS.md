# 🔐 MP3 Sync - Secrets & Credentials

## Overview
This project syncs YouTube Music playlists to an MP3 player. It requires YouTube Music authentication credentials.

## Credential Location
**All sensitive files are stored OUTSIDE this repo in `%APPDATA%\MP3SyncOAuth\`:**

```
C:\Users\LRNA\AppData\Roaming\MP3SyncOAuth\
├── oauth.json      # YouTube Music session headers/cookies (from ytmusicapi)
└── cookies.txt     # Browser cookies backup (optional)
```

## How It Works
- `sync_manager.py` reads `OAUTH_FILE` from `%APPDATA%\MP3SyncOAuth\oauth.json`
- The `ytmusicapi` library uses this for authenticated YouTube Music API calls
- No credentials are stored in this repository

## Setup for New Machines
1. Run `ytmusicapi oauth` in the terminal
2. Follow the browser auth flow
3. Move the generated `oauth.json` to `%APPDATA%\MP3SyncOAuth\`

Or copy from an existing machine:
```powershell
Copy-Item "$env:APPDATA\MP3SyncOAuth" -Destination "\\NewMachine\..." -Recurse
```

## For AI Agents
- **NEVER** commit `oauth.json` or `cookies.txt` to this repo
- Credentials path is defined at top of `sync_manager.py`
- If auth fails, the user needs to re-run `ytmusicapi oauth`
