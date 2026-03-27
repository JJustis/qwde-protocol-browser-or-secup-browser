@echo off
REM ═══════════════════════════════════════════════════════════
REM QWDE Protocol - Complete Build Script
REM Builds ALL components including Config Wizard with guide
REM ═══════════════════════════════════════════════════════════

setlocal enabledelayedexpansion

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║     QWDE Protocol v3.0 - Complete Build System            ║
echo ╠═══════════════════════════════════════════════════════════╣
echo ║  Building:                                                ║
echo ║    1. QWDE_Browser.exe (Main browser)                    ║
echo ║    2. QWDE_Central_Server.exe (Python DDNS)              ║
echo ║    3. QWDE_Config_Wizard.exe (With self-host guide)      ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)

echo [1/8] Installing dependencies...
pip install pyinstaller cryptography requests certifi mysql-connector-python pillow --quiet --disable-pip-version-check
echo [✓] Dependencies installed

echo.
echo [2/8] Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "output" rmdir /s /q "output"
echo [✓] Cleaned

echo.
echo [3/8] Building QWDE_Browser.exe...
python -m PyInstaller --clean ^
    --name QWDE_Browser ^
    --windowed ^
    --onefile ^
    --add-data "qwde_config.ini;." ^
    --add-data "plugins;plugins" ^
    --hidden-import=tkinter ^
    --hidden-import=cryptography ^
    --hidden-import=requests ^
    --hidden-import=PIL ^
    qwde_browser.py

if exist "dist\QWDE_Browser.exe" (
    mkdir "output\QWDE_Browser"
    move /Y "dist\QWDE_Browser.exe" "output\QWDE_Browser\"
    copy /Y "qwde_config.ini" "output\QWDE_Browser\"
    if exist "plugins" xcopy /E /I /Y "plugins" "output\QWDE_Browser\plugins"
    echo [✓] QWDE_Browser.exe built successfully
) else (
    echo [✗] Browser build failed!
    pause
    exit /b 1
)

echo.
echo [4/8] Building QWDE_Central_Server.exe...
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
    copy /Y "peer_directory_api.php" "output\QWDE_Central_Server\"
    echo [✓] QWDE_Central_Server.exe built successfully
) else (
    echo [✗] Central Server build failed!
)

echo.
echo [5/8] Building QWDE_Config_Wizard.exe...
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
    echo [✓] QWDE_Config_Wizard.exe built successfully (with Self-Host Guide)
) else (
    echo [✗] Config Wizard build failed!
)

echo.
echo [6/8] Copying mirror server and documentation...

mkdir "output\QWDE_Mirror_Server" 2>nul
copy /Y "qwde_mirror_server.py" "output\QWDE_Mirror_Server\" >nul

mkdir "output\Documentation" 2>nul
copy /Y "README.md" "output\Documentation\" >nul
copy /Y "STARTUP_GUIDE.md" "output\Documentation\" >nul
copy /Y "WEBSITE_CREATION_GUIDE.md" "output\Documentation\" >nul
copy /Y "SECURE_HTML_VIEWER.md" "output\Documentation\" >nul
copy /Y "SYSTEM_DIAGRAM.md" "output\Documentation\" >nul
copy /Y "DELETION_SYSTEM.md" "output\Documentation\" >nul

echo [✓] Files copied

echo.
echo [7/8] Creating launcher scripts and switch folder...

REM Create switch folder for PHP website files
mkdir "switch" 2>nul
copy /Y "website_template\peer_directory_api.php" "switch\" >nul
copy /Y "website_template\api_handler.php" "switch\" >nul
copy /Y "setup_central_database.sql" "switch\" >nul
copy /Y "qwde_config.ini" "switch\" >nul
copy /Y "website_template\index.html" "switch\" >nul
if exist "website_template\css" xcopy /E /I /Y "website_template\css" "switch\css" >nul
if exist "website_template\js" xcopy /E /I /Y "website_template\js" "switch\js" >nul
echo [✓] Switch folder created (PHP website files for secupgrade.com/switch)

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
echo echo.
echo echo ╔═══════════════════════════════════════════════════════════╗
echo echo ║  QWDE Configuration Wizard                                ║
echo echo ╠═══════════════════════════════════════════════════════════╣
echo echo ║  Configure:                                               ║
echo echo ║    • Central Server (secupgrade.com/switch or self-host) ║
echo echo ║    • Database Connection                                  ║
echo echo ║    • Browser Settings                                     ║
echo echo ║    • Mirror Server                                        ║
echo echo ║    • Security Settings                                    ║
echo echo ║                                                           ║
echo echo ║  Includes Self-Hosting Guide!                            ║
echo echo ╚═══════════════════════════════════════════════════════════╝
echo echo.
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
echo echo ║     QWDE Protocol v3.0 - Quick Start                      ║
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

echo.
echo [8/8] Creating release zip (includes ALL files + switch/ folder)...

REM Wait a moment for all files to be written
timeout /t 2 /nobreak >nul

REM Create comprehensive zip with all source files
powershell -Command "$files = @(); Get-ChildItem -Path '.' -Include '*.py','*.php','*.sql','*.bat','*.cmd','*.ini','*.md','*.txt','*.html','*.css','*.js' -Recurse -Exclude 'build','dist','output','old','__pycache__','*.pyc' | ForEach-Object { $files += $_.FullName }; Get-ChildItem -Path 'switch','plugins','website_template' -Recurse -ErrorAction SilentlyContinue | ForEach-Object { $files += $_.FullName }; Get-ChildItem -Path 'output' -Recurse -ErrorAction SilentlyContinue | ForEach-Object { $files += $_.FullName }; Compress-Archive -Path $files -DestinationPath 'QWDE_Protocol_v3.0_Source.zip' -Force" 2>nul

if exist "QWDE_Protocol_v3.0_Source.zip" (
    echo [✓] Release zip created: QWDE_Protocol_v3.0_Source.zip
    echo [✓] Includes:
    echo      - All Python source files (*.py)
    echo      - All PHP files (switch/ folder)
    echo      - All SQL files
    echo      - All batch scripts
    echo      - All documentation (*.md)
    echo      - All configuration files (*.ini)
    echo      - Compiled EXEs (output/ folder)
    echo      - Plugins folder
    echo      - Website template folder
) else (
    echo [!] Could not create release zip
    echo [!] Creating manually...
    
    REM Fallback: Simple zip command
    powershell -Command "Compress-Archive -Path '*.py','*.php','*.sql','*.bat','*.ini','*.md','switch','plugins','website_template','output' -DestinationPath 'QWDE_Protocol_v3.0_Source.zip' -Force" 2>nul
    
    if exist "QWDE_Protocol_v3.0_Source.zip" (
        echo [✓] Release zip created (fallback method)
    ) else (
        echo [✗] Failed to create release zip
    )
)

REM Cleanup
rmdir /s /q "build" 2>nul

echo.
echo ═══════════════════════════════════════════════════════════
echo BUILD COMPLETE - Next Steps:
echo ═══════════════════════════════════════════════════════════
echo.
echo 1. Deploy PHP files to web server:
echo    - Run QWDE_Config_Wizard.exe
echo    - Step 7: Deployment Path
echo    - Select deployment location and click Deploy
echo.
echo    OR manually upload switch/ folder to:
echo    secupgrade.com/switch/
echo.
echo 2. Setup MySQL database:
echo    - Import: switch/setup_central_database.sql
echo.
echo 3. Configure mirror server:
echo    - Edit: qwde_config.ini
echo    - Set: [central_server] → host = secupgrade.com
echo    - Set: [central_server] → api_path = /switch
echo.
echo 4. Run components:
echo    - Browser: output\QWDE_Browser\QWDE_Browser.exe
echo    - Mirror: output\QWDE_Mirror_Server\qwde_mirror_server.py
echo    - Wizard: output\QWDE_Config_Wizard\QWDE_Config_Wizard.exe
echo.
echo ═══════════════════════════════════════════════════════════
echo.

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║           BUILD COMPLETE!                                 ║
echo ╠═══════════════════════════════════════════════════════════╣
echo ║  Output: output\                                          ║
echo ║                                                           ║
echo ║  QWDE_Browser\                                            ║
echo ║    └─ QWDE_Browser.exe          [Main Browser]           ║
echo ║       • Secure HTML viewer (source-first)                ║
echo ║       • Plugin system                                    ║
echo ║       • Site creator                                     ║
echo ║       • Ownership tokens                                 ║
echo ║                                                           ║
echo ║  QWDE_Central_Server\                                     ║
echo ║    └─ QWDE_Central_Server.exe   [Python DDNS Server]     ║
echo ║       • Peer directory                                   ║
echo ║       • Site metadata                                    ║
echo ║       • Cache invalidation                               ║
echo ║                                                           ║
echo ║  QWDE_Config_Wizard\                                      ║
echo ║    └─ QWDE_Config_Wizard.exe    [Config Wizard]          ║
echo ║       • 8-step configuration                             ║
echo ║       • Self-hosting guide                               ║
echo ║       • phpMyAdmin integration                           ║
echo ║       • Test connections                                 ║
echo ║                                                           ║
echo ║  QWDE_Mirror_Server\                                      ║
echo ║    └─ qwde_mirror_server.py     [Mirror Server Script]   ║
echo ║       • Downloads all sites                              ║
echo ║       • Auto-purges deleted                              ║
echo ║                                                           ║
echo ║  Quick Start: start.bat                                   ║
echo ║  Release Zip: QWDE_Protocol_v3.0_Build.zip               ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

pause
