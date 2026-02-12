@echo off
echo Attempting to launch FBReader UWP...
start shell:AppsFolder\FBReader_n0j83cvmz1mee!App
timeout /t 5
tasklist /FI "IMAGENAME eq FBReader.exe"
