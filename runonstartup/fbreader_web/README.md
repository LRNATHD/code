# FBReader Web

A web-based reader for accessing your **FBReader Book Network** library from any device, including download-blocked devices. This application leverages your existing FBReader authentication to provide seamless access to your ebook library.

## Features

- 🔐 **Password-Protected Access** - Simple password authentication with IP-based session persistence
- 📚 **Full Library Access** - View all your synced FBReader books
- 📖 **In-Browser ePub Reader** - Read ePub books directly in your browser using epub.js
- 🎨 **Multiple Reading Themes** - Light, Sepia, and Dark modes
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile devices
- 🔖 **Progress Syncing** - Reading progress is saved back to your FBReader database
- 🔍 **Search & Filter** - Find books quickly with search and filter options

## How It Works

This application:
1. Reads your FBReader's local SQLite database for book metadata
2. Uses your existing FBReader session cookies to authenticate with the Book Network
3. Downloads and caches books for web-based reading
4. Syncs reading progress back to the local database

## Prerequisites

- **FBReader** installed on the server (Windows UWP version)
- **Python 3.10+** 
- FBReader must be **logged into your Book Network account**

## Installation

1. **Clone or copy this folder** to your server

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the application** (edit `config.py`):
   ```python
   # Change the access password!
   ACCESS_PASSWORD = "your-secure-password"
   
   # Update FBReader path if different
   FBREADER_BASE = Path(r"C:\Users\YOUR_USER\AppData\Local\Packages\FBReader_n0j83cvmz1mee")
   ```

4. **Run the server:**
   ```bash
   python app.py
   ```

5. **Access from any device:**
   Navigate to `http://YOUR_SERVER_IP:5555` in a web browser

## Configuration

Edit `config.py` to customize:

| Setting | Description | Default |
|---------|-------------|---------|
| `PORT` | Server port | `5555` |
| `ACCESS_PASSWORD` | Password for authentication | `changeme123` |
| `SESSION_TIMEOUT_HOURS` | How long sessions last | `168` (1 week) |
| `FBREADER_BASE` | Path to FBReader data folder | Windows UWP path |

## Project Structure

```
fbreader_web/
├── app.py              # Flask application
├── config.py           # Configuration settings
├── fbreader_client.py  # FBReader database/API client
├── requirements.txt    # Python dependencies
├── cache/              # Downloaded book cache
├── templates/          # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── library.html
│   └── reader.html
└── static/
    ├── css/
    │   ├── style.css   # Main styles
    │   └── reader.css  # Reader styles
    ├── js/
    │   ├── library.js  # Library page logic
    │   └── reader.js   # ePub reader logic
    └── img/
        └── no-cover.svg
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Health check (public) |
| `/api/books` | GET | List all books |
| `/api/book/<id>` | GET | Get book details |
| `/api/book/<id>/content` | GET | Get book file |
| `/api/book/<id>/cover` | GET | Get book cover |
| `/api/book/<id>/position` | POST | Update reading position |

## Security Notes

⚠️ **Important Security Considerations:**

1. **Change the default password** in `config.py` before deploying
2. Consider using **HTTPS** in production (use a reverse proxy like nginx)
3. The server stores FBReader session cookies - keep the cache directory secure
4. IP-based authentication provides convenience but can be bypassed on shared networks

## Troubleshooting

### "Database not found"
Make sure FBReader is installed and has been opened at least once. The database is created when FBReader first syncs.

### "Cookies not loaded"
FBReader must be logged into your Book Network account. Open FBReader and ensure you can see your synced library.

### Books not appearing
Some books may be stored only on Google Drive. Make sure FBReader has downloaded them locally.

### ePub not loading
Only ePub format is currently supported for in-browser reading. FB2 support is planned.

## Running as a Service (Windows)

To run automatically on startup, create a Windows Task:

1. Open Task Scheduler
2. Create a new task
3. Trigger: "At startup"
4. Action: Start a program
   - Program: `python` (or full path to python.exe)
   - Arguments: `app.py`
   - Start in: `C:\path\to\fbreader_web`

## License

This project is for personal use with your own FBReader library.

---

Made with ❤️ for reading anywhere
