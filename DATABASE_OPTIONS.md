# QWDE Protocol - Database Configuration Options

## Overview

The QWDE Protocol now supports **two database backends** for the Python DDNS server:

1. **MySQL** - Full-featured, production-ready
2. **SQLite** - Simple, no installation required

## Database Types

### MySQL

**Best for:**
- Production deployments
- XAMPP users
- Multiple concurrent connections
- Large-scale deployments

**Requirements:**
- MySQL 5.7+ or MariaDB
- OR XAMPP (includes MySQL)

**Configuration:**
```ini
[database]
type = mysql

[mysql]
host = localhost
port = 3306
user = qwde_user
password = your_password
database = qwde_directory
```

**Setup:**
1. Install XAMPP
2. Start MySQL from XAMPP Control Panel
3. Run: `mysql -u root -p < setup_central_database.sql`
4. Configure in Config Wizard (Step 3)

### SQLite

**Best for:**
- Testing and development
- Single-user deployments
- Quick setup without installation
- Portable deployments

**Requirements:**
- None! (Built into Python)

**Configuration:**
```ini
[database]
type = sqlite
sqlite_path = qwde_ddns.db
```

**Setup:**
1. Select "SQLite" in Config Wizard (Step 3)
2. Set database file path (default: `qwde_ddns.db`)
3. Database file created automatically on first run

## Configuration Wizard (Step 3)

The Config Wizard now includes database type selection:

```
╔═══════════════════════════════════════════════════════════╗
║  Step 3: Database Configuration                           ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  Database Type:                                           ║
║  ● MySQL (from XAMPP or installed MySQL)                 ║
║  ○ SQLite (simpler, no installation needed)              ║
║                                                           ║
║  MySQL Fields:                                            ║
║    Host: localhost                                        ║
║    Port: 3306                                             ║
║    Database: qwde_directory                               ║
║    Username: qwde_user                                    ║
║    Password: ********                                     ║
║                                                           ║
║  SQLite Field:                                            ║
║    File Path: qwde_ddns.db                                ║
║                                                           ║
║  [🧪 Test Database Connection]                            ║
╚═══════════════════════════════════════════════════════════╝
```

## Python DDNS Server

The Python DDNS server (`qwde_mysql_ddns.py`) automatically detects the database type from config:

```bash
# Run Python DDNS server
python qwde_mysql_ddns.py --server

# Output shows which database is being used:
╔═══════════════════════════════════════════════════════════╗
║        QWDE Protocol - DDNS Server                        ║
╠═══════════════════════════════════════════════════════════╣
║  Listening on port: 8765                                  ║
║  Database: SQLite: qwde_ddns.db                           ║
╚═══════════════════════════════════════════════════════════╝
```

## Self-Host Guide (Config Wizard Step 7)

The Config Wizard includes a complete self-hosting guide with both database options:

```
STEP 2: SETUP DATABASE
───────────────────────────────────────────────────────────
OPTION A: MySQL (Recommended for production)
1. Open phpMyAdmin: http://localhost/phpmyadmin
2. Click "Import" tab
3. Choose file: setup_central_database.sql
4. Click "Go" button
5. Database "qwde_directory" will be created

OR use command line:
  mysql -u root -p < setup_central_database.sql

OPTION B: SQLite (Simpler, for testing)
1. No setup needed!
2. Database file created automatically
3. Select "SQLite" in Config Wizard
4. Set path: qwde_ddns.db

In Config Wizard (Step 3):
  ● MySQL - For XAMPP/production use
  ○ SQLite - For quick testing, no install
```

## Comparison Table

| Feature | MySQL | SQLite |
|---------|-------|--------|
| **Installation** | Requires MySQL/XAMPP | None (built-in) |
| **Setup Complexity** | Medium | Simple |
| **Performance** | High (concurrent) | Good (single-user) |
| **Scalability** | Excellent | Limited |
| **Network Access** | Yes | No (file-based) |
| **Backup** | Dump/restore | Copy file |
| **Best For** | Production | Testing |

## Migration

### MySQL → SQLite

1. Close Python DDNS server
2. Edit `qwde_config.ini`:
   ```ini
   [database]
   type = sqlite
   sqlite_path = qwde_ddns.db
   ```
3. Restart server
4. **Note:** Existing data won't migrate automatically

### SQLite → MySQL

1. Close Python DDNS server
2. Setup MySQL database
3. Edit `qwde_config.ini`:
   ```ini
   [database]
   type = mysql
   ```
4. Restart server
5. **Note:** Existing data won't migrate automatically

## Architecture

```
Python DDNS Server (qwde_mysql_ddns.py)
    │
    ├─► Database Type Check (from config)
    │
    ├─► If MySQL:
    │   └─► MySQLDDNSDatabase class
    │       └─► MySQL connection
    │
    └─► If SQLite:
        └─► SQLiteDDNSDatabase class
            └─► SQLite file (qwde_ddns.db)
```

## Files Modified

| File | Changes |
|------|---------|
| `qwde_mysql_ddns.py` | Added SQLite support, database type detection |
| `qwde_config_wizard.py` | Added database type selection (Step 3) |
| `qwde_config.ini` | Added `[database]` section |
| `qwde_mysql_ddns.py` | Updated startup banner to show database type |

## Usage Examples

### Quick Test (SQLite)

```bash
# 1. Run Config Wizard
cd output\QWDE_Config_Wizard
QWDE_Config_Wizard.exe

# 2. Select:
#    Step 3: Database Type = SQLite
#    Step 7: Save configuration

# 3. Run Python DDNS server
cd output\QWDE_Central_Server
QWDE_Central_Server.exe --server

# Database file created automatically!
```

### Production (MySQL with XAMPP)

```bash
# 1. Install XAMPP
# 2. Start MySQL from XAMPP
# 3. Setup database:
mysql -u root -p < setup_central_database.sql

# 4. Run Config Wizard
cd output\QWDE_Config_Wizard
QWDE_Config_Wizard.exe

# 5. Select:
#    Step 3: Database Type = MySQL
#    Enter MySQL credentials
#    Step 7: Save configuration

# 6. Run Python DDNS server
cd output\QWDE_Central_Server
QWDE_Central_Server.exe --server
```

---

**Last Updated:** 2026-03-27  
**Version:** 3.0  
**Status:** ✅ Both MySQL and SQLite Supported
