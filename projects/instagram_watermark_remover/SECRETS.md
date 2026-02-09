# 🔐 Instagram Watermark Remover - Secrets & Credentials

## Overview
This project removes watermarks from Instagram photos using Google Photos API. It requires Google OAuth credentials.

## Credential Location
**All sensitive files are stored OUTSIDE this repo in `%APPDATA%\InstagramWatermarkRemover\`:**

```
C:\Users\LRNA\AppData\Roaming\InstagramWatermarkRemover\
└── client_secret.json    # Google OAuth client ID + secret
```

## What These Files Contain
- **client_secret.json** — Google Cloud OAuth client configuration
  - `client_id`: Your app's public identifier
  - `client_secret`: 🔴 SENSITIVE - secret key for OAuth flow
  - Project: `watermark-remover-486201`

## Setup for New Machines
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to APIs & Services > Credentials
3. Download the OAuth client JSON
4. Place it in `%APPDATA%\InstagramWatermarkRemover\client_secret.json`

Or copy from an existing machine:
```powershell
Copy-Item "$env:APPDATA\InstagramWatermarkRemover" -Destination "\\NewMachine\..." -Recurse
```

## For AI Agents
- **NEVER** commit `client_secret.json` to this repo
- Original location was `credentials/client_secret.json` — that folder is now deleted
- If you add new credential-loading code, use:
  ```python
  import os
  CREDS_DIR = os.path.join(os.environ.get('APPDATA', ''), 'InstagramWatermarkRemover')
  CLIENT_SECRET = os.path.join(CREDS_DIR, 'client_secret.json')
  ```
