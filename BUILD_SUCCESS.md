# QWDE Protocol - Build & Correction Summary

## ✅ Build Successful!

Both EXE files compiled successfully:

```
✓ QWDE_Browser.exe      (43 MB)
✓ QWDE_PyServerDB.exe   (35 MB)
```

## Location

```
output/
├── QWDE_Browser/
│   ├── QWDE_Browser.exe      ← RUN THIS
│   ├── Start.bat
│   ├── qwde_config.ini
│   └── plugins/
│
└── QWDE_PyServerDB/
    ├── QWDE_PyServerDB.exe   ← OPTIONAL
    ├── Start.bat
    └── setup_mysql_php.sql
```

## Protocol Correction

**Fixed:** All instances of `qwede://` → `qwde://site.domain`

**Correct Protocol Format:**
```
qwde://mysite.qwde
qwde://fwild:123
```

**Files Updated:**
- ✓ README.md
- ✓ INSTALLATION_GUIDE.md
- ✓ FINAL_SUMMARY.md
- ✓ output/Documentation/README.md
- ✓ old/VISUAL_GUIDE.md

## How to Use

### For Users

```bash
# 1. Go to output folder
cd output\QWDE_Browser

# 2. Run browser
QWDE_Browser.exe

# 3. Create sites
# Click "Create Site" button

# 4. Browse qwde:// sites
# Enter: qwde://mysite.qwde
```

### For Server (secupgrade.com)

1. Upload `qwde_ddns_api.php` to XAMPP htdocs
2. Run `setup_mysql_php.sql` in phpMyAdmin
3. Users connect via browser

## System Diagram

```
QWDE_Browser.exe  ──HTTPS──>  secupgrade.com/qwde_ddns_api.php  ──>  MySQL
      │                              │
      │                              │
Has full QWDE                   PHP Backend
encryption built in              (stores encrypted
(RSA+AES+Rolling)                 site data)

Protocol: qwde://site.domain
```

## What's Built In

### QWDE_Browser.exe
- ✓ Firefox-like GUI
- ✓ Site Creator (Notepad clone)
- ✓ Plugin System
- ✓ Network Health Topology Map
- ✓ **QWDE Encryption** (from improved_qwde.py):
  - RSA-2048 Handshake
  - AES-256 Encryption
  - Seeded Rolling Encryption
  - Wave Diffusion
  - Temporal Key Stretching
  - Error Correction Hash
- ✓ qwde:// protocol support
- ✓ HTTPS to secupgrade.com

### QWDE_PyServerDB.exe
- ✓ MySQL Database Server
- ✓ Peer Registry
- ✓ Site Storage
- ✓ 30-second Polling

## Configuration

**Pre-configured in qwde_config.ini:**
```ini
[central_server]
url = https://secupgrade.com/qwde_ddns_api.php

[security]
https_only = True
verify_certificates = True
```

## Quick Start

```bash
# Users
cd output\QWDE_Browser
QWDE_Browser.exe

# Then:
# 1. Network → Connect
# 2. Create Site (button)
# 3. Browse qwde://sites
```

## Build Script Fix

**Issue:** PyInstaller not in PATH  
**Solution:** Changed `pyinstaller` to `python -m PyInstaller`

Now builds successfully on all systems with Python 3.8+

---

**Build Date:** 2026-03-27  
**Protocol:** qwde://site.domain  
**Status:** ✅ Complete & Corrected
