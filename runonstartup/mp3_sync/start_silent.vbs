Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "c:\Users\LRNA\Desktop\code\runonstartup\mp3_sync"
Set WshEnv = WshShell.Environment("USER")
password = WshEnv("STARTUP_APPS_PASSWORD")
Set procEnv = WshShell.Environment("PROCESS")
procEnv("STARTUP_APPS_PASSWORD") = password
WshShell.Run "cmd /c py app.py", 0
Set WshShell = Nothing
