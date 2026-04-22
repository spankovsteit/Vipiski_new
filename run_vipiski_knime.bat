@echo off
setlocal EnableExtensions

REM Non-interactive launcher for KNIME External Tool node.
REM Usage:
REM   run_vipiski_knime.bat "input_file" "output_file"
REM Output file is always produced to unblock the node parser.

cd /d "%~dp0"
set "PYTHONUNBUFFERED=1"

set "IN_FILE=%~1"
set "OUT_FILE=%~2"
if "%OUT_FILE%"=="" set "OUT_FILE=%~dp0knime_output.csv"

REM KNIME run: avoid long waits on Telegram API retries.
if "%VIPISKI_SKIP_TELEGRAM%"=="" set "VIPISKI_SKIP_TELEGRAM=true"
if "%VIPISKI_TELEGRAM_SOFT_FAIL%"=="" set "VIPISKI_TELEGRAM_SOFT_FAIL=true"
REM main.py requires Telegram vars at settings load time even when skip is true.
if "%TELEGRAM_BOT_TOKEN%"=="" set "TELEGRAM_BOT_TOKEN=knime-skip-telegram"
if "%TELEGRAM_CHAT_ID%"=="" set "TELEGRAM_CHAT_ID=0"

if exist ".\.venv\Scripts\python.exe" (
  ".\.venv\Scripts\python.exe" -u main.py
) else (
  where py >nul 2>nul
  if %errorlevel%==0 (
    py -u main.py
  ) else (
    python -u main.py
  )
)

set "RC=%errorlevel%"

REM KNIME expects an output file from External Tool.
REM Write a tiny CSV payload regardless of main.py result.
(
  echo status;exit_code;input_file
  if %RC%==0 (
    echo OK;%RC%;"%IN_FILE%"
  ) else (
    echo ERROR;%RC%;"%IN_FILE%"
  )
) > "%OUT_FILE%"

echo Exit code: %RC%
echo Output file: %OUT_FILE%
endlocal & exit /b %RC%
