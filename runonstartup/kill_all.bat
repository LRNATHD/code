@echo off
:: Kill All Startup Apps
:: Stops all Python Flask apps and Cloudflare tunnel

echo Stopping all startup apps...

:: Kill all Python processes (Flask apps)
taskkill /F /IM python.exe 2>nul
taskkill /F /IM UnifiedRunningService.exe 2>nul
if %errorlevel%==0 (
    echo [OK] Killed Python processes
) else (
    echo [--] No Python processes found
)

:: Kill Cloudflare tunnel
taskkill /F /IM cloudflared.exe 2>nul
if %errorlevel%==0 (
    echo [OK] Killed Cloudflare tunnel
) else (
    echo [--] No Cloudflare tunnel found
)

echo.
echo All startup apps stopped.
pause
