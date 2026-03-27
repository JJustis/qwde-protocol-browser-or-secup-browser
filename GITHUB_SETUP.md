# QWDE Protocol - GitHub Repository Structure

## Main Folder Contents (For GitHub)

All files in the main `qwde_protocol/` folder are ready for GitHub upload:

### Python Source Files (.py)
- `qwde_browser.py` - Main browser with secure HTML viewer
- `qwde_peer_network.py` - P2P networking
- `qwde_encryption.py` - Base encryption layer
- `qwde_enhanced_encryption.py` - HMAC + AES-GCM encryption
- `qwde_secure_html_viewer.py` - Secure HTML viewer (source-first)
- `qwde_ownership_tokens.py` - Ownership token system
- `qwde_delete_site.py` - Site deletion with cache invalidation
- `qwde_mirror_server.py` - Mirror server (downloads all sites)
- `qwde_mysql_ddns.py` - Python central DDNS server
- `qwde_config_wizard.py` - Configuration wizard
- `qwde_protocol_handler.py` - Protocol customization
- `qwde_protocol.py` - Main integration module
- `qwde_network_health.py` - Network health visualization
- `qwde_site_packager.py` - Site export tool
- `qwde_html_renderer.py` - HTML rendering engine
- `test_qwde.py` - Test suite
- `__init__.py` - Package initialization

### PHP Files (.php)
- `peer_directory_api.php` - Central directory API (for secupgrade.com)
- `api_handler.php` - Alternative API handler
- `qwde_ddns_api.php` - DDNS API handler

### SQL Files (.sql)
- `setup_central_database.sql` - Central database setup
- `setup_mysql_php.sql` - MySQL setup script

### Build Scripts (.bat)
- `build_all.bat` - Complete build script (all EXEs)
- `run_all.bat` - Run all components
- `quick_start.bat` - Quick startup
- `rebuild.bat` - Selective rebuild

### Configuration Files (.ini)
- `qwde_config.ini` - Main configuration
- `server_config.ini` - Server configuration

### Documentation (.md)
- `README.md` - Main documentation
- `STARTUP_GUIDE.md` - Startup instructions
- `WEBSITE_CREATION_GUIDE.md` - Website creation guide
- `SECURE_HTML_VIEWER.md` - Secure HTML viewer docs
- `ENHANCED_ENCRYPTION_GUIDE.md` - Encryption guide
- `DELETION_SYSTEM.md` - Deletion & cache invalidation
- `SUPPORTED_FILE_TYPES.md` - File type support
- `CLEAN_STRUCTURE.md` - Folder structure docs

### Other Files
- `requirements.txt` - Python dependencies
- `plugins/` - Plugin folder (with sample plugins)
- `website_template/` - Website export template

### Folders
- `old/` - Archived/redundant files (not needed for build)
- `output/` - Build output (generated, can be excluded from git)
- `build/` - PyInstaller build temp (exclude from git)
- `dist/` - PyInstaller dist (exclude from git)

---

## Git Ignore Recommendations

Create `.gitignore` with:

```gitignore
# PyInstaller build artifacts
build/
dist/
*.spec

# Python cache
__pycache__/
*.pyc
*.pyo

# Output folder (generated)
output/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db

# Logs
*.log
```

---

## SourceForge Release Package

**File:** `QWDE_Protocol_v3.0_Source.zip`

**Contains:**
- All source files (.py, .php, .sql)
- Build scripts (.bat)
- Configuration files (.ini)
- Documentation (.md)
- Plugin templates
- Website templates
- Requirements file

**Size:** ~500 KB (source only)

**For Users:**
1. Download zip
2. Extract to folder
3. Run `build_all.bat`
4. Use compiled EXEs from `output/` folder

---

## GitHub Repository Setup

### Repository Name
`qwde-protocol`

### Description
"Decentralized web protocol with secure HTML rendering, ownership tokens, and cache invalidation"

### Topics
- decentralized-web
- python
- encryption
- p2p
- browser
- cybersecurity
- aes-encryption
- hmac
- html-viewer

### License
MIT License (include LICENSE file)

### README
Use `README.md` from main folder

### Releases
Upload `QWDE_Protocol_v3.0_Source.zip` to releases

---

## Build Instructions for Users

### From GitHub (Source)

```bash
# 1. Clone or download
git clone https://github.com/username/qwde-protocol.git
cd qwde-protocol

# 2. Install dependencies
pip install -r requirements.txt

# 3. Build
build_all.bat

# 4. Run
cd output
start.bat
```

### From SourceForge (Zip)

```bash
# 1. Download QWDE_Protocol_v3.0_Source.zip
# 2. Extract to folder
# 3. Install dependencies
pip install -r requirements.txt

# 4. Build
build_all.bat

# 5. Run
cd output
start.bat
```

---

## File Count

| Type | Count |
|------|-------|
| Python (.py) | 17 files |
| PHP (.php) | 3 files |
| SQL (.sql) | 2 files |
| Batch (.bat) | 4 files |
| Config (.ini) | 2 files |
| Documentation (.md) | 8 files |
| Other | 3 files |
| **Total** | **39 files** |

**Plus:**
- `plugins/` folder (2 files)
- `website_template/` folder (3 files)

---

## Ready for Distribution

✅ All source files in main folder  
✅ Build scripts included  
✅ Documentation complete  
✅ Configuration templates ready  
✅ Zip package created for SourceForge  
✅ Ready for GitHub upload  

**Next Steps:**
1. Upload to GitHub repository
2. Create release on SourceForge with zip file
3. Update README with download links
