Set WshShell = CreateObject("WScript.Shell")

' 0 = Hide window
' False = Do not wait for the process to complete
WshShell.Run "pythonw.exe ""d:\Users\me\Documents\projects\random-stuff\sff_case_9L_01\telemetry_display\telemetry_stream.py""", 0, False
Set WshShell = Nothing