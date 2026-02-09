# Run On Startup Apps - AI Agent Guide

This directory contains startup web applications. This README is specifically for **AI coding agents** working on these applications.

## Quick Reference for AI Agents

### Directory Structure
```
runonstartup/
├── start_all.bat          # Master startup (runs all apps silently)
├── kill_all.bat           # Stops all apps (Python + Cloudflare)
├── restart_all.bat        # Kill + Start all apps
├── README.md              # This file - AI agent guide
│
├── fbreader_web/          # FBReader ebook library (port 5555)
├── google_tasks/          # Google Tasks automation (port 5556)
└── parts_inventory/       # Parts inventory (port 5557)
```

### Port Assignments
| App | Port | Domain |
|-----|------|--------|
| parts_inventory | 8000 | organizer.noahsmith.dev |
| fbreader_web | 5555 | books.noahsmith.dev |
| google_tasks | 5556 | tasks.noahsmith.dev |

**When adding new apps, use the next available port (5557, 5558, etc.)**

---

## Commands for AI Agents

### Starting/Stopping Apps

```powershell
# Kill all Python processes and Cloudflare tunnel
taskkill /F /IM python.exe; taskkill /F /IM cloudflared.exe

# Start an app with the password environment variable
$env:STARTUP_APPS_PASSWORD = [Environment]::GetEnvironmentVariable("STARTUP_APPS_PASSWORD", "User"); py app.py

# Check if an app is running
Invoke-WebRequest -Uri "http://localhost:5556/api/status" -UseBasicParsing | Select-Object -ExpandProperty Content

# Test external domain
Invoke-WebRequest -Uri "https://tasks.noahsmith.dev/api/status" -UseBasicParsing -TimeoutSec 10
```

### Environment Variables
The user has set these as **Windows User environment variables** (not system-wide):

```powershell
# Read a user environment variable
[Environment]::GetEnvironmentVariable("STARTUP_APPS_PASSWORD", "User")

# Set env var for current process (required when starting Flask apps)
$env:STARTUP_APPS_PASSWORD = [Environment]::GetEnvironmentVariable("STARTUP_APPS_PASSWORD", "User")
```

**IMPORTANT**: Flask apps started from your terminal do NOT automatically inherit user env vars. You MUST set them explicitly like above.

### Cloudflare Tunnel Commands

```powershell
# List tunnels
cloudflared tunnel list

# Run the tunnel manually (connects all configured domains)
cloudflared tunnel run fbreader

# Check tunnel config
cat C:\Users\LRNA\.cloudflared\config.yml

# Add a new domain route to existing tunnel
cloudflared tunnel route dns fbreader newapp.noahsmith.dev
```

The tunnel config is at: `C:\Users\LRNA\.cloudflared\config.yml`

---

## Design Guidelines

### OLED High Contrast Theme
All apps use a consistent OLED-optimized theme matching `parts_inventory`:

```css
:root {
    --bg-dark: #000000;        /* Pure black background */
    --accent-primary: #ffffff;  /* White for main elements */
    --accent-secondary: #00ffff; /* Cyan for highlights */
    --text-main: #ffffff;
    --text-muted: #cccccc;
    --border-color: #ffffff;    /* High contrast borders */
    --border-subtle: #333333;
}
```

**Key design principles:**
- Pure black backgrounds (#000000) for OLED power saving
- White borders for high contrast
- Cyan (#00ffff) for interactive/accent elements
- No border-radius (sharp corners for tech aesthetic)
- Minimal shadows (OLED doesn't need them)
- Monospace fonts for technical data

### App Structure Template
Each app follows this structure:

```
app_name/
├── app.py                 # Flask application
├── config.py              # Configuration (uses STARTUP_APPS_PASSWORD)
├── requirements.txt       # Python dependencies
├── README.md              # App-specific documentation
├── start_appname.bat      # Manual startup (visible windows)
├── start_silent.vbs       # Silent startup for auto-start
├── .gitignore
├── static/
│   └── css/
│       └── style.css      # OLED theme styles
└── templates/
    ├── base.html
    ├── login.html         # Password authentication
    └── ...
```

### Authentication Pattern
All apps use the same password from `STARTUP_APPS_PASSWORD`:

```python
# In config.py
ACCESS_PASSWORD = os.environ.get("STARTUP_APPS_PASSWORD")

# In app.py - Authentication check
def is_authenticated() -> bool:
    if session.get('authenticated'):
        return True
    client_ip = get_client_ip()
    if client_ip in authenticated_ips:
        if authenticated_ips[client_ip] > datetime.now():
            return True
    return False

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == config.ACCESS_PASSWORD:
            session['authenticated'] = True
            # ... success
```

### VBS Silent Startup Template
For new apps, use this start_silent.vbs template:

```vbscript
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "c:\Users\LRNA\Desktop\code\runonstartup\app_name"

' Load user environment variable
Set WshEnv = WshShell.Environment("USER")
password = WshEnv("STARTUP_APPS_PASSWORD")
Set procEnv = WshShell.Environment("PROCESS")
procEnv("STARTUP_APPS_PASSWORD") = password

' Start Flask app hidden
WshShell.Run "cmd /c py app.py", 0

Set WshShell = Nothing
```

---

## Common Issues & Solutions

### 1. "Invalid Password" on Login
**Cause**: The Flask app was started without the environment variable.

**Fix**:
```powershell
# Kill and restart with env var explicitly set
taskkill /F /IM python.exe
$env:STARTUP_APPS_PASSWORD = [Environment]::GetEnvironmentVariable("STARTUP_APPS_PASSWORD", "User"); py app.py
```

### 2. Domain Not Routing Correctly
**Cause**: Cloudflare tunnel needs restart after config changes.

**Fix**:
```powershell
taskkill /F /IM cloudflared.exe
cloudflared tunnel run fbreader
```

### 3. Port Already in Use
**Cause**: Old Python process still running.

**Fix**:
```powershell
# Kill all Python processes
taskkill /F /IM python.exe
# Or find specific process
netstat -ano | findstr :5556
taskkill /F /PID <pid>
```

### 4. Flask Watchdog Reload Loses Env Vars
**Cause**: Debug mode restarts lose the environment variable.

**Fix**: Set `debug=False` in production, or always restart manually for development.

---

## Adding a New App

1. **Create directory**: `runonstartup/new_app/`
2. **Choose port**: Use next available (5558+)
3. **Copy templates** from existing app:
   - `config.py` (update port)
   - `templates/base.html`, `templates/login.html`
   - `static/css/style.css`
   - `start_silent.vbs` (update paths)
4. **Update tunnel config** at `~/.cloudflared/config.yml`:
   ```yaml
   - hostname: newapp.noahsmith.dev
     service: http://127.0.0.1:5558
   ```
5. **Add DNS route**:
   ```powershell
   cloudflared tunnel route dns fbreader newapp.noahsmith.dev
   ```
6. **Add to start_all.bat**:
   ```batch
   start "" "C:\Users\LRNA\Desktop\code\runonstartup\new_app\start_silent.vbs"
   ```

---

## Testing Checklist

Before considering an app complete:

- [ ] App starts without errors
- [ ] Login works with `STARTUP_APPS_PASSWORD`
- [ ] `/api/status` returns OK (public health check)
- [ ] Cloudflare domain routes correctly
- [ ] `start_silent.vbs` works (loads env var, runs hidden)
- [ ] App added to `start_all.bat`
- [ ] Styles match OLED theme (pure black, cyan accents)
- [ ] Mobile responsive

---

*This guide is maintained for AI coding agents. Update when adding new patterns or common issues.*
