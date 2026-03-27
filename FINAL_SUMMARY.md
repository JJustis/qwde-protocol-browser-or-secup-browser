# QWDE Protocol - Final System Summary

## ✅ COMPLETE SYSTEM

### Two EXE Files Built

```
build_all.bat
    │
    ├─► QWDE_Browser.exe         [REQUIRED - For Everyone]
    │   ├─ Full browser GUI
    │   ├─ Site Creator
    │   ├─ Plugin System
    │   ├─ Network Health Map
    │   └─ QWDE Encryption (RSA+AES+Rolling)
    │
    └─► QWDE_PyServerDB.exe      [OPTIONAL - Self-hosting only]
        ├─ MySQL Database Server
        └─ Only needed if NOT using secupgrade.com
```

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  QWDE_Browser.exe (User runs this)                         │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Browser GUI (Firefox-like)                           │ │
│  │  Site Creator (Notepad clone)                         │ │
│  │  Plugins                                              │ │
│  │  Network Map                                          │ │
│  │                                                        │ │
│  │  ┌─────────────────────────────────────────────────┐  │ │
│  │  │  QWDE Encryption Engine (BUILT IN)             │  │ │
│  │  │  ├─ RSA-2048                                   │  │ │
│  │  │  ├─ AES-256                                    │  │ │
│  │  │  ├─ Seeded Rolling (per-message keys)          │  │ │
│  │  │  ├─ Wave Diffusion                             │  │ │
│  │  │  ├─ Temporal Key Stretching                    │  │ │
│  │  │  └─ Error Correction                           │  │ │
│  │  └─────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
         │
         │ HTTPS (Port 443)
         │ POST/GET to qwde_ddns_api.php
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  secupgrade.com (XAMPP Server)                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  qwde_ddns_api.php                                    │ │
│  │  (PHP Backend - Stores encrypted site data)           │ │
│  └───────────────────────────────────────────────────────┘ │
│         │                                                   │
│         ▼                                                   │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  MySQL Database (qwde_ddns)                           │ │
│  │  ├─ sites table (encrypted blobs)                     │ │
│  │  ├─ peers table                                       │ │
│  │  └─ fwild index                                       │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## How Users Experience It

```
1. User runs QWDE_Browser.exe
   │
   ├─► Dark theme browser opens
   ├─► Looks like Firefox developer edition
   │
2. User clicks "Create Site"
   │
   ├─► Notepad-like editor opens
   ├─► Write HTML/content
   ├─► Enter domain name
   ├─► Click "Publish"
   │
   ├─► Content encrypted with QWDE encryption
   ├─► Sent to secupgrade.com/qwde_ddns_api.php
   ├─► Stored in MySQL database
   │
3. User browses qwede://mysite.qwde
   │
   ├─► Downloads encrypted data from secupgrade.com
   ├─► Decrypts locally in browser
   ├─► Displays content
   │
4. 30-second polling
   │
   ├─► Automatically checks for new sites
   ├─► Downloads new content
   └─► Updates available sites
```

## Files in output/ Folder

```
output/
│
├── QWDE_Browser/                         ← MAIN FOLDER
│   ├── QWDE_Browser.exe                  ← RUN THIS
│   ├── Start.bat                         ← Quick launcher
│   ├── qwde_config.ini                   ← Pre-configured for secupgrade.com
│   └── plugins/
│       ├── __init__.py
│       └── dark_mode.py
│
├── QWDE_PyServerDB/                      ← OPTIONAL FOLDER
│   ├── QWDE_PyServerDB.exe               ← Only for self-hosting
│   ├── Start.bat
│   └── setup_mysql_php.sql
│
└── Documentation/
    ├── README.md                         ← System overview with diagrams
    ├── INSTALLATION_GUIDE.md             ← Step-by-step setup
    └── server_config.ini                 ← Advanced configuration
```

## Configuration (Already Set)

**qwde_config.ini** (inside QWDE_Browser folder):
```ini
[central_server]
# Pre-configured to use secupgrade.com base domain
protocol = https
host = secupgrade.com
port = 443
url = https://secupgrade.com/qwde_ddns_api.php

[security]
# HTTPS enabled by default
https_only = True
verify_certificates = True
```

## Build Instructions

```bash
# Step 1: Run build script
build_all.bat

# Step 2: Wait 2-5 minutes
# PyInstaller compiles Python to EXE

# Step 3: Find output in:
# output/QWDE_Browser/QWDE_Browser.exe
# output/QWDE_PyServerDB/QWDE_PyServerDB.exe
```

## What's Included in QWDE_Browser.exe

| Feature | Description |
|---------|-------------|
| **GUI Browser** | Firefox-like interface with tabs |
| **Site Creator** | Notepad clone with line numbers, syntax highlighting |
| **Plugins** | Script Blocker, Ad Blocker, Privacy Guard, Dark Mode |
| **Network Map** | Real-time topology visualization |
| **Encryption** | Full QWDE system from improved_qwde.py |
| **HTTPS** | Secure connection to secupgrade.com |
| **qwede://** | Protocol support for decentralized sites |
| **Toolbar** | Encryption indicator, URL bar, navigation |

## Encryption Details (Built In)

The browser includes ALL encryption from `improved_qwde.py`:

```python
# This code is COMPILED into QWDE_Browser.exe
encrypt_qwde(
    S=os.urandom(16),           # Seed
    E=hashlib.sha256(data).digest(),  # Entropy
    U=os.urandom(16),           # Unique
    plaintext=site_content,
    omega=1.0,                   # Temporal parameter
    tau_max=1.0,                 # Max fuzz
    eta=0.1,                     # Security level
    n=100,                       # Iterations
    kappa=0.01                   # Decay rate
)
```

**Result:**
- 4 encrypted quadrants
- Error correction hash
- Temporal parameters applied
- Wave diffusion applied
- Security-modulated XOR

## For Server Hosting

**If you have secupgrade.com with XAMPP:**

1. Upload `qwde_ddns_api.php` to htdocs
2. Run `setup_mysql_php.sql` in phpMyAdmin
3. Done! Users can connect

**If you want to host your own:**

1. Run `QWDE_PyServerDB.exe --server`
2. Update `qwde_config.ini` with your URL
3. Users connect to your server

## Quick Start for Users

```
1. Download output/QWDE_Browser/ folder
2. Run QWDE_Browser.exe
3. Click "Network" → "Connect"
4. Click "Create Site" to make websites
5. Browse qwede:// sites
```

## Quick Start for Server Hosts

```
1. Upload qwde_ddns_api.php to XAMPP
2. Create MySQL database
3. Users connect via QWDE_Browser.exe
```

## Version Information

- **Build System:** PyInstaller 6.x
- **Python:** 3.8+
- **Encryption:** QWDE (RSA+AES+Rolling)
- **Protocol:** qwede://
- **Central Server:** https://secupgrade.com
- **Last Updated:** 2026-03-27
