@echo off
chcp 65001 >nul
cd /d "%~dp0"

where python >nul 2>&1
if %ERRORLEVEL%==0 (
  python "%~dp0check-health.py"
  set ERR=%ERRORLEVEL%
  goto :show
)

where py >nul 2>&1
if %ERRORLEVEL%==0 (
  py -3 "%~dp0check-health.py"
  set ERR=%ERRORLEVEL%
  goto :show
)

echo [FAIL] 找不到 python / py。请先安装 Python 3 并加入 PATH。
echo 详细说明见 README.md
set ERR=2

:show
echo.
echo 报告已写入 sessions\_health_check.md
echo 日常也可直接打开 sessions\_health.md 看上次钩子心跳。
echo.
pause
exit /b %ERR%
