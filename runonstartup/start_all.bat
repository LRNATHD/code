@echo off
:: Master Startup Script for all background services
:: This script starts all run-on-startup applications silently

echo Starting background services...

:: Start Parts Inventory (Hidden)
start "" "C:\Users\LRNA\Desktop\code\runonstartup\parts_inventory\start_silent.vbs"

:: Small delay
timeout /t 2 /nobreak >nul

:: Start FBReader Web (Hidden)
start "" "C:\Users\LRNA\Desktop\code\runonstartup\fbreader_web\start_silent.vbs"

:: The terminal window running THIS script will close automatically
exit
