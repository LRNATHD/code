@echo off
:: Google Tasks Custom Startup Script
:: This script starts the Flask app (tunnel is shared with fbreader)

:: Start Flask app in the background
start "Google Tasks Flask" /min cmd /c "cd /d C:\Users\LRNA\Desktop\code\runonstartup\google_tasks && py app.py"

echo Google Tasks Custom started!
echo - Flask app running on http://localhost:5556
echo - Tunnel available at https://tasks.noahsmith.dev (shared tunnel with fbreader)
