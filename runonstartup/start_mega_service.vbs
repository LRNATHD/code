Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Path to the runonstartup directory
currentDir = "c:\Users\LRNA\Desktop\code\runonstartup"
WshShell.CurrentDirectory = currentDir

' Explicitly load environment variables from USER scope (legacy support)
Set WshEnv = WshShell.Environment("USER")
On Error Resume Next
    password = WshEnv("STARTUP_APPS_PASSWORD")
    If password <> "" Then
        Set procEnv = WshShell.Environment("PROCESS")
        procEnv("STARTUP_APPS_PASSWORD") = password
    End If
On Error GoTo 0

' Define the target executable path (same as in launch_mega.py)
exePath = "C:\Users\LRNA\AppData\Local\Python\pythoncore-3.14-64\UnifiedRunningService.exe"
scriptPath = "unified_server.py"

' Check if the custom executable exists
If Not fso.FileExists(exePath) Then
    ' If not, run the setup script to create it
    ' This will open a window briefly
    WshShell.Run "python launch_mega.py", 1, True
End If

' Run the unified server silently (WindowStyle 0 = Hide)
' We use cmd /c to ensure it runs properly, or just the exe directly
WshShell.Run """" & exePath & """ " & scriptPath, 0

Set WshShell = Nothing
