# QWDE Protocol - Installation & Setup Guide

## System Overview Diagram

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                        QWDE PROTOCOL SYSTEM                               ║
╚═══════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────┐
│  COMPONENT 1: QWDE_Browser.exe (REQUIRED - For Everyone)               │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │  Firefox-like Browser GUI                                         │ │
│  │                                                                   │ │
│  │  Features:                                                        │ │
│  │  ├─ Site Creator (Notepad Clone)                                 │ │
│  │  │   └─ Line numbers, syntax highlighting, word count            │ │
│  │  ├─ Plugin System                                                 │ │
│  │  │   ├─ Script Blocker                                           │ │
│  │  │   ├─ Ad Blocker                                               │ │
│  │  │   └─ Privacy Guard                                            │ │
│  │  ├─ Network Health Topology Map                                  │ │
│  │  │   └─ Real-time peer visualization                             │ │
│  │  └─ QWDE Encryption Engine ← BUILT IN                            │ │
│  │      ├─ RSA-2048 Handshake                                       │ │
│  │      ├─ AES-256 Encryption                                       │ │
│  │      ├─ Seeded Rolling Encryption (per-message keys)             │ │
│  │      ├─ Wave Diffusion                                           │ │
│  │      ├─ Temporal Key Stretching                                  │ │
│  │      └─ Error Correction Hash                                    │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                              │                                          │
│                              │ HTTPS (Port 443)                        │
│                              │ qwde_ddns_api.php                       │
│                              ▼                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                │
                                │
                ┌───────────────┴───────────────┐
                │                               │
                ▼                               ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│  secupgrade.com           │   │  COMPONENT 2:             │
│  (XAMPP Web Server)       │   │  QWDE_PyServerDB.exe      │
│  ┌─────────────────────┐  │   │  (OPTIONAL)               │
│  │ qwde_ddns_api.php   │  │   │  ┌─────────────────────┐  │
│  │ (PHP Backend)       │  │   │  │ MySQL Database      │  │
│  └─────────┬───────────┘  │   │  │ Server              │  │
│            │              │   │  │                     │  │
│  ┌─────────▼───────────┐  │   │  │ Use this ONLY if:   │  │
│  │ MySQL Database      │  │   │  │ - You DON'T have    │  │
│  │ (qwde_ddns)         │  │   │  │   secupgrade.com    │  │
│  │                     │  │   │  │ - You want to host  │  │
│  │ Stores:             │  │   │  │   your OWN central  │  │
│  │ - Encrypted sites   │  │   │  │   server            │  │
│  │ - Peer registry     │  │   │  └─────────────────────┘  │
│  │ - fwild index       │  │   │                           │
│  └─────────────────────┘  │   │  NOT NEEDED if you're    │  │
│                           │   │  just using/browsing     │  │
│  THIS IS WHAT YOU NEED    │   │                           │  │
│  for central server       │   │  File: QWDE_PyServerDB.exe│ │
│                           │   │  Port: 8765 (UDP)         │  │
│  Files:                   │   │                           │  │
│  - qwde_ddns_api.php     │   └───────────────────────────┘  │
│  - MySQL database        │                                   │
│  - XAMPP (already have)  │                                   │
└───────────────────────────┘                                   │
                                                                │
┌───────────────────────────────────────────────────────────────┘
│
│  HOW IT WORKS:
│
│  1. User creates site in Browser
│     └─► Content encrypted with QWDE encryption
│
│  2. Browser publishes to secupgrade.com/qwde_ddns_api.php
│     └─► Encrypted data stored in MySQL
│
│  3. Other users browse qwede://mysite
│     └─► Download encrypted data from secupgrade.com
│     └─► Decrypt locally with QWDE encryption
│
│  4. 30-second polling checks for new sites
│     └─► Auto-downloads new content
└─────────────────────────────────────────────────────────────────┘
```

## What You Need

| If you want to... | You need |
|-------------------|----------|
| Browse QWDE sites | QWDE_Browser.exe |
| Create QWDE sites | QWDE_Browser.exe |
| Host central server (using secupgrade.com) | XAMPP + qwde_ddns_api.php |
| Host your OWN central server | QWDE_PyServerDB.exe + XAMPP |

## Installation Steps

### Step 1: Build the System

```bash
# Run the build script
build_all.bat

# Wait 2-5 minutes for compilation
```

### Step 2: For Users (Browse & Create Sites)

```
1. Go to: output\QWDE_Browser\
2. Run: QWDE_Browser.exe (or Start.bat)
3. Browser opens with dark theme
4. Click "Network" → "Connect"
5. Click "Create Site" to make websites
6. Publish to secupgrade.com
```

**Configuration** (already set):
```ini
# qwde_config.ini
[central_server]
url = https://secupgrade.com/qwde_ddns_api.php
```

### Step 3: For Server Hosting (secupgrade.com)

**Upload PHP Backend:**

1. Copy `qwde_ddns_api.php` to XAMPP htdocs:
   ```
   C:\xampp\htdocs\qwde_ddns_api.php
   ```

2. Create MySQL database:
   - Open phpMyAdmin (http://localhost/phpmyadmin)
   - Run SQL from `setup_mysql_php.sql`

3. Test the API:
   ```
   http://localhost/qwde_ddns_api.php?action=get_stats
   ```

4. For production (secupgrade.com):
   - Upload `qwde_ddns_api.php` to your web server
   - Create database on your MySQL server
   - Update `qwde_config.ini` with your URL

### Step 4: For Self-Hosting (Alternative to secupgrade.com)

Only if you want to host your OWN central server:

```
1. Go to: output\QWDE_PyServerDB\
2. Run: setup_mysql.sql in phpMyAdmin
3. Run: QWDE_PyServerDB.exe --server
4. Update qwde_config.ini:
   [central_server]
   url = http://localhost:8765/qwde_ddns_api.php
```

## Encryption System (Built into Browser)

```
┌─────────────────────────────────────────────────────────────┐
│  QWDE Encryption Flow (Inside QWDE_Browser.exe)            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Site Content (plaintext)                                   │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  encrypt_qwde() - From improved_qwde.py             │  │
│  │                                                       │  │
│  │  1. Split into 4 quadrants                           │  │
│  │  2. Generate polymorphic seeds                       │  │
│  │     ├─ S (seed), E (entropy), U (unique)            │  │
│  │     └─ Uses: omega, tau_max, eta, n, kappa          │  │
│  │  3. Apply transformations:                           │  │
│  │     ├─ Temporal Key Stretching (τ∞)                 │  │
│  │     ├─ Wave Diffusion (D_n)                         │  │
│  │     ├─ Security-Modulated XOR (η)                   │  │
│  │     └─ AES-CBC Encryption                           │  │
│  │  4. Generate error correction hash                   │  │
│  └──────────────────────────────────────────────────────┘  │
│         │                                                    │
│         ▼                                                    │
│  Encrypted Site Data (ciphertext)                           │
│         │                                                    │
│         ▼                                                    │
│  Publish to secupgrade.com                                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## File Structure After Build

```
output/
│
├── QWDE_Browser/                    ← MAIN FOLDER
│   ├── QWDE_Browser.exe             ← RUN THIS
│   ├── Start.bat                    ← Quick launcher
│   ├── qwde_config.ini              ← Settings (secupgrade.com)
│   └── plugins/                     ← Plugin folder
│       ├── __init__.py
│       └── dark_mode.py
│
├── QWDE_PyServerDB/                 ← OPTIONAL FOLDER
│   ├── QWDE_PyServerDB.exe          ← Only for self-hosting
│   ├── Start.bat                    ← Quick launcher
│   ├── setup_mysql_php.sql          ← Database setup
│   └── qwde_config.ini              ← Settings
│
└── Documentation/
    ├── README.md                    ← This file
    ├── server_config.ini            ← Advanced config
    └── INSTALLATION_GUIDE.md        ← Detailed setup
```

## Quick Reference

| Action | Command/File |
|--------|-------------|
| Start Browser | `output\QWDE_Browser\QWDE_Browser.exe` |
| Start Server (local) | `output\QWDE_PyServerDB\QWDE_PyServerDB.exe --server` |
| Upload PHP | Copy `qwde_ddns_api.php` to XAMPP htdocs |
| Setup Database | Run `setup_mysql_php.sql` in phpMyAdmin |
| Test API | `http://localhost/qwde_ddns_api.php?action=get_stats` |

## Ports Used

| Component | Port | Protocol |
|-----------|------|----------|
| Browser → Server | 443 | HTTPS |
| PyServerDB | 8765 | UDP |
| P2P Connections | 8766 | TCP |
| XAMPP (default) | 80 | HTTP |
| XAMPP (SSL) | 443 | HTTPS |

## Troubleshooting

**Browser won't connect:**
1. Check internet connection
2. Verify secupgrade.com is accessible
3. Check firewall allows HTTPS

**PHP API not working:**
1. Ensure XAMPP is running
2. Check `qwde_ddns_api.php` is in htdocs
3. Verify MySQL database exists
4. Test: `http://localhost/qwde_ddns_api.php?action=get_stats`

**Encryption errors:**
1. Check `improved_qwde.py` is present
2. Verify cryptography library: `pip install cryptography`
3. Check console for detailed errors

## Support

For issues or questions, check:
1. Console output in browser
2. XAMPP error logs
3. MySQL error logs
4. Configuration files

---

**Version:** 1.0.0  
**Build Date:** 2026-03-27  
**Central Server:** https://secupgrade.com
