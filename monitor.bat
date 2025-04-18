@echo off
where py >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Python not found.
    echo [INFO] Installing Python 3.12 via winget...
    winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
    goto :INSTALL_PACKAGES
)

python -c "import sys; exit(0 if sys.version_info >= (3,10) else 1)"
if %ERRORLEVEL%==0 (
    echo [INFO] Python 3.10 or higher is already installed.
) else (
    echo [INFO] Python 3.10 or higher is not installed.
    echo [INFO] Installing Python 3.12 via winget...
    winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
)

:INSTALL_PACKAGES
echo [INFO] Installing required Python packages...
py.exe -m pip install bleak pyperclip pynput pygetwindow psutil requests

echo [INFO] Running checker.py...
REM [MODIFY_HERE]

echo [INFO] Done.
exit /b
