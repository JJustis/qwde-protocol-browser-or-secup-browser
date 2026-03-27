@echo off
REM ═══════════════════════════════════════════════════════════
REM QWDE Protocol - Run All Components
REM Starts database setup, mirror server, and browser
REM ═══════════════════════════════════════════════════════════

setlocal enabledelayedexpansion

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║        QWDE Protocol - Run All Components                 ║
echo ╠═══════════════════════════════════════════════════════════╣
echo ║  This script will:                                        ║
echo ║    1. Setup MySQL database (if needed)                   ║
echo ║    2. Start Mirror Server                                ║
echo ║    3. Start Browser Client                               ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM Check if output folder exists
if not exist "output" (
    echo [ERROR] Output folder not found!
    echo Please run build_all.bat first.
    pause
    exit /b 1
)

REM Check if browser exists
if not exist "output\QWDE_Browser\QWDE_Browser.exe" (
    echo [ERROR] QWDE_Browser.exe not found!
    echo Please run build_all.bat first.
    pause
    exit /b 1
)

echo [✓] Found output folder and browser

echo.

REM ═══════════════════════════════════════════════════════════
REM STEP 1: Database Setup
REM ═══════════════════════════════════════════════════════════
echo ═══════════════════════════════════════════════════════════
echo Step 1: Database Setup
echo ═══════════════════════════════════════════════════════════
echo.
echo Do you want to setup/recreate the MySQL database?
echo.
echo 1. Yes - Setup database (requires MySQL)
echo 2. No - Skip (using existing database)
echo 3. Test connection only
echo.
set /p db_choice="Enter choice (1-3): "

if "%db_choice%"=="1" (
    echo.
    echo Running database setup...
    echo.
    echo Enter MySQL root password when prompted:
    mysql -u root -p < setup_central_database.sql
    
    if errorlevel 1 (
        echo.
        echo [!] Database setup failed or MySQL not found
        echo [!] You can run setup later: mysql -u root -p < setup_central_database.sql
        echo.
        set /p continue_anyway="Continue anyway? (Y/N): "
        if /i not "!continue_anyway!"=="Y" exit /b 1
    ) else (
        echo [✓] Database setup complete!
    )
) else if "%db_choice%"=="3" (
    echo.
    echo Testing MySQL connection...
    mysql -u qwde_user -p -e "USE qwde_directory; SELECT 'Connection OK!' as status;"
    
    if errorlevel 1 (
        echo [!] MySQL connection failed
        echo [!] Make sure MySQL is running and database exists
    ) else (
        echo [✓] MySQL connection successful!
    )
) else (
    echo [✓] Skipping database setup
)

echo.

REM ═══════════════════════════════════════════════════════════
REM STEP 2: Start Mirror Server
REM ═══════════════════════════════════════════════════════════
echo ═══════════════════════════════════════════════════════════
echo Step 2: Mirror Server
echo ═══════════════════════════════════════════════════════════
echo.
echo Do you want to start the Mirror Server?
echo (Downloads ALL sites from ALL peers for backup)
echo.
echo 1. Yes - Start mirror server on port 8765
echo 2. No - Skip mirror server
echo.
set /p mirror_choice="Enter choice (1-2): "

if "%mirror_choice%"=="1" (
    echo.
    echo Starting Mirror Server...
    echo.
    echo [!] This will open a new command window
    echo [!] Press Ctrl+C in that window to stop the server
    echo.
    
    start "QWDE Mirror Server" cmd /k "cd output && python qwde_mirror_server.py"
    
    timeout /t 3 /nobreak >nul
    echo [✓] Mirror Server started in new window
) else (
    echo [✓] Mirror server not started
)

echo.

REM ═══════════════════════════════════════════════════════════
REM STEP 3: Start Browser Client
REM ═══════════════════════════════════════════════════════════
echo ═══════════════════════════════════════════════════════════
echo Step 3: Browser Client
echo ═══════════════════════════════════════════════════════════
echo.
echo Starting QWDE Browser...
echo.

start "QWDE Browser" "output\QWDE_Browser\QWDE_Browser.exe"

timeout /t 2 /nobreak >nul
echo [✓] Browser started

echo.

REM ═══════════════════════════════════════════════════════════
REM Summary
REM ═══════════════════════════════════════════════════════════
echo ═══════════════════════════════════════════════════════════
echo Summary
echo ═══════════════════════════════════════════════════════════
echo.
echo The following components are now running:
echo.
echo   ✓ QWDE Browser (main window)
if "%mirror_choice%"=="1" (
    echo   ✓ Mirror Server (new command window)
)
echo.
echo To stop components:
echo   • Browser: Close the window
if "%mirror_choice%"=="1" (
    echo   • Mirror Server: Press Ctrl+C in its window
)
echo.
echo ═══════════════════════════════════════════════════════════
echo.
echo All components started successfully!
echo.

pause
