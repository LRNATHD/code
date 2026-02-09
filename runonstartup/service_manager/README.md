# Service Manager Dashboard

Config-driven dashboard for managing all startup services.

## Quick Start

```powershell
# Start the dashboard
cd c:\Users\LRNA\Desktop\code\runonstartup\service_manager
python app.py
```

Open http://localhost:9870 in your browser.

## Adding New Services

Edit `services.json` to add a new service:

```json
{
  "id": "new_app",
  "name": "My New App",
  "internal_port": 9874,
  "path": "/newapp",
  "domain": "newapp.noahsmith.dev",
  "dir": "../new_app",
  "start_cmd": "py app.py",
  "health_url": "/api/status",
  "type": "flask",
  "description": "Description of the app"
}
```

Then add the Cloudflare route:
```powershell
cloudflared tunnel route dns fbreader newapp.noahsmith.dev
```

## Port Assignments

| Service | Port |
|---------|------|
| Service Manager | 9870 |
| FBReader Web | 9871 |
| Google Tasks | 9872 |
| Parts Inventory | 9873 |

## Files

- `services.json` - Service registry (AI agents add here)
- `manager.py` - Process management
- `app.py` - Flask dashboard
- `start_silent.vbs` - Auto-start script
