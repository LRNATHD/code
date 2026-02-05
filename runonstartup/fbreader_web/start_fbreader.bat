@echo off
:: FBReader Web Startup Script
:: This script starts both the Flask app and Cloudflare tunnel

:: Start Flask app in the background
start "FBReader Flask" /min cmd /c "cd /d C:\Users\LRNA\Desktop\code\runonstartup\fbreader_web && py app.py"

:: Give Flask a moment to start
timeout /t 3 /nobreak >nul

:: Start Cloudflare tunnel
start "FBReader Tunnel" /min cmd /c "cloudflared tunnel run fbreader"

echo FBReader Web started!
echo - Flask app running on http://localhost:5555
echo - Tunnel available at https://reading.noahsmith.dev
