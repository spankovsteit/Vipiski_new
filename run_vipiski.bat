@echo off
setlocal EnableExtensions

REM Run Vipiski pipeline (main.py) from Windows.
REM Place this file next to main.py and double-click it.

cd /d "%~dp0"

REM Optional: activate local venv if present
if exist ".\.venv\Scripts\activate.bat" (
  call ".\.venv\Scripts\activate.bat"
)

REM Prefer py launcher when available, fall back to python
where py >nul 2>nul
if %errorlevel%==0 (
  py main.py
) else (
  python main.py
)

echo.
echo Exit code: %errorlevel%

endlocal
