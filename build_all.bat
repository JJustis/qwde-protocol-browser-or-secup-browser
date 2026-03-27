@echo off
REM ═══════════════════════════════════════════════════════════
REM QWDE Protocol - Complete Build Script
REM Builds ALL components including Python central server
REM ═══════════════════════════════════════════════════════════

setlocal enabledelayedexpansion

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║     QWDE Protocol - Complete Build System                 ║
echo ╠═══════════════════════════════════════════════════════════╣
echo ║  Building:                                                ║
echo ║    1. QWDE_Browser.exe (Main browser)                    ║
echo ║    2. QWDE_Central_Server.exe (Python DDNS)              ║
echo ║    3. QWDE_Config_Wizard.exe (Config wizard)             ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)

echo [1/7] Installing dependencies...
pip install pyinstaller cryptography requests certifi mysql-connector-python --quiet --disable-pip-version-check
echo [✓] Dependencies installed

echo.
echo [2/7] Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "output" rmdir /s /q "output"
echo [✓] Cleaned

echo.
echo [3/7] Building QWDE_Browser.exe...
python -m PyInstaller --clean ^
    --name QWDE_Browser ^
    --windowed ^
    --onefile ^
    --add-data "qwde_config.ini;." ^
    --add-data "plugins;plugins" ^
    --hidden-import=tkinter ^
    --hidden-import=cryptography ^
    --hidden-import=requests ^
    qwde_browser.py

if exist "dist\QWDE_Browser.exe" (
    mkdir "output\QWDE_Browser"
    move /Y "dist\QWDE_Browser.exe" "output\QWDE_Browser\"
    copy /Y "qwde_config.ini" "output\QWDE_Browser\"
    if exist "plugins" xcopy /E /I /Y "plugins" "output\QWDE_Browser\plugins"
    echo [✓] QWDE_Browser.exe built
) else (
    echo [✗] Browser build failed!
)

echo.
echo [4/7] Building QWDE_Central_Server.exe...
python -m PyInstaller --clean ^
    --name QWDE_Central_Server ^
    --console ^
    --onefile ^
    --add-data "qwde_config.ini;." ^
    --add-data "setup_central_database.sql;." ^
    --hidden-import=mysql.connector ^
    qwde_mysql_ddns.py

if exist "dist\QWDE_Central_Server.exe" (
    mkdir "output\QWDE_Central_Server"
    move /Y "dist\QWDE_Central_Server.exe" "output\QWDE_Central_Server\"
    copy /Y "setup_central_database.sql" "output\QWDE_Central_Server\"
    echo [✓] QWDE_Central_Server.exe built
) else (
    echo [✗] Central Server build failed!
)

echo.
echo [5/7] Building QWDE_Config_Wizard.exe...
python -m PyInstaller --clean ^
    --name QWDE_Config_Wizard ^
    --windowed ^
    --onefile ^
    --hidden-import=tkinter ^
    --hidden-import=mysql.connector ^
    qwde_config_wizard.py

if exist "dist\QWDE_Config_Wizard.exe" (
    mkdir "output\QWDE_Config_Wizard"
    move /Y "dist\QWDE_Config_Wizard.exe" "output\QWDE_Config_Wizard\"
    echo [✓] QWDE_Config_Wizard.exe built
) else (
    echo [✗] Config Wizard build failed!
)

echo.
echo [6/7] Copying scripts and documentation...

mkdir "output\QWDE_Mirror_Server" 2>nul
copy /Y "qwde_mirror_server.py" "output\QWDE_Mirror_Server\" >nul
copy /Y "peer_directory_api.php" "output\QWDE_Central_Server\" >nul

mkdir "output\Documentation" 2>nul
copy /Y "README.md" "output\Documentation\" >nul
copy /Y "STARTUP_GUIDE.md" "output\Documentation\" >nul
copy /Y "WEBSITE_CREATION_GUIDE.md" "output\Documentation\" >nul
copy /Y "SECURE_HTML_VIEWER.md" "output\Documentation\" >nul

echo [✓] Files copied

echo.
echo [7/7] Creating launcher scripts...

REM Browser launcher
(
echo @echo off
echo cd /d "%%~dp0"
echo start QWDE_Browser.exe
) > "output\QWDE_Browser\Start.bat"

REM Central Server launcher
(
echo @echo off
echo cd /d "%%~dp0"
echo echo.
echo echo ╔═══════════════════════════════════════════════════════════╗
echo echo ║  QWDE Central DDNS Server - Python Backend               ║
echo echo ╠═══════════════════════════════════════════════════════════╣
echo echo ║  Stores: Peer IPs, Site Metadata, Ownership Tokens       ║
echo echo ║  NOT stored: Site content (stored on peer computers)     ║
echo echo ╚═══════════════════════════════════════════════════════════╝
echo echo.
echo echo Starting central server on port 8765...
echo echo Press Ctrl+C to stop
echo echo.
echo QWDE_Central_Server.exe --server
) > "output\QWDE_Central_Server\Start.bat"

REM Config Wizard launcher
(
echo @echo off
echo cd /d "%%~dp0"
echo start QWDE_Config_Wizard.exe
) > "output\QWDE_Config_Wizard\Start.bat"

REM Mirror Server launcher
(
echo @echo off
echo cd /d "%%~dp0"
echo echo.
echo echo ╔═══════════════════════════════════════════════════════════╗
echo echo ║  QWDE Mirror Server - Full Site Backup                    ║
echo echo ╠═══════════════════════════════════════════════════════════╣
echo echo ║  Downloads ALL sites from ALL peers                      ║
echo echo ║  Auto-updates every 60 seconds                           ║
echo echo ║  Purges deleted sites from cache                         ║
echo echo ╚═══════════════════════════════════════════════════════════╝
echo echo.
echo python qwde_mirror_server.py
) > "output\QWDE_Mirror_Server\Start.bat"

REM Master launcher
(
echo @echo off
echo echo.
echo echo ╔═══════════════════════════════════════════════════════════╗
echo echo ║     QWDE Protocol - Quick Start                           ║
echo echo ╚═══════════════════════════════════════════════════════════╝
echo echo.
echo echo Select an option:
echo echo.
echo echo 1. Start Browser
echo echo 2. Start Central Server
echo echo 3. Start Mirror Server
echo echo 4. Open Config Wizard
echo echo 5. Exit
echo echo.
echo set /p choice="Enter choice (1-5): "
echo.
echo if "%%choice%%"=="1" start QWDE_Browser\QWDE_Browser.exe
echo if "%%choice%%"=="2" start cmd /k "cd QWDE_Central_Server ^&^& QWDE_Central_Server.exe --server"
echo if "%%choice%%"=="3" start cmd /k "cd QWDE_Mirror_Server ^&^& python qwde_mirror_server.py"
echo if "%%choice%%"=="4" start QWDE_Config_Wizard\QWDE_Config_Wizard.exe
echo if "%%choice%%"=="5" exit /b
) > "start.bat"

echo [✓] Launcher scripts created

REM Cleanup
rmdir /s /q "build" 2>nul

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║           BUILD COMPLETE!                                 ║
echo ╠═══════════════════════════════════════════════════════════╣
echo ║  Output: output\                                          ║
echo ║                                                           ║
echo ║  QWDE_Browser\                                            ║
echo ║    └─ QWDE_Browser.exe          [Main Browser]           ║
echo ║                                                           ║
echo ║  QWDE_Central_Server\                                     ║
echo ║    └─ QWDE_Central_Server.exe   [Python DDNS Server]     ║
echo ║                                                           ║
echo ║  QWDE_Config_Wizard\                                      ║
echo ║    └─ QWDE_Config_Wizard.exe    [Config Wizard]          ║
echo ║                                                           ║
echo ║  QWDE_Mirror_Server\                                      ║
echo ║    └─ qwde_mirror_server.py     [Mirror Server Script]   ║
echo ║                                                           ║
echo ║  Quick Start: start.bat                                   ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

pause
