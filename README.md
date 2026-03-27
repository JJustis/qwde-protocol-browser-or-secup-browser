# QWDE Protocol - Complete System

**Decentralized Web Protocol with Custom Encryption**

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         QWDE Protocol System                            │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  EXE #1: QWDE_Browser.exe (For ALL Users)                              │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │  Firefox-like GUI Browser                                         │ │
│  │  ├─ Site Creator (Notepad Clone)                                  │ │
│  │  ├─ Plugin System                                                 │ │
│  │  ├─ Network Health Map                                            │ │
│  │  └─ QWDE Encryption Engine                                        │ │
│  │      ├─ RSA Handshake                                             │ │
│  │      ├─ AES Key Exchange                                          │ │
│  │      ├─ Seeded Rolling Encryption                                 │ │
│  │      └─ Error Correction                                          │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                              │                                          │
│                              │ HTTPS                                    │
│                              ▼                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                │
                                │
                ┌───────────────┴───────────────┐
                │                               │
                ▼                               ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│  secupgrade.com           │   │  EXE #2: QWDE_PyServerDB  │
│  (XAMPP + PHP Backend)    │   │  (OPTIONAL - Local Only)  │
│  ┌─────────────────────┐  │   │  ┌─────────────────────┐  │
│  │ qwde_ddns_api.php   │  │   │  │ MySQL Database      │  │
│  │ (Stores encrypted   │  │   │  │ (Only needed if     │  │
│  │  site data)         │  │   │  │  hosting your own   │  │
│  └─────────────────────┘  │   │  │  central server)    │  │
│  ┌─────────────────────┐  │   │  └─────────────────────┘  │
│  │ MySQL Database      │  │   │                           │
│  │ (qwde_ddns)         │  │   │  Use this if you DON'T    │
│  └─────────────────────┘  │   │  have secupgrade.com      │
│                           │   │                           │
│  THIS IS ALL YOU NEED     │   │  NOT NEEDED if using      │
│  for central server       │   │  secupgrade.com           │
└───────────────────────────┘   └───────────────────────────┘
```

## How It Works

### For Regular Users (Browsing & Creating Sites)

```
User runs QWDE_Browser.exe
         │
         ├─► Creates site in Site Creator
         │   └─► Content encrypted with QWDE encryption
         │
         ├─► Publishes to secupgrade.com/qwde_ddns_api.php
         │   └─► Encrypted data stored in MySQL
         │
         └─► Browses qwde:// sites
             └─► Downloads encrypted data, decrypts locally
```

### For Server Hosts (Optional - Only if running own central server)

```
Host runs QWDE_PyServerDB.exe
         │
         ├─► Starts MySQL database
         │   └─► Listens on port 3306
         │
         └─► PHP backend (already on XAMPP)
             └─► Handles API requests from browsers
```

## Files After Build

```
output/
├── QWDE_Browser/
│   ├── QWDE_Browser.exe          ← MAIN APPLICATION
│   ├── qwde_config.ini           ← Configure secupgrade.com
│   ├── plugins/                   ← Plugin folder
│   └── Start_Browser.bat
│
├── QWDE_PyServerDB/              ← OPTIONAL (only for self-hosting)
│   ├── QWDE_PyServerDB.exe
│   └── setup_mysql.sql
│
└── Documentation/
    └── README.md
```

## Quick Start

### For Users (Most Common)

1. **Download** `output/QWDE_Browser/` folder
2. **Run** `QWDE_Browser.exe`
3. **Create** sites with the Site Creator button
4. **Browse** qwede:// sites

**Configuration** (already set to secupgrade.com):
```ini
# qwde_config.ini
[central_server]
url = https://secupgrade.com/qwde_ddns_api.php
```

### For Server Hosting (Optional)

Only needed if you want to host your OWN central server (not using secupgrade.com):

1. **Install XAMPP** (already done for secupgrade.com)
2. **Upload** `qwde_ddns_api.php` to XAMPP htdocs
3. **Run** `setup_mysql.sql` in phpMyAdmin
4. **Users connect** to your server URL

## Encryption Flow

```
┌─────────────────┐
│  Site Creator   │
│  (Write content)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  QWDE Encrypt   │
│  ├─ RSA Keys    │
│  ├─ AES Wrap    │
│  ├─ Rolling     │
│  └─ Error Corr  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Publish to     │
│  secupgrade.com │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  MySQL stores   │
│  encrypted blob │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Other users    │
│  download &     │
│  decrypt        │
└─────────────────┘
```

## Build Instructions

```bash
# Run the build script
build_all.bat

# Output:
# - output/QWDE_Browser/QWDE_Browser.exe (MAIN)
# - output/QWDE_PyServerDB/QWDE_PyServerDB.exe (OPTIONAL)
```

## Configuration

### Using secupgrade.com (Default)

```ini
# qwde_config.ini - Already configured
[central_server]
protocol = https
host = secupgrade.com
url = https://secupgrade.com/qwde_ddns_api.php

[security]
https_only = True
verify_certificates = True
```

### Using Local Server (For Testing)

```ini
[central_server]
protocol = http
host = localhost
port = 8080
url = http://localhost:8080/qwde_ddns_api.php
```

## Features

### QWDE_Browser.exe Includes:
- ✓ Firefox-like GUI
- ✓ Site Creator (Notepad clone)
- ✓ Plugin System
- ✓ Network Health Map
- ✓ HTTPS Support
- ✓ QWDE Custom Encryption
- ✓ qwede:// Protocol
- ✓ Encryption State Indicator

### QWDE_PyServerDB.exe Includes:
- ✓ MySQL Database Server
- ✓ Peer Registry
- ✓ Site Storage
- ✓ 30-second Polling

## What You Need

| Purpose | Need |
|---------|------|
| Browse sites | QWDE_Browser.exe |
| Create sites | QWDE_Browser.exe |
| Host central server (secupgrade.com) | XAMPP + PHP file |
| Host own central server | QWDE_PyServerDB.exe + XAMPP |

## Network Diagram

```
                    ┌─────────────────┐
                    │  secupgrade.com │
                    │  (XAMPP + PHP)  │
                    │  + MySQL DB     │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
         ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
         │ Browser │   │ Browser │   │ Browser │
         │  User 1 │   │  User 2 │   │  User 3 │
         └─────────┘   └─────────┘   └─────────┘
              │              │              │
              └──────────────┴──────────────┘
                             │
                    P2P Connections
                    (Pin Wheel System)
```

## Version
1.0.0 - 2026-03-27
