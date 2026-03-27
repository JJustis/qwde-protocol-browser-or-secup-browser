@echo off
REM QWDE Protocol - Build Summary
REM Shows what will be built before running the actual build

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║           QWDE Protocol - Build Preview                   ║
echo ╠═══════════════════════════════════════════════════════════╣
echo ║  This script will compile TWO executable files:          ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.
echo  ┌─────────────────────────────────────────────────────────┐
echo  │  1. QWDE_Browser.exe                                    │
echo  │     Location: output\QWDE_Browser\                      │
echo  │     Size: ~30-40 MB (includes Python + all libraries)   │
echo  │                                                         │
echo  │     INCLUDES:                                           │
echo  │     ✓ Full Firefox-like GUI browser                     │
echo  │     ✓ Site Creator (Notepad clone)                      │
echo  │     ✓ Plugin System                                     │
echo  │     ✓ Network Health Topology Map                       │
echo  │     ✓ QWDE Encryption Engine:                           │
echo  │       • RSA-2048 Handshake                              │
echo  │       • AES-256 Encryption                              │
echo  │       • Seeded Rolling Encryption                       │
echo  │       • Wave Diffusion                                  │
echo  │       • Temporal Key Stretching                         │
echo  │       • Error Correction                                │
echo  │     ✓ qwde:// protocol support                          │
echo  │     ✓ HTTPS to secupgrade.com                           │
echo  │                                                         │
echo  │     USE: For ALL users who want to browse/create sites  │
echo  └─────────────────────────────────────────────────────────┘
echo.
echo  ┌─────────────────────────────────────────────────────────┐
echo  │  2. QWDE_PyServerDB.exe                                 │
echo  │     Location: output\QWDE_PyServerDB\                   │
echo  │     Size: ~20-30 MB                                     │
echo  │                                                         │
echo  │     INCLUDES:                                           │
echo  │     ✓ MySQL Database Server                             │
echo  │     ✓ Peer Registry                                     │
echo  │     ✓ Site Storage                                      │
echo  │     ✓ 30-second Polling                                 │
echo  │                                                         │
echo  │     USE: ONLY if hosting your OWN central server        │
echo  │          NOT needed if using secupgrade.com             │
echo  └─────────────────────────────────────────────────────────┘
echo.
echo ═══════════════════════════════════════════════════════════
echo.
echo  SYSTEM DIAGRAM:
echo.
echo      QWDE_Browser.exe
echo           │
echo           │ HTTPS
echo           ▼
echo    secupgrade.com/qwde_ddns_api.php
echo           │
echo           ▼
echo    MySQL Database (qwde_ddns)
echo.
echo  QWDE_PyServerDB.exe (OPTIONAL)
echo    └─ Use this if you DON'T have secupgrade.com
echo.
echo ═══════════════════════════════════════════════════════════
echo.
echo  AFTER BUILD:
echo.
echo  output/
echo  ├── QWDE_Browser/
echo  │   ├── QWDE_Browser.exe     ← MAIN APPLICATION
echo  │   ├── Start.bat
echo  │   ├── qwde_config.ini
echo  │   └── plugins/
echo  │
echo  └── QWDE_PyServerDB/          ← OPTIONAL
echo      ├── QWDE_PyServerDB.exe
echo      ├── Start.bat
echo      └── setup_mysql_php.sql
echo.
echo ═══════════════════════════════════════════════════════════
echo.
echo  BUILD TIME: Approximately 2-5 minutes
echo.
echo  Press Y to start building, or any other key to cancel.
echo.
set /p confirm="Continue with build? (Y/N): "

if /i "%confirm%"=="Y" (
    echo.
    echo Starting build process...
    echo.
    call build_all.bat
) else (
    echo.
    echo Build cancelled.
    echo.
)

pause
