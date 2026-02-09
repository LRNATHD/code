Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "c:\Users\LRNA\Desktop\code\runonstartup\google_tasks"

' Read the password from User environment variable and set it for this process
Set WshEnv = WshShell.Environment("USER")
password = WshEnv("STARTUP_APPS_PASSWORD")

' Set it as a process environment variable before starting Flask
Set procEnv = WshShell.Environment("PROCESS")
procEnv("STARTUP_APPS_PASSWORD") = password

' Start Flask app hidden
WshShell.Run "cmd /c py app.py > startup_log.txt 2>&1", 0

' Note: The Cloudflare tunnel is shared with fbreader and started there

Set WshShell = Nothing
