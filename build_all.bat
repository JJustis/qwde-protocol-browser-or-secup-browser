@echo off
REM QWDE Protocol - Simple Build Script
REM Builds only the essential EXEs:
REM 1. QWDE_Browser.exe (Main browser with encryption)
REM 2. QWDE_PyServerDB.exe (Optional local MySQL server)

setlocal enabledelayedexpansion

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║        QWDE Protocol - Build System                       ║
echo ╠═══════════════════════════════════════════════════════════╣
echo ║  Building:                                                ║
echo ║    1. QWDE_Browser.exe (Main browser)                    ║
echo ║    2. QWDE_PyServerDB.exe (Optional MySQL server)        ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)

echo [1/6] Installing dependencies...
pip install pyinstaller cryptography requests certifi mysql-connector-python --quiet --disable-pip-version-check
echo [✓] Dependencies installed

echo.
echo [2/6] Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "output" rmdir /s /q "output"
echo [✓] Cleaned

echo.
echo [3/6] Building QWDE_Browser.exe...
echo      (This includes the full encryption system)

python -m PyInstaller --clean ^
    --name QWDE_Browser ^
    --windowed ^
    --onefile ^
    --add-data "qwde_config.ini;." ^
    --add-data "plugins;plugins" ^
    --hidden-import=tkinter ^
    --hidden-import=cryptography ^
    --hidden-import=requests ^
    --icon=NONE ^
    --path=. ^
    qwde_browser.py

if exist "dist\QWDE_Browser.exe" (
    mkdir "output\QWDE_Browser"
    move /Y "dist\QWDE_Browser.exe" "output\QWDE_Browser\"
    copy /Y "qwde_config.ini" "output\QWDE_Browser\"
    if exist "plugins" (
        xcopy /E /I /Y "plugins" "output\QWDE_Browser\plugins"
    )
    echo [✓] QWDE_Browser.exe built successfully
) else (
    echo [✗] Browser build failed!
)

echo.
echo [4/6] Building QWDE_PyServerDB.exe...
echo      (OPTIONAL - Only for hosting your own MySQL server)

python -m PyInstaller --clean ^
    --name QWDE_PyServerDB ^
    --console ^
    --onefile ^
    --add-data "setup_mysql_php.sql;." ^
    --add-data "qwde_config.ini;." ^
    --hidden-import=mysql.connector ^
    --icon=NONE ^
    --path=. ^
    qwde_mysql_ddns.py

if exist "dist\QWDE_PyServerDB.exe" (
    mkdir "output\QWDE_PyServerDB"
    move /Y "dist\QWDE_PyServerDB.exe" "output\QWDE_PyServerDB\"
    copy /Y "setup_mysql_php.sql" "output\QWDE_PyServerDB\"
    copy /Y "qwde_config.ini" "output\QWDE_PyServerDB\"
    echo [✓] QWDE_PyServerDB.exe built successfully
) else (
    echo [✗] PyServerDB build failed!
)

echo.
echo [5/6] Creating launcher scripts...

REM Browser launcher
(
echo @echo off
echo cd /d "%%~dp0"
echo echo.
echo echo ╔═══════════════════════════════════════════════════════════╗
echo echo ║         QWDE Browser - Starting...                        ║
echo echo ╚═══════════════════════════════════════════════════════════╝
echo echo.
echo echo Connecting to: https://secupgrade.com
echo echo.
echo start QWDE_Browser.exe
) > "output\QWDE_Browser\Start.bat"

REM PyServerDB launcher
(
echo @echo off
echo cd /d "%%~dp0"
echo echo.
echo echo ╔═══════════════════════════════════════════════════════════╗
echo echo ║    QWDE PyServerDB - Local MySQL Server                   ║
echo echo ╠═══════════════════════════════════════════════════════════╣
echo echo ║  OPTIONAL - Only if hosting your own central server      ║
echo echo ║  NOT NEEDED if using secupgrade.com                      ║
echo echo ╚═══════════════════════════════════════════════════════════╝
echo echo.
echo echo Starting MySQL server on port 8765...
echo echo Press Ctrl+C to stop
echo echo.
echo QWDE_PyServerDB.exe --server
) > "output\QWDE_PyServerDB\Start.bat"

echo [✓] Launcher scripts created

echo.
echo [6/6] Copying documentation...

mkdir "output\Documentation" 2>nul
copy /Y "README.md" "output\Documentation\" >nul
copy /Y "DEPLOYMENT.md" "output\Documentation\" >nul 2>nul
copy /Y "server_config.ini" "output\Documentation\" >nul 2>nul
echo [✓] Documentation copied

REM Cleanup
echo.
echo Cleaning up...
rmdir /s /q "build" 2>nul
rmdir /s /q "dist" 2>nul

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║              BUILD COMPLETE!                              ║
echo ╠═══════════════════════════════════════════════════════════╣
echo ║  Output folder: output\                                   ║
echo ║                                                           ║
echo ║  QWDE_Browser\                                            ║
echo ║    └─ QWDE_Browser.exe      [MAIN APPLICATION]           ║
echo ║       - Full browser GUI                                  ║
echo ║       - Site Creator                                      ║
echo ║       - Plugin System                                     ║
echo ║       - QWDE Encryption (RSA+AES+Rolling)                ║
echo ║       - Network Health Map                                ║
echo ║       - Connects to: https://secupgrade.com              ║
echo ║                                                           ║
echo ║  QWDE_PyServerDB\                                         ║
echo ║    └─ QWDE_PyServerDB.exe   [OPTIONAL]                   ║
echo ║       - Local MySQL server                                ║
echo ║       - ONLY needed if hosting own central server         ║
echo ║       - NOT needed if using secupgrade.com                ║
echo ║                                                           ║
echo ║  Quick Start:                                             ║
echo ║    1. Go to output\QWDE_Browser\                          ║
echo ║    2. Run Start.bat or QWDE_Browser.exe                   ║
echo ║    3. Click "Create Site" to make websites                ║
echo ║    4. Publish to secupgrade.com                           ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM Show built files
echo Built files:
echo.
dir /s /b output\*.exe 2>nul
echo.

pause
