' gedi-proxy-startup.vbs — Avvia gedi-proxy in background al login
' Nessuna finestra console visibile. Parte da shell:startup.
'
' Installazione:
'   Copiare (o creare shortcut) in:
'   %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\
'
' Stop manuale:
'   taskkill /F /FI "WINDOWTITLE eq gedi-proxy*"
'   oppure: netstat -ano | findstr 8765 → taskkill /PID <pid> /F

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\old\easyway\gedi-check"
WshShell.Run "python -m gedi_check.proxy --port 8765 --upstream https://api.anthropic.com", 0, False
