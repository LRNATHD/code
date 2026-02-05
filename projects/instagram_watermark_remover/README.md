# Instagram Watermark Remover

A powerful tool to remove Instagram watermarks from your Google Photos using AI-powered inpainting (LaMa/IOPaint).

![Screenshot](docs/screenshot.png)

## Features

- 🔗 **Google Photos Integration** - Connect directly to your Google Photos library
- 🤖 **AI-Powered Removal** - Uses state-of-the-art LaMa inpainting model via IOPaint
- 📍 **Auto-Detection** - Automatically detects watermark position in corners
- 📦 **Batch Processing** - Process multiple images at once
- 💾 **Local Upload** - Also supports uploading local images
- 🎨 **Beautiful UI** - Modern glassmorphism dark theme interface

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Google account for Google Photos access
- (Optional) NVIDIA GPU with CUDA for faster processing

## Installation

### 1. Clone/Navigate to the project

```bash
cd instagram_watermark_remover
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

**For GPU acceleration (recommended):**

First install PyTorch with CUDA support:
```bash
# Visit https://pytorch.org/get-started/locally/ for your specific configuration
# Example for CUDA 11.8:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

Then install the rest:
```bash
pip install -r requirements.txt
```

### 4. Set up Google Photos API credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to **APIs & Services** > **Library**
4. Search for and enable **Google Photos Library API**
5. Go to **APIs & Services** > **OAuth consent screen**
   - Configure the consent screen (External or Internal)
   - Add your email as a test user
6. Go to **APIs & Services** > **Credentials**
7. Click **Create Credentials** > **OAuth client ID**
8. Select **Desktop app** as the application type
9. Download the JSON file
10. Rename it to `client_secret.json` and place it in the `credentials/` folder

### 5. Configure environment (optional)

Copy the example environment file:
```bash
copy .env.example .env
```

Edit `.env` to customize settings.

## Usage

### Start the application

```bash
python app.py
```

Open your browser to `http://localhost:5000`

### Workflow

1. **Connect to Google Photos** - Click "Sign in with Google" to authorize access
2. **Fetch Photos** - Select an album or fetch all photos
3. **Select Images** - Ctrl+Click to select multiple images for processing
4. **Choose Watermark Position** - Select where the watermark is located, or use "Auto" for detection
5. **Process** - Click "Remove Watermarks" to start batch processing
6. **View Results** - Switch to "Processed" tab to see the results

### Local Images

You can also drag & drop local images or click the upload zone to browse files.

## Project Structure

```
instagram_watermark_remover/
├── app.py                  # Flask web application
├── config.py               # Configuration settings
├── google_photos.py        # Google Photos API client
├── watermark_remover.py    # Watermark detection & removal engine
├── requirements.txt        # Python dependencies
├── .env.example            # Example environment configuration
├── credentials/            # Google API credentials (gitignored)
│   └── client_secret.json  # Your OAuth credentials
├── downloads/              # Downloaded photos from Google Photos
├── processed/              # Processed images with watermarks removed
├── temp/                   # Temporary processing files
├── static/
│   ├── css/
│   │   └── styles.css      # Application styles
│   └── js/
│       └── app.js          # Frontend JavaScript
└── templates/
    └── index.html          # Main HTML template
```

## How It Works

### Watermark Detection

The app looks for Instagram watermarks in the typical corner positions:
- Bottom-right (most common)
- Bottom-left
- Top-right
- Top-left

Auto-detection uses edge detection to identify text-like patterns in these regions.

### Watermark Removal

1. **IOPaint/LaMa Model** (Primary) - Uses the Large Mask Inpainting (LaMa) model for high-quality results
2. **OpenCV Telea** (Fallback) - If IOPaint fails, uses classic inpainting algorithms

## Troubleshooting

### "IOPaint not installed" warning

Run:
```bash
pip install iopaint
```

### GPU not detected

Ensure you have:
1. NVIDIA GPU with CUDA support
2. Correct CUDA version installed
3. PyTorch with CUDA support installed

Check GPU availability:
```python
import torch
print(torch.cuda.is_available())
```

### OAuth error

- Make sure `client_secret.json` is in the `credentials/` folder
- Verify your Google Cloud project has the Photos Library API enabled
- Check that your email is added as a test user in the OAuth consent screen

### Processing is slow

- Enable GPU acceleration (see installation instructions)
- Process fewer images at once
- The first run downloads the model, subsequent runs are faster

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Check app status |
| `/api/albums` | GET | List Google Photos albums |
| `/api/photos` | GET | List photos (supports `album_id` param) |
| `/api/download` | POST | Download selected photos |
| `/api/local-photos` | GET | List downloaded photos |
| `/api/processed-photos` | GET | List processed photos |
| `/api/upload` | POST | Upload local images |
| `/api/process` | POST | Start batch processing |
| `/api/process/status` | GET | Get processing progress |
| `/api/process/single` | POST | Process single image |

## License

MIT License - feel free to use and modify!

## Acknowledgments

- [IOPaint](https://github.com/Sanster/IOPaint) - AI-powered inpainting
- [LaMa](https://github.com/saic-mdal/lama) - Large Mask Inpainting model
- [Google Photos Library API](https://developers.google.com/photos)
