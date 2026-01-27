@echo off
set "TARGET=%1"
set "RETRIES=0"
set "MAX_RETRIES=1"
set "MINICHLINK=..\..\tools\minichlink.exe"

:LOOP
echo Attempting to flash %TARGET% using minichlink... (Attempt %RETRIES% of %MAX_RETRIES%)

"%MINICHLINK%" -w "%TARGET%" flash -b
if %ERRORLEVEL% equ 0 goto SUCCESS

set /a RETRIES+=1
if %RETRIES% geq %MAX_RETRIES% goto FAIL

echo Flash failed. Retrying in 1 second...
timeout /t 1 >nul
goto LOOP

:SUCCESS
echo Flash Successful!
exit /b 0


:FAIL
echo Flash failed after %MAX_RETRIES% attempts.

set "WCHTOOL=c:\MounRiver\MounRiver_Studio2\resources\app\resources\win32\components\WCH\Others\WCHISPTool\default\WCHISPTool_CH57x-59x\WCHISPTool_CH57x-59x.exe"

if exist "isp_config.ini" (
    echo Found isp_config.ini, attempting to flash using WCHISPTool CLI...
    "%WCHTOOL%" -c "isp_config.ini" -o download -f "%TARGET%"
    if %ERRORLEVEL% equ 0 goto SUCCESS
    echo CLI Flash failed.
)

echo Note: minichlink requires the WinUSB driver to work in CLI mode.
echo Launching WCHISPTool GUI for manual flashing...
echo (Tip: In the GUI, configure your settings and click 'Save UI Config' to save an 'isp_config.ini' in this folder for auto-flashing next time!)
start "" "%WCHTOOL%"
exit /b 1
