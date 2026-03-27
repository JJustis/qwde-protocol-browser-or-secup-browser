# QWDE Protocol v3.0 - Complete Decentralized Web System

**Status:** ✅ Production Ready  
**Last Updated:** 2026-03-27  
**Build:** Complete with Config Wizard

## Overview

QWDE (pronounced "quade") is a complete decentralized web protocol featuring:

- **Custom encryption** (HMAC + AES-GCM + QWDE custom algorithm)
- **Peer-to-peer site hosting** (sites stored on peer computers)
- **Central directory** (metadata only - NOT content)
- **Full mirror backup** (downloads all sites for offline access)
- **Ownership tokens** (secure site deletion with cache invalidation)
- **Secure HTML viewer** (source-first rendering for security)
- **Plugin system** (extend browser functionality)
- **Configuration wizard** (easy setup for all components)

## Quick Start

### Option 1: Use Config Wizard (Recommended for First Time)

```bash
cd output\QWDE_Config_Wizard
QWDE_Config_Wizard.exe
```

**Wizard guides you through:**
1. Central server configuration
2. Database setup
3. Browser settings
4. Mirror server configuration
5. Security settings

### Option 2: Quick Start (Default Settings)

```bash
start.bat
# Select option 1 (Browser)
```

### Option 3: Manual Start

```bash
# Browser
cd output\QWDE_Browser
QWDE_Browser.exe

# Mirror Server (optional)
cd output\QWDE_Mirror_Server
python qwde_mirror_server.py
```

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  CENTRAL DIRECTORY (secupgrade.com or your server)             │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  peer_directory_api.php OR QWDE_Central_Server.exe       │ │
│  │                                                           │ │
│  │  Stores ONLY:                                             │ │
│  │  • Peer IP addresses and ports                           │ │
│  │  • Site metadata (domain, fwild, creator)                │ │
│  │  • Ownership tokens (for deletion)                       │ │
│  │  • Site hashes (for update detection)                    │ │
│  │  • Cache invalidation records                            │ │
│  │                                                           │ │
│  │  ✗ Does NOT store site content                           │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │
         │ HTTPS API calls
         │
┌────────▼────────────────────────────────────────────────────────┐
│  MIRROR SERVER (Optional - Full Backup)                        │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  • Downloads ALL sites from ALL peers                    │ │
│  │  • Stores full copy locally                              │ │
│  │  • Detects updates (hash/size/version)                   │ │
│  │  • Auto-purges deleted sites from cache                  │ │
│  │  • Serves when peers offline                             │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │
         │ P2P connections
         │
┌────────▼────────────────────────────────────────────────────────┐
│  PEERS (User Computers)                                        │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  QWDE_Browser.exe                                         │ │
│  │  • Creates sites (stored locally on peer computer)       │ │
│  │  • Serves sites via P2P (port 8766)                      │ │
│  │  • Registers metadata with central directory             │ │
│  │  • Ownership tokens for secure deletion                  │ │
│  │  • Secure HTML viewer (source-first)                     │ │
│  │  • Plugin system support                                 │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Build Output Structure

```
output/
├── QWDE_Browser/
│   ├── QWDE_Browser.exe         ← Main browser
│   ├── Start.bat                ← Quick launcher
│   └── qwde_config.ini          ← Browser config
│
├── QWDE_Central_Server/
│   ├── QWDE_Central_Server.exe  ← Python DDNS server
│   ├── Start.bat                ← Launcher
│   ├── peer_directory_api.php   ← PHP alternative
│   └── setup_central_database.sql
│
├── QWDE_Config_Wizard/
│   ├── QWDE_Config_Wizard.exe   ← Configuration wizard
│   └── Start.bat                ← Launcher
│
├── QWDE_Mirror_Server/
│   ├── qwde_mirror_server.py    ← Mirror server script
│   └── Start.bat                ← Launcher
│
├── Documentation/
│   ├── README.md
│   ├── STARTUP_GUIDE.md
│   ├── WEBSITE_CREATION_GUIDE.md
│   ├── SECURE_HTML_VIEWER.md
│   └── ...
│
└── start.bat                     ← Master launcher
```

## Features

### 🔐 Security Features

| Feature | Description |
|---------|-------------|
| **Three-Layer Encryption** | QWDE custom + AES-GCM + HMAC |
| **Secure HTML Viewer** | Shows source first, then render |
| **Ownership Tokens** | Required for site deletion |
| **Cache Invalidation** | Auto-purge deleted sites |
| **HTTPS-Only Mode** | Block unencrypted connections |
| **Certificate Verification** | Validate SSL certificates |

### 🌐 Content Support

**QWDE Protocol (`qwde://`)**
- ✅ HTML (with secure rendering)
- ✅ Plain text (`.txt`, `.md`)
- ✅ JSON, XML
- ✅ Encrypted QWDE sites
- ✅ Binary files (hex view)

**HTTP/HTTPS**
- ✅ View source code
- ✅ Download text files
- ✅ Secure HTML viewer (if HTML detected)

### 🔌 Plugin System

**Built-in Plugins:**
- Script Blocker - Blocks JavaScript
- Ad Blocker - Blocks ads & trackers
- Privacy Guard - Privacy enhancements
- Dark Mode - Forces dark theme

**Create Custom Plugins:**
```python
from qwde_browser import QWDEPlugin

class MyPlugin(QWDEPlugin):
    name = "My Plugin"
    version = "1.0.0"
    
    def on_page_load(self, url, content):
        # Modify content
        return content
    
    def on_request(self, url):
        # Block/allow requests
        return True
```

### 🗑️ Site Deletion with Cache Invalidation

**Deletion Flow:**
```
Site Owner
    │
    ├─► Requests deletion with ownership token
    │
    ▼
Central Directory
    │
    ├─► Verifies ownership token
    ├─► Marks site as deleted
    └─► Broadcasts cache invalidation
    │
    ▼
All Clients & Mirror Servers
    │
    ├─► Receive invalidation message
    ├─► Purge site from cache
    └─► Confirm deletion
```

**Cache Invalidation:**
- ✅ Automatic purge on deletion
- ✅ Polling every 30 seconds
- ✅ Signature verification
- ✅ All clients synchronized

### 🖥️ Secure HTML Viewer

**Security Flow:**
```
1. HTML Loaded
   ↓
2. Shows Source Code (user reviews)
   ↓
3. User Clicks "Render HTML"
   ↓
4. Security Warning Dialog
   ↓
5. User Confirms
   ↓
6. HTML Rendered
```

**Features:**
- Source code shown first
- Security confirmation required
- Toggle between source/render
- External browser option

## Configuration

### Using Config Wizard

```bash
cd output\QWDE_Config_Wizard
QWDE_Config_Wizard.exe
```

**Wizard configures:**
1. Central server (secupgrade.com or self-hosted)
2. MySQL database connection
3. Browser settings (protocol, HTML rendering)
4. Mirror server (port, sync intervals)
5. Security (HTTPS, certificates, tokens)

### Manual Configuration

Edit `qwde_config.ini`:

```ini
[central_server]
protocol = https
host = secupgrade.com
port = 443
api_path = /peer_directory_api.php

[mysql]
host = localhost
port = 3306
database = qwde_directory
user = qwede_user
password = your_password

[protocol]
protocol_prefix = qwde
protocol_separator = ://

[security]
https_only = True
verify_certificates = True
token_expiry = 5
auto_invalidate = True
invalidation_poll = 30

[mirror]
enabled = True
port = 8765
sync_interval = 30
update_interval = 60
cache_purge = True
```

## Deployment

### Central Directory (secupgrade.com)

**Option 1: PHP Backend**
```bash
# Upload to secupgrade.com
scp peer_directory_api.php user@secupgrade.com:/var/www/html/

# Setup database
mysql -u root -p < setup_central_database.sql
```

**Option 2: Python Backend**
```bash
# Run Python central server
cd output\QWDE_Central_Server
QWDE_Central_Server.exe --server
```

### Mirror Server

```bash
cd output\QWDE_Mirror_Server
python qwde_mirror_server.py
```

**Features:**
- Downloads ALL sites from ALL peers
- Checks for updates every 60 seconds
- Auto-purges deleted sites
- Serves clients when peers offline

### Client Distribution

```bash
# Build
build_all.bat

# Distribute
output/QWDE_Browser/QWDE_Browser.exe
```

## Usage Examples

### Create Site

```bash
# 1. Open Browser
QWDE_Browser.exe

# 2. Click "Create Site" (Ctrl+N)

# 3. Write HTML
<!DOCTYPE html>
<html>
<head><title>My Site</title></head>
<body><h1>Hello QWDE!</h1></body>
</html>

# 4. Enter domain: mysite
# 5. Enable encryption ✓
# 6. Click "Publish"
```

### Delete Site

```bash
# In Browser:
# File → Delete My Site (Ctrl+D)

# Select site → Confirm deletion
# Site purged from all caches
```

### Configure with Wizard

```bash
cd output\QWDE_Config_Wizard
QWDE_Config_Wizard.exe

# Follow wizard steps:
# 1. Central Server
# 2. Database
# 3. Browser
# 4. Mirror Server
# 5. Security
# 6. Review & Save
```

## API Endpoints

### Central Directory

| Action | Method | Description |
|--------|--------|-------------|
| `register_peer` | POST | Register peer IP |
| `get_peers` | GET | Get peer list |
| `register_site` | POST | Register site metadata |
| `get_site` | GET | Get site metadata |
| `delete_site` | POST | Delete site (requires token) |
| `get_invalidations` | GET | Get cache invalidations |
| `get_stats` | GET | Get statistics |

### Mirror Server

| Action | Method | Description |
|--------|--------|-------------|
| `get_site` | GET | Get site content |
| `sync_sites` | GET | Get all sites |
| `check_update` | GET | Check for updates |
| `get_stats` | GET | Get mirror stats |

## Database Schema

```sql
-- Peer registry
peers (peer_id, peer_ip, peer_port, public_key, last_seen, is_online)

-- Site metadata (NOT content)
site_directory (
    id, domain, fwild, creator_peer_id,
    ownership_token, site_hash, site_size,
    version, is_active, created_at, updated_at
)

-- Cache invalidations
cache_invalidations (
    id, domain, fwild, deleted_at, signature, broadcast_at
)

-- Deletion log
deletion_log (
    id, domain, deleted_by, deleted_at, reason
)
```

## Troubleshooting

### Build Fails

```bash
# Install dependencies
pip install -r requirements.txt

# Clean build
build_all.bat
```

### Database Connection Failed

```bash
# Test connection
mysql -u qwede_user -p -e "USE qwede_directory; SELECT 1;"

# Recreate database
mysql -u root -p < setup_central_database.sql
```

### Site Not Purged from Cache

**Check:**
1. Ownership token is valid
2. Cache invalidation broadcast received
3. Polling interval (default: 30s)
4. Mirror server running

### HTML Not Rendering

```bash
# Install HTML renderer
pip install PyQt5 PyQtWebEngine

# Or use external browser option
# Click "Open in Browser" button
```

## Requirements

- **Python:** 3.8+
- **MySQL:** 5.7+ (for central directory)
- **PHP:** 7.4+ (for PHP backend)
- **PyQt5:** Optional (for HTML rendering)

## Files

| File | Purpose |
|------|---------|
| `qwde_browser.py` | Main browser with secure HTML viewer |
| `qwde_peer_network.py` | P2P networking |
| `qwde_encryption.py` | Encryption layer |
| `qwde_enhanced_encryption.py` | HMAC + AES-GCM |
| `qwde_secure_html_viewer.py` | Secure HTML viewer |
| `qwde_ownership_tokens.py` | Ownership token system |
| `qwde_delete_site.py` | Site deletion system |
| `qwde_mirror_server.py` | Mirror server |
| `qwde_config_wizard.py` | Configuration wizard |
| `qwde_mysql_ddns.py` | Python central server |
| `peer_directory_api.php` | PHP central server |

## Documentation

| Document | Purpose |
|----------|---------|
| `README.md` | This file - complete overview |
| `STARTUP_GUIDE.md` | Startup instructions |
| `WEBSITE_CREATION_GUIDE.md` | Create websites |
| `SECURE_HTML_VIEWER.md` | Secure viewer docs |
| `ENHANCED_ENCRYPTION_GUIDE.md` | Encryption docs |
| `DELETION_SYSTEM.md` | Deletion & cache invalidation |
| `SUPPORTED_FILE_TYPES.md` | File support |

## Changelog

### Version 3.0 (Current)

- ✅ Configuration wizard for all components
- ✅ Python central DDNS server (alternative to PHP)
- ✅ Cache invalidation with auto-purge
- ✅ Ownership tokens for secure deletion
- ✅ Secure HTML viewer (source-first)
- ✅ HMAC + AES-GCM encryption
- ✅ Full mirror server with update detection
- ✅ Plugin system

### Version 2.0

- ✅ QWDE custom encryption
- ✅ Peer-to-peer distribution
- ✅ Central directory (metadata only)
- ✅ fwild indexing

### Version 1.0

- ✅ Basic encryption
- ✅ Site creation
- ✅ Peer registration

## Support

For issues or questions:
1. Check documentation in `output/Documentation/`
2. Run Config Wizard to verify settings
3. Check console logs for errors
4. Test with localhost first

## License

MIT License

---

**Build Date:** 2026-03-27  
**Version:** 3.0  
**Status:** ✅ Production Ready  
**Components:** Browser, Central Server, Config Wizard, Mirror Server
