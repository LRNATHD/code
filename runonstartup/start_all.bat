@echo off
:: Master Startup Script for all background services
:: This script starts all run-on-startup applications silently

echo Starting background services...

:: Start Service Manager Dashboard (Hidden) - FIRST so it can manage others
start "" "C:\Users\LRNA\Desktop\code\runonstartup\service_manager\start_silent.vbs"

:: Small delay
timeout /t 2 /nobreak >nul

:: Start Parts Inventory (Hidden)
start "" "C:\Users\LRNA\Desktop\code\runonstartup\parts_inventory\start_silent.vbs"

:: Small delay
timeout /t 2 /nobreak >nul

:: Start FBReader Web (Hidden)
start "" "C:\Users\LRNA\Desktop\code\runonstartup\fbreader_web\start_silent.vbs"

:: Small delay
timeout /t 2 /nobreak >nul

:: Start Google Tasks Custom (Hidden)
start "" "C:\Users\LRNA\Desktop\code\runonstartup\google_tasks\start_silent.vbs"

:: Small delay
timeout /t 2 /nobreak >nul

:: Start MP3 Sync (Hidden)
start "" "C:\Users\LRNA\Desktop\code\runonstartup\mp3_sync\start_silent.vbs"

:: The terminal window running THIS script will close automatically
exit

