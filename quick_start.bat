@echo off
REM ═══════════════════════════════════════════════════════════
REM QWDE Protocol - Quick Start
REM Fast startup (skips database setup)
REM ═══════════════════════════════════════════════════════════

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║        QWDE Protocol - Quick Start                        ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM Check output folder
if not exist "output\QWDE_Browser\QWDE_Browser.exe" (
    echo [ERROR] Build not found! Run build_all.bat first.
    pause
    exit /b 1
)

echo Starting QWDE Browser...
start "QWDE Browser" "output\QWDE_Browser\QWDE_Browser.exe"

echo Starting Mirror Server...
start "QWDE Mirror Server" cmd /k "cd output && python qwde_mirror_server.py"

timeout /t 3 /nobreak >nul

echo.
echo ═══════════════════════════════════════════════════════════
echo Components Started:
echo   ✓ Browser
echo   ✓ Mirror Server
echo.
echo Using: secupgrade.com (central directory)
echo ═══════════════════════════════════════════════════════════
echo.

pause
