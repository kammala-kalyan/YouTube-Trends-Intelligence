@echo off
REM Used by Windows Task Scheduler. Logs to logs\run_YYYY-MM-DD.log
cd /d "%~dp0"
if not exist logs mkdir logs
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set D=%%i
"%~dp0venv\Scripts\python.exe" -X utf8 run_daily.py >> "logs\run_%D%.log" 2>&1
