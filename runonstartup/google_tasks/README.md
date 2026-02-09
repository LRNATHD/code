# Google Tasks Custom App

A web application for automating Google Tasks with custom rules, such as incrementing timers on recurring tasks.

**URL**: https://tasks.noahsmith.dev

## Features

- **View all task lists and tasks** from your Google account
- **Create automation rules** to modify task titles automatically
- **Increment duration values** (e.g., "Plank 1:00" → "Plank 1:01")
- **Count increments** (e.g., "Day 1" → "Day 2")
- **Secure access** with password authentication via Cloudflare Tunnel

## Example Use Case: Progressive Plank Timer

1. Create a recurring task in Google Tasks: "Plank 1:00"
2. Create an automation rule:
   - **Name**: Plank Timer Increment
   - **Pattern**: `plank \d+:\d{2}` (regex to match "plank" followed by time)
   - **Increment Type**: Duration (M:SS format)
   - **Increment Value**: 1 (add 1 second each time)
3. When you complete the task and it reappears, click "Apply" to increment:
   - Day 1: "Plank 1:00"
   - Day 2: "Plank 1:01"
   - Day 3: "Plank 1:02"
   - etc.

## Setup

### 1. Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select an existing one
3. Enable the **Google Tasks API**:
   - Navigate to **APIs & Services > Library**
   - Search for "Google Tasks API"
   - Click **Enable**
4. Create OAuth credentials:
   - Navigate to **APIs & Services > Credentials**
   - Click **Create Credentials > OAuth 2.0 Client ID**
   - Select **Desktop app** as the application type
   - Download the JSON file
   - Rename it to `credentials.json`
   - Place it in `google_tasks/credentials/`

### 2. Environment Setup

Set the shared password environment variable:

```powershell
# PowerShell (temporary for current session)
$env:STARTUP_APPS_PASSWORD = "your-secure-password"

# Or permanently via System Properties > Environment Variables
```

### 3. Install Dependencies

```bash
cd runonstartup/google_tasks
pip install -r requirements.txt
```

### 4. Cloudflare Tunnel Setup

```bash
# Login to Cloudflare
cloudflared tunnel login

# Create the tunnel
cloudflared tunnel create tasks

# Configure the tunnel (add to ~/.cloudflared/config.yml)
# tunnel: <tunnel-id>
# credentials-file: ~/.cloudflared/<tunnel-id>.json
# ingress:
#   - hostname: tasks.noahsmith.dev
#     service: http://localhost:5556
#   - service: http_status:404

# Add DNS route
cloudflared tunnel route dns tasks tasks.noahsmith.dev
```

### 5. First Run (Manual)

Run the app manually first to complete OAuth:

```bash
cd runonstartup/google_tasks
py app.py
```

Visit http://localhost:5556 and complete the Google OAuth flow.

### 6. Auto-Start

The app is automatically started by `start_all.bat` in the parent directory.

## Project Structure

```
google_tasks/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── tasks_client.py        # Google Tasks API client + rules engine
├── requirements.txt       # Python dependencies
├── start_tasks.bat        # Manual startup script
├── start_silent.vbs       # Silent startup script
├── credentials/           # OAuth credentials (gitignored)
│   ├── README.md
│   ├── credentials.json   # Download from Google Cloud
│   └── token.json         # Auto-generated after auth
├── data/                  # App data
│   └── rules.json         # Saved automation rules
├── static/
│   └── css/
│       └── style.css      # Application styles
└── templates/
    ├── base.html          # Base template
    ├── login.html         # Login page
    ├── dashboard.html     # Main dashboard
    ├── setup.html         # OAuth setup instructions
    └── error.html         # Error page
```

## API Endpoints

### Authentication
- `GET /login` - Login page
- `POST /login` - Submit password
- `GET /logout` - Clear session

### Task Lists
- `GET /api/task-lists` - Get all task lists

### Tasks
- `GET /api/tasks/<list_id>` - Get tasks in a list
- `GET /api/task/<list_id>/<task_id>` - Get specific task
- `POST /api/task/<list_id>` - Create new task
- `PATCH /api/task/<list_id>/<task_id>` - Update task
- `DELETE /api/task/<list_id>/<task_id>` - Delete task

### Rules
- `GET /api/rules` - Get all rules
- `POST /api/rules` - Create new rule
- `PATCH /api/rules/<rule_id>` - Update rule
- `DELETE /api/rules/<rule_id>` - Delete rule
- `POST /api/rules/<rule_id>/test` - Test rule against sample title
- `POST /api/apply-rule` - Apply rule to a task

### Status
- `GET /api/status` - Health check (public)
