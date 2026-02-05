Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "c:\Users\LRNA\Desktop\code\runonstartup\fbreader_web"

' Start Flask app hidden
WshShell.Run "cmd /c py app.py", 0

' Wait 3 seconds
WScript.Sleep 3000

' Start Cloudflare Tunnel hidden
WshShell.Run "cmd /c cloudflared tunnel run fbreader", 0

Set WshShell = Nothing
