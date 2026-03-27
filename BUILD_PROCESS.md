# QWDE Protocol - Build Process & Deployment Guide

## Correct Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  PHP Central Directory (secupgrade.com/switch)                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  peer_directory_api.php                                   │ │
│  │  MySQL Database (stores metadata only)                    │ │
│  │  NOT site content - stored on peer computers              │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         ▲
         │ Polls every 30 seconds
         │ Downloads site updates
         │
┌────────┴────────────────────────────────────────────────────────┐
│  Python Mirror Server                                          │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  qwde_mirror_server.py                                    │ │
│  │                                                           │ │
│  │  • Polls PHP API every 30 seconds                        │ │
│  │  • Downloads site updates from PHP server                │ │
│  │  • Stores downloaded sites locally                       │ │
│  │  • Serves as backup when peers offline                   │ │
│  │  • Auto-purges deleted sites on invalidation             │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Build Process (build_all.bat)

### Step-by-Step

```
1. Install dependencies
   ✓ pip install pyinstaller cryptography requests etc.

2. Clean previous builds
   ✓ Remove build/, dist/, output/ folders

3. Build QWDE_Browser.exe
   ✓ Main browser with secure HTML viewer
   ✓ Output: output/QWDE_Browser/QWDE_Browser.exe

4. Build QWDE_Central_Server.exe
   ✓ Python DDNS server (alternative to PHP)
   ✓ Output: output/QWDE_Central_Server/QWDE_Central_Server.exe

5. Build QWDE_Config_Wizard.exe
   ✓ Configuration wizard with self-host guide
   ✓ Output: output/QWDE_Config_Wizard/QWDE_Config_Wizard.exe

6. Copy files
   ✓ Mirror server script
   ✓ Documentation
   ✓ PHP files to switch/ folder ← IMPORTANT!

7. Create launcher scripts
   ✓ Start.bat files for each component

8. Create release zip
   ✓ QWDE_Protocol_v3.0_Source.zip
   ✓ Includes ALL source files + switch/ folder
```

### What Gets Created

```
After build_all.bat:

output/
├── QWDE_Browser/
│   └── QWDE_Browser.exe              ← Main browser
├── QWDE_Central_Server/
│   └── QWDE_Central_Server.exe       ← Python DDNS
├── QWDE_Config_Wizard/
│   └── QWDE_Config_Wizard.exe        ← Config wizard
└── QWDE_Mirror_Server/
    └── qwde_mirror_server.py         ← Mirror server script

switch/  ← PHP Website Files
├── peer_directory_api.php            ← Upload to web server
├── api_handler.php
├── setup_central_database.sql
├── qwde_config.ini
├── index.html
├── css/
└── js/

QWDE_Protocol_v3.0_Source.zip  ← Complete source package
```

## Deployment Process

### 1. Deploy PHP Files (switch/ folder)

```bash
# Upload switch/ folder contents to secupgrade.com/switch/
scp -r switch/* user@secupgrade.com:/var/www/html/switch/

# Or use FTP/SFTP to upload entire switch/ folder
```

### 2. Setup MySQL Database

```bash
# Import database schema
mysql -u root -p < switch/setup_central_database.sql
```

### 3. Configure Python Mirror Server

Edit `qwde_config.ini`:
```ini
[central_server]
protocol = https
host = secupgrade.com
api_path = /switch

[mirror]
enabled = True
sync_interval = 30  # Poll every 30 seconds
update_interval = 60
```

### 4. Run Mirror Server

```bash
cd output/QWDE_Mirror_Server
python qwde_mirror_server.py
```

### 5. Test

```bash
# Test PHP API
curl https://secupgrade.com/switch/peer_directory_api.php?action=get_stats

# Expected:
# {"status":"success","total_peers":0,"total_sites":0,...}

# Test mirror server
# Check console for "Synced X sites" messages
```

## File Locations

| File | Location | Purpose |
|------|----------|---------|
| **PHP API** | `switch/peer_directory_api.php` | Upload to web server |
| **Database SQL** | `switch/setup_central_database.sql` | Import to MySQL |
| **Browser** | `output/QWDE_Browser/QWDE_Browser.exe` | User browser |
| **Config Wizard** | `output/QWDE_Config_Wizard/QWDE_Config_Wizard.exe` | Configuration |
| **Mirror Server** | `output/QWDE_Mirror_Server/qwde_mirror_server.py` | Backup server |
| **Central Server** | `output/QWDE_Central_Server/QWDE_Central_Server.exe` | Alternative to PHP |

## Important Notes

### switch/ Folder

- ✅ Created by `build_all.bat`
- ✅ Contains PHP files for web server deployment
- ✅ Uploaded to `secupgrade.com/switch/`
- ✅ NOT compiled - runs on web server

### Python Mirror Server

- ✅ Polls PHP API every 30 seconds
- ✅ Downloads site updates
- ✅ Stores locally for backup
- ✅ NOT the central directory - just a mirror

### Python Central Server

- ✅ Alternative to PHP backend
- ✅ Can use MySQL or SQLite
- ✅ For self-hosting without PHP
- ✅ NOT needed if using secupgrade.com

## Build Order

```
1. Run build_all.bat
   ↓
2. switch/ folder created with PHP files
   ↓
3. Upload switch/ to secupgrade.com/switch/
   ↓
4. Setup MySQL database
   ↓
5. Configure mirror server
   ↓
6. Run mirror server
   ↓
7. Create release zip (automatic)
```

## Troubleshooting

**switch/ folder not created:**
- Run `build_all.bat` again
- Check for errors in step 7

**Mirror server won't connect:**
- Verify PHP API URL: `https://secupgrade.com/switch/peer_directory_api.php?action=get_stats`
- Check firewall allows outbound HTTPS
- Test with curl first

**PHP API returns error:**
- Check database credentials in `peer_directory_api.php`
- Verify database exists
- Check MySQL user permissions

---

**Last Updated:** 2026-03-27  
**Version:** 3.0  
**Status:** ✅ Build process documented
