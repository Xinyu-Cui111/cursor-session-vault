@echo off
REM User-hook entry: locate Python and run save-session.py. Always exit 0 for the agent.
REM Install: copy this file + save-session.py into %USERPROFILE%\.cursor\hooks\
setlocal EnableExtensions
cd /d "%~dp0\.."

REM >>> Edit this path to your local vault clone <<<
set "VAULT=C:\path\to\cursor-session-vault"
if defined CURSOR_SESSION_VAULT set "VAULT=%CURSOR_SESSION_VAULT%"
set "HEALTH_DIR=%VAULT%\sessions"
if not exist "%HEALTH_DIR%" mkdir "%HEALTH_DIR%"

where python >nul 2>&1
if %ERRORLEVEL%==0 (
  python "%~dp0save-session.py"
  exit /b 0
)

where py >nul 2>&1
if %ERRORLEVEL%==0 (
  py -3 "%~dp0save-session.py"
  exit /b 0
)

powershell -NoProfile -Command ^
  "$d=Get-Date -Format 'yyyy-MM-dd HH:mm:ss'; $j=@{ok=$false;status='python_not_found';checked_at=$d;message='PATH ???? python/py???? Python 3 ??? Add to PATH?'} | ConvertTo-Json; Set-Content -Encoding utf8 '%HEALTH_DIR%\_health.json' $j; @('# Session Vault ???????','','- ??: **??? Python**','- ??: '+$d,'- ??: ?? Python 3 ??? PATH????? check-health.cmd') | Set-Content -Encoding utf8 '%HEALTH_DIR%\_health.md'"

echo {}
exit /b 0
