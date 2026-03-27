# QWDE Protocol - Complete Startup Guide

## Quick Start Options

### Option 1: Quick Start (Recommended for Testing)

```bash
# From qwde_protocol folder
quick_start.bat
```

**Starts:**
- ✓ QWDE Browser
- ✓ Mirror Server (downloads all sites)

**Uses:** secupgrade.com as central server

---

### Option 2: Run All Components (Full Setup)

```bash
# From qwde_protocol folder
run_all.bat
```

**Prompts for:**
1. Database setup (MySQL)
2. Start local central server (optional)
3. Start mirror server (optional)
4. Start browser

**Use this if:**
- Setting up for the first time
- Need to create/recreate database
- Running local central server

---

### Option 3: Manual Start

```bash
# 1. Start Browser
cd output\QWDE_Browser
QWDE_Browser.exe

# 2. Start Mirror Server (optional)
cd output
python qwde_mirror_server.py

# 3. Setup Database (if needed)
mysql -u root -p < setup_central_database.sql
```

---

## File Locations After Build

```
output/
├── QWDE_Browser/
│   ├── QWDE_Browser.exe         ← Main browser
│   └── Start.bat                ← Quick launcher
│
├── QWDE_PyServerDB/
│   ├── QWDE_PyServerDB.exe      ← Local server (optional)
│   ├── Start_Mirror.bat         ← Mirror server launcher
│   └── setup_central_database.sql
│
├── Documentation/
│   └── README.md
│
├── setup_central_database.sql   ← Database setup
├── run_all.bat                  ← Full startup script
├── quick_start.bat              ← Quick startup
└── qwde_mirror_server.py        ← Mirror server source
```

---

## Database Setup

### When to Setup Database

**Needed if:**
- Running your own central server
- Using local MySQL instead of secupgrade.com

**NOT needed if:**
- Using secupgrade.com (recommended)
- Just browsing/creating sites

### Setup Commands

```bash
# Method 1: Automatic (via run_all.bat)
run_all.bat
# Choose option 1: Yes - Setup database

# Method 2: Manual
mysql -u root -p < setup_central_database.sql
```

### What the SQL Script Does

1. Drops existing database (if exists)
2. Creates fresh `qwde_directory` database
3. Creates `qwede_user` with password
4. Creates tables:
   - `peers` - Peer IP registry
   - `site_directory` - Site metadata
   - `peer_sites` - Peer-site mapping
   - `system_stats` - Statistics
5. Creates views and stored procedures
6. Sets up auto-cleanup event (every 5 minutes)

### Verify Database

```bash
# Test connection
mysql -u qwede_user -p -e "USE qwede_directory; SELECT * FROM vw_stats;"
```

---

## Component Descriptions

### QWDE_Browser.exe
**What it does:**
- Browse qwde:// sites
- Create new sites
- Upload to central server
- Download from peers

**Port:** None (client only)

**Config:** qwede_config.ini

---

### Mirror Server (qwde_mirror_server.py)
**What it does:**
- Downloads ALL sites from ALL peers
- Stores full backup locally
- Detects updates (hash/size/version)
- Auto-updates every 60 seconds
- Serves clients when peers offline

**Port:** 8765 (HTTP API)

**API Endpoints:**
- `GET /?action=get_site&domain=X` - Get site content
- `GET /?action=check_update&domain=X` - Check for updates
- `GET /?action=sync_sites` - Get all sites
- `GET /?action=get_stats` - Get statistics

**Start:**
```bash
python qwede_mirror_server.py
```

---

### Central Server (peer_directory_api.php)
**What it does:**
- Stores peer IPs and ports
- Stores site metadata (NOT content)
- Tracks hash/size/version for updates

**Location:** secupgrade.com/api_handler.php

**Port:** 443 (HTTPS)

**Start (local only):**
```bash
# Upload to secupgrade.com
scp peer_directory_api.php user@secupgrade.com:/var/www/html/

# Or run local PyServerDB
QWDE_PyServerDB.exe
```

---

## Startup Scenarios

### Scenario 1: Just Browsing/Creating Sites

```bash
quick_start.bat
```

**Components:**
- Browser only

**Uses:** secupgrade.com

---

### Scenario 2: Full Local Setup

```bash
run_all.bat
```

**Components:**
- Database (local MySQL)
- Central Server (local)
- Mirror Server (local)
- Browser

**Uses:** Local everything

---

### Scenario 3: Hybrid (Recommended)

```bash
# 1. Setup database once
mysql -u root -p < setup_central_database.sql

# 2. Start mirror server
cd output
python qwede_mirror_server.py

# 3. Start browser (separate window)
cd output\QWDE_Browser
QWDE_Browser.exe
```

**Components:**
- Database (local, for backup)
- Mirror Server (local cache)
- Browser

**Uses:** secupgrade.com + local mirror

---

## Troubleshooting

### MySQL Not Found

**Error:** `'mysql' is not recognized`

**Solution:**
```bash
# Install MySQL
# Or use secupgrade.com (no MySQL needed)
```

### Port Already in Use

**Error:** `Address already in use`

**Solution:**
```bash
# Find process using port 8765
netstat -ano | findstr :8765

# Kill process
taskkill /PID <PID> /F
```

### Mirror Server Won't Start

**Error:** `Module not found`

**Solution:**
```bash
# Install dependencies
pip install requests
```

### Database Connection Failed

**Error:** `Can't connect to MySQL server`

**Solution:**
```bash
# Check MySQL is running
net start MySQL

# Or recreate database
mysql -u root -p < setup_central_database.sql
```

---

## Quick Reference

| Command | What it Does |
|---------|-------------|
| `quick_start.bat` | Start browser + mirror |
| `run_all.bat` | Full setup with prompts |
| `build_all.bat` | Compile EXEs |
| `mysql -u root -p < setup_central_database.sql` | Setup database |
| `python qwede_mirror_server.py` | Start mirror server |
| `QWDE_Browser.exe` | Start browser |

---

## Default Configuration

| Component | Default Setting |
|-----------|----------------|
| Central Server | https://secupgrade.com |
| Mirror Server | http://localhost:8765 |
| Database | localhost:3306 |
| Browser P2P Port | 8766 |
| Mirror API Port | 8765 |

---

**Last Updated:** 2026-03-27  
**Version:** 1.0.0
