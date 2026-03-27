@echo off
REM ═══════════════════════════════════════════════════════════
REM QWDE Protocol - Selective Rebuild Script
REM Choose what to rebuild
REM ═══════════════════════════════════════════════════════════

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║        QWDE Protocol - Rebuild Selector                   ║
echo ╠═══════════════════════════════════════════════════════════╣
echo ║  What do you want to rebuild?                            ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.
echo  1. Browser Only (QWDE_Browser.exe)
echo  2. Mirror Server Only (qwde_mirror_server.py - no build needed)
echo  3. Everything (Full rebuild)
echo  4. Cancel
echo.
set /p choice="Enter choice (1-4): "

if "%choice%"=="4" (
    echo.
    echo Build cancelled.
    pause
    exit /b 1
)

if "%choice%"=="1" (
    echo.
    echo ═══════════════════════════════════════════════════════════
    echo Rebuilding Browser...
    echo ═══════════════════════════════════════════════════════════
    echo.
    
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
        move /Y "dist\QWDE_Browser.exe" "output\QWDE_Browser\QWDE_Browser.exe"
        echo.
        echo ╔═══════════════════════════════════════════════════════════╗
        echo ║  ✓ Browser rebuilt successfully!                          ║
        echo ║  Location: output\QWDE_Browser\QWDE_Browser.exe          ║
        echo ╚═══════════════════════════════════════════════════════════╝
    ) else (
        echo.
        echo ╔═══════════════════════════════════════════════════════════╗
        echo ║  ✗ Browser build failed!                                  ║
        echo ╚═══════════════════════════════════════════════════════════╝
    )
    goto :cleanup
)

if "%choice%"=="2" (
    echo.
    echo ═══════════════════════════════════════════════════════════
    echo Mirror Server doesn't need building (runs from Python)
    echo ═══════════════════════════════════════════════════════════
    echo.
    echo To run mirror server:
    echo   cd output
    echo   python qwde_mirror_server.py
    echo.
    goto :cleanup
)

if "%choice%"=="3" (
    echo.
    echo ═══════════════════════════════════════════════════════════
    echo Full Rebuild...
    echo ═══════════════════════════════════════════════════════════
    echo.
    call build_all.bat
    goto :cleanup
)

echo.
echo Invalid choice!

:cleanup
echo.
pause
