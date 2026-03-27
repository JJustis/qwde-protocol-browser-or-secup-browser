# ✅ QWDE Protocol v3.0 - Build & Deployment Checklist

## Build Process

### Before Building
- [ ] Python 3.8+ installed
- [ ] All source files in main folder
- [ ] `requirements.txt` present

### Running Build
- [ ] Run `build_all.bat`
- [ ] Wait for completion (3-5 minutes)
- [ ] Check for errors in console

### After Building
- [ ] `output/QWDE_Browser/QWDE_Browser.exe` exists
- [ ] `output/QWDE_Central_Server/QWDE_Central_Server.exe` exists
- [ ] `output/QWDE_Config_Wizard/QWDE_Config_Wizard.exe` exists
- [ ] `switch/` folder created with PHP files
- [ ] `QWDE_Protocol_v3.0_Source.zip` created

## Deployment to secupgrade.com/switch

### Upload PHP Files
- [ ] Upload `switch/peer_directory_api.php` to web server
- [ ] Upload `switch/api_handler.php` to web server
- [ ] Upload `switch/setup_central_database.sql` to web server
- [ ] Upload `switch/qwde_config.ini` to web server
- [ ] Upload `switch/index.html` to web server
- [ ] Upload `switch/css/` folder to web server
- [ ] Upload `switch/js/` folder to web server

### Setup Database
- [ ] Import `setup_central_database.sql` into MySQL
- [ ] Verify database `qwde_directory` created
- [ ] Check tables exist (peers, site_directory, etc.)

### Configure API
- [ ] Edit `peer_directory_api.php` with MySQL credentials
- [ ] Set database host, username, password
- [ ] Test API: `curl https://secupgrade.com/switch/peer_directory_api.php?action=get_stats`
- [ ] Verify JSON response with "status":"success"

### Configure Mirror Server
- [ ] Edit `qwde_config.ini`
- [ ] Set `[central_server]` → `host = secupgrade.com`
- [ ] Set `[central_server]` → `api_path = /switch`
- [ ] Set `[mirror]` → `enabled = True`
- [ ] Set `[mirror]` → `sync_interval = 30`

### Run Mirror Server
- [ ] Run `python qwde_mirror_server.py`
- [ ] Check console for "Polling every 30 seconds"
- [ ] Verify "Synced X sites" messages appear
- [ ] Test site download from PHP server

### Test Complete System
- [ ] PHP API responds correctly
- [ ] Mirror server polling every 30 seconds
- [ ] Sites downloaded to mirror server
- [ ] Browser can connect to central directory
- [ ] Sites can be registered and retrieved

## Configuration Wizard

### Run Wizard
- [ ] Run `QWDE_Config_Wizard.exe`
- [ ] Complete all 8 steps
- [ ] Step 2: Select central server type
- [ ] Step 3: Select database type (MySQL/SQLite)
- [ ] Step 7: Review self-host guide
- [ ] Step 8: Save configuration

### Verify Configuration
- [ ] `qwde_config.ini` saved correctly
- [ ] Central server URL correct
- [ ] Database settings correct
- [ ] Mirror server settings correct

## Documentation

### Files Present
- [ ] `README.md` - Main documentation
- [ ] `BUILD_PROCESS.md` - Build process guide
- [ ] `DATABASE_OPTIONS.md` - Database configuration
- [ ] `SYSTEM_DIAGRAM.md` - Architecture diagrams
- [ ] `switch/README.md` - PHP deployment guide

### Updated Files
- [ ] `build_all.bat` creates switch/ folder
- [ ] `build_all.bat` includes switch/ in zip
- [ ] `qwde_config.ini` has [database] section
- [ ] `qwde_mysql_ddns.py` supports MySQL/SQLite
- [ ] `qwde_config_wizard.py` has 8 steps including self-host guide

## Final Verification

### Build Output
- [ ] All 3 EXEs built successfully
- [ ] switch/ folder contains all PHP files
- [ ] Release zip includes everything
- [ ] No build errors

### Deployment
- [ ] PHP files uploaded to secupgrade.com/switch/
- [ ] MySQL database setup
- [ ] API tested and working
- [ ] Mirror server running
- [ ] Browser can connect

### Architecture Correct
- [ ] PHP server stores metadata only (NOT site content)
- [ ] Python mirror polls PHP API every 30 seconds
- [ ] Mirror downloads site updates from PHP server
- [ ] Mirror stores sites locally for backup
- [ ] Cache invalidation purges deleted sites

---

**Status:** Ready for deployment  
**Version:** 3.0  
**Date:** 2026-03-27
