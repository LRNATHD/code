Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "c:\Users\LRNA\Desktop\code\runonstartup\parts_inventory"
WshShell.Run "python server.py", 0
Set WshShell = Nothing
