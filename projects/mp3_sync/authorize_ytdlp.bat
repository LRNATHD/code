
@echo off
echo Starting YouTube Music Authentication for downloader...
echo You will be asked to open a URL and enter a code.
echo.
yt-dlp --username oauth --password "" https://music.youtube.com/watch?v=LO0BRuBFtp0 --download-archive tmp_auth_check
echo.
echo Authentication complete! You can strict restart the sync service now.
del tmp_auth_check
pause
