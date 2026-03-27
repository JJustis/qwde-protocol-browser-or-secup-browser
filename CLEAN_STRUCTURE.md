# QWDE Protocol - Clean Folder Structure

## Main Folder (Clean)

```
qwde_protocol/
├── Core System Files
│   ├── qwde_browser.py              # Main browser with HTML viewer
│   ├── qwde_peer_network.py         # P2P networking
│   ├── qwde_encryption.py           # Encryption layer
│   ├── qwde_enhanced_encryption.py  # HMAC + AES-GCM
│   ├── qwde_protocol_handler.py     # Protocol customization
│   ├── qwde_protocol.py             # Main integration
│   └── __init__.py                  # Package init
│
├── Security Features
│   ├── qwde_secure_html_viewer.py   # Secure HTML viewer
│   ├── qwde_ownership_tokens.py     # Site ownership tokens
│   └── qwde_delete_site.py          # Site deletion system
│
├── Server Components
│   ├── peer_directory_api.php       # Central directory API
│   ├── qwde_mirror_server.py        # Full mirror server
│   └── qwde_network_health.py       # Network health visualization
│
├── Site Management
│   ├── qwde_site_packager.py        # Export to website folders
│   └── website_template/            # Website export template
│       ├── index.html
│       ├── css/style.css
│       └── js/main.js
│
├── Build & Startup
│   ├── build_all.bat                # Build all EXEs
│   ├── run_all.bat                  # Start all components
│   ├── quick_start.bat              # Quick startup
│   └── rebuild.bat                  # Selective rebuild
│
├── Configuration
│   ├── qwde_config.ini              # Client config
│   ├── server_config.ini            # Server config
│   ├── setup_central_database.sql   # Database setup
│   └── setup_mysql_php.sql          # MySQL setup
│
├── Documentation
│   ├── README.md                    # Main documentation
│   ├── STARTUP_GUIDE.md             # Startup instructions
│   ├── WEBSITE_CREATION_GUIDE.md    # Create websites
│   ├── SUPPORTED_FILE_TYPES.md      # File support
│   ├── SECURE_HTML_VIEWER.md        # Secure viewer docs
│   ├── ENHANCED_ENCRYPTION_GUIDE.md # Encryption docs
│   ├── DELETION_SYSTEM.md           # Deletion docs
│   └── requirements.txt             # Python dependencies
│
└── Plugin System
    └── plugins/                     # Drop plugins here
        ├── __init__.py
        └── dark_mode.py
```

## Old Folder (Archived)

```
old/
├── build/                    # Build artifacts
├── dist/                     # Distribution files
├── output/                   # Previous output
├── qwde_https_config.py      # Old config module
├── qwde_relay_server.py      # Old relay server
├── qwde_secure_server.py     # Old secure server
├── qwde_php_server_launcher.py
├── qwde_mysql_ddns.py        # Old MySQL module
├── qwde_ddns_api.php         # Old API file
├── qwde_browser.spec         # Old spec file
├── BUILD_PREVIEW.bat         # Old preview script
├── fix_protocol_typo.py      # Typo fix script
└── [Old documentation files]
```

## Essential Files Only

### Must Have (Core System)
- ✅ `qwde_browser.py` - Main browser
- ✅ `qwde_peer_network.py` - P2P networking
- ✅ `qwde_encryption.py` - Encryption
- ✅ `qwde_enhanced_encryption.py` - Enhanced encryption
- ✅ `peer_directory_api.php` - Central API
- ✅ `qwde_mirror_server.py` - Mirror server

### Must Have (Security)
- ✅ `qwde_secure_html_viewer.py` - Secure HTML viewer
- ✅ `qwde_ownership_tokens.py` - Ownership tokens
- ✅ `qwde_delete_site.py` - Site deletion

### Must Have (Build)
- ✅ `build_all.bat` - Build script
- ✅ `run_all.bat` - Startup script
- ✅ `quick_start.bat` - Quick start
- ✅ `rebuild.bat` - Rebuild selector

### Must Have (Config)
- ✅ `qwde_config.ini` - Client config
- ✅ `setup_central_database.sql` - Database setup

### Must Have (Docs)
- ✅ `README.md` - Main docs
- ✅ `STARTUP_GUIDE.md` - Startup guide
- ✅ `WEBSITE_CREATION_GUIDE.md` - Website creation
- ✅ `SUPPORTED_FILE_TYPES.md` - File support
- ✅ `SECURE_HTML_VIEWER.md` - Secure viewer
- ✅ `ENHANCED_ENCRYPTION_GUIDE.md` - Encryption
- ✅ `DELETION_SYSTEM.md` - Deletion
- ✅ `requirements.txt` - Dependencies

## File Count

| Category | Count |
|----------|-------|
| **Core Python** | 7 files |
| **Security** | 3 files |
| **Server** | 3 files |
| **Site Management** | 2 files + template |
| **Build Scripts** | 4 files |
| **Configuration** | 4 files |
| **Documentation** | 8 files |
| **Plugins** | 2 files |
| **Total** | 33 files |

## What Was Removed

| Moved to old/ | Reason |
|--------------|--------|
| Build artifacts | Generated files |
| Duplicate API files | Only need peer_directory_api.php |
| Old server modules | Replaced by mirror server |
| Redundant docs | Consolidated into main docs |
| Old spec files | build_all.bat handles this |
| Utility scripts | Not needed for end users |

## Ready to Build

All essential files are in place:
- ✅ Core system files
- ✅ Security features
- ✅ Server components
- ✅ Build scripts
- ✅ Configuration
- ✅ Documentation

**Next Step:** Run `build_all.bat` to compile EXEs
