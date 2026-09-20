@echo off
setlocal
set "WSL_DISTRO=Ubuntu-24.04"
set "DEMO_DIR=/mnt/d/comma_ai/openpilot-release-mici"

echo Starting protected openpilot hackathon demo...
wsl.exe -d %WSL_DISTRO% -- bash -lc "cd %DEMO_DIR% && source .venv/bin/activate && python tools/hackathon_demo.py"

set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
  echo.
  echo Demo exited with code %EXIT_CODE%.
  pause
)
exit /b %EXIT_CODE%
