# AI Screenshot Search

A global screenshot tool that sends captured areas to AI for explanation.

## Features
- **Global Hotkey:** Press `Ctrl+Alt+S` anywhere to activate.
- **VS Code Themed:** Dark mode UI that matches your coding environment.
- **AI Integration:** Sends screenshots + questions to Google Gemini (or mocks it if no key is present).

## Setup

1.  **Install Dependencies:**
    ```powershell
    python -m venv venv
    .\venv\Scripts\pip install -r requirements.txt
    ```

2.  **API Key (Optional):**
    To use real AI, set your Gemini API key:
    ```powershell
    $env:GEMINI_API_KEY="your_key_here"
    ```
    Or add it to your system environment variables.

## Running
Run the script and keep it open in the background:
```powershell
.\venv\Scripts\python main.py
```

## Usage
1.  Run the app.
2.  Press `Ctrl+Alt+S`.
3.  Drag to select an area of your screen.
4.  Type a question (optional) and hit Enter.
