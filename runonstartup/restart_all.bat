@echo off
:: Restart All Startup Apps
:: Kills all apps then starts them fresh

echo ========================================
echo   Restarting All Startup Apps
echo ========================================
echo.

:: First, kill everything
echo [1/2] Stopping all apps...

taskkill /F /IM python.exe 2>nul
taskkill /F /IM cloudflared.exe 2>nul

echo      All processes stopped.
echo.

:: Wait a moment
timeout /t 2 /nobreak >nul

:: Start all apps
echo [2/2] Starting all apps...
call "%~dp0start_all.bat"
