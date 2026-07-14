@echo off
cd /d "%~dp0"
echo Starting Vue Quiz Game from:
echo %CD%
echo.
python server.py --host 0.0.0.0 --port 5000 --questions questions.json
pause
