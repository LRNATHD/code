Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "c:\Users\LRNA\Desktop\code\runonstartup\service_manager"

' Load user environment variable
Set WshEnv = WshShell.Environment("USER")
password = WshEnv("STARTUP_APPS_PASSWORD")
Set procEnv = WshShell.Environment("PROCESS")
procEnv("STARTUP_APPS_PASSWORD") = password

' Start Flask app hidden
WshShell.Run "cmd /c py app.py", 0

Set WshShell = Nothing
