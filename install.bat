@echo off
:: ─────────────────────────────────────────
:: On vérifie si le script tourne en admin
:: Si non, on se relance en admin
:: ─────────────────────────────────────────
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Restarting script with administrative privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit
)

echo === ESSEC WiFi Installer ===
echo.

:: ─────────────────────────────────────────
:: On vérifie si Python est installé
:: ─────────────────────────────────────────
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Python is not installed. Installing Python...  
    echo Downloading Python installer...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe' -OutFile '%TEMP%\python_installer.exe'"
    %TEMP%\python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del %TEMP%\python_installer.exe
    echo Python installed successfully.
) else (
    echo Python is already installed.
)

:: ─────────────────────────────────────────
:: Installation des dépendances Python
:: ─────────────────────────────────────────
echo Downloading and installing dependencies...
python -m pip install --quiet selenium python-dotenv
echo Dependencies installed successfully.

:: ─────────────────────────────────────────
:: Lancement du setup Python
:: ─────────────────────────────────────────
echo Starting Python setup...
python "%~dp0setup.py"

echo.
echo Done! Press any key to exit.
pause
