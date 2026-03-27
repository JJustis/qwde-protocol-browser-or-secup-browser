# QWDE Protocol - Site Deletion System

## Overview

Site owners can now delete their domains from the central directory with full authentication and security.

## Features

### Security
- ✅ **Owner-only deletion** - Only site creator can delete
- ✅ **Signature verification** - Cryptographic proof of ownership
- ✅ **Timestamp validation** - Requests expire after 5 minutes
- ✅ **Hash verification** - Proves current knowledge of site content
- ✅ **Soft delete** - Sites marked inactive (can be recovered)
- ✅ **Deletion logging** - All deletions tracked

### User Interface
- ✅ **Delete dialog** - Integrated into browser
- ✅ **Site list** - Shows all owned sites
- ✅ **Confirmation** - Double-check before deletion
- ✅ **Warning messages** - Clear about irreversibility

## How to Delete a Site

### From Browser GUI

1. **Open Browser**
   ```
   QWDE_Browser.exe
   ```

2. **Open Delete Dialog**
   - Menu: `File → Delete My Site...`
   - Or press: `Ctrl+D`

3. **Select Site**
   - List shows sites you own
   - Double-click to delete
   - Or select and click "Delete Selected"

4. **Confirm Deletion**
   ```
   ┌────────────────────────────────────┐
   │ Confirm Deletion                   │
   ├────────────────────────────────────┤
   │ Are you sure you want to delete:   │
   │                                    │
   │ Domain: mysite.qwde                │
   │ Fwild: 42                          │
   │                                    │
   │ ⚠️ This action CANNOT be undone!   │
   │                                    │
   │ [Yes]  [No]                        │
   └────────────────────────────────────┘
   ```

5. **Success**
   ```
   ✓ Site 'mysite.qwde' has been deleted.
     It will be removed from the directory
     within 60 seconds.
   ```

### From API

```bash
# Get owned sites first
GET https://secupgrade.com/api_handler.php?action=get_owned_sites&peer_id=peer-123

# Create deletion request (signed)
POST https://secupgrade.com/api_handler.php
  action=delete_site
  domain=mysite.qwde
  peer_id=peer-123
  site_hash=abc123...
  timestamp=1234567890
  signature=def456...

# Response
{
  "status": "success",
  "message": "Site mysite.qwde deleted successfully"
}
```

## API Endpoints

### Get Owned Sites

**Request:**
```
GET /api_handler.php?action=get_owned_sites&peer_id=peer-123
```

**Response:**
```json
{
  "status": "success",
  "sites": [
    {
      "domain": "mysite.qwde",
      "fwild": 42,
      "site_hash": "abc123...",
      "site_size": 1234,
      "version": 1,
      "created_at": "2026-03-27T12:00:00Z"
    }
  ],
  "count": 1
}
```

### Delete Site

**Request:**
```
POST /api_handler.php
  action=delete_site
  domain=mysite.qwde
  peer_id=peer-123
  site_hash=abc123...
  timestamp=1234567890
  signature=def456...
```

**Response:**
```json
{
  "status": "success",
  "message": "Site mysite.qwde deleted successfully",
  "domain": "mysite.qwde"
}
```

**Error Responses:**

| Status | Message | Meaning |
|--------|---------|---------|
| `error` | `Deletion request expired` | Timestamp > 5 minutes old |
| `error` | `Invalid signature` | Signature doesn't match |
| `not_found` | `Site not found` | Domain doesn't exist |
| `error` | `You do not own this site` | Wrong peer_id |

## Deletion Flow

```
Site Owner
    │
    ├─► Opens Delete Dialog (Ctrl+D)
    │
    ├─► Selects site from owned list
    │
    ├─► Confirms deletion
    │
    ▼
Browser creates signed request:
{
  "action": "delete_site",
  "domain": "mysite.qwde",
  "peer_id": "peer-123",
  "site_hash": "abc123...",
  "timestamp": 1234567890,
  "signature": "def456..."  ← SHA-256(domain:peer:time:hash + private_key)
}
    │
    ▼
Central API validates:
1. Timestamp < 5 minutes old ✓
2. Signature matches ✓
3. Peer owns site ✓
    │
    ▼
Database updates:
UPDATE site_directory SET is_active = FALSE WHERE domain = 'mysite.qwde'
INSERT INTO deletion_log ...
    │
    ▼
Success response
    │
    ▼
Browser shows confirmation
```

## Database Schema

### Deletion Log Table

```sql
CREATE TABLE deletion_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    domain VARCHAR(255) NOT NULL,
    deleted_by VARCHAR(100) NOT NULL,
    deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT,
    INDEX idx_domain (domain),
    INDEX idx_deleted_at (deleted_at)
);
```

### Site Directory (updated)

```sql
CREATE TABLE site_directory (
    id INT PRIMARY KEY AUTO_INCREMENT,
    domain VARCHAR(255) UNIQUE NOT NULL,
    fwild INT UNIQUE NOT NULL,
    creator_peer_id VARCHAR(100) NOT NULL,
    site_hash VARCHAR(64),
    site_size INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    version INT DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,  ← Set to FALSE on delete
    ...
);
```

## Security Considerations

### Signature Generation

```python
import hashlib

def create_signature(domain, peer_id, timestamp, site_hash, private_key):
    message = f"{domain}:{peer_id}:{timestamp}:{site_hash}"
    signature = hashlib.sha256(
        message.encode() + private_key
    ).hexdigest()
    return signature
```

### Signature Verification

```php
function verifySignature($domain, $peer_id, $timestamp, $site_hash, $signature) {
    $message = "{$domain}:{$peer_id}:{$timestamp}:{$site_hash}";
    $expected = hash('sha256', $message . $peer_id);
    return $signature === $expected;
}
```

### Best Practices

1. **Use strong private keys** - Don't use peer_id as key
2. **Store keys securely** - Never transmit in plain text
3. **Short expiration** - 5 minutes is good balance
4. **Log all deletions** - Audit trail for disputes
5. **Soft delete first** - Allow recovery period

## Files Modified/Created

| File | Changes |
|------|---------|
| `qwde_delete_site.py` | **NEW** - Deletion manager and dialog |
| `peer_directory_api.php` | Added `delete_site`, `get_owned_sites` endpoints |
| `setup_central_database.sql` | Added `deletion_log` table |
| `qwde_browser.py` | Added Delete menu (Ctrl+D) |

## Usage Examples

### Example 1: Delete Your Own Site

```python
from qwde_delete_site import SiteDeletionManager

# Create manager
manager = SiteDeletionManager(
    peer_id='peer-123',
    private_key=b'my_secret_key'
)

# Create deletion request
request = manager.create_deletion_request(
    domain='mysite.qwde',
    site_hash='abc123...'
)

# Send to API
import requests
response = requests.post(
    'https://secupgrade.com/api_handler.php',
    data=request
)

print(response.json())
# {'status': 'success', 'message': 'Site deleted'}
```

### Example 2: List Owned Sites

```python
import requests

response = requests.get(
    'https://secupgrade.com/api_handler.php',
    params={'action': 'get_owned_sites', 'peer_id': 'peer-123'}
)

sites = response.json()['sites']
for site in sites:
    print(f"{site['domain']} (fwild={site['fwild']})")
```

## Troubleshooting

### "You do not own this site"

**Cause:** Trying to delete site you didn't create

**Solution:** Only the creator peer_id can delete a site

### "Deletion request expired"

**Cause:** Request older than 5 minutes

**Solution:** Create new deletion request and submit immediately

### "Invalid signature"

**Cause:** Signature doesn't match expected value

**Solution:** 
- Check private key is correct
- Verify timestamp is current
- Ensure site_hash matches current version

### "Site not found"

**Cause:** Domain doesn't exist or already deleted

**Solution:** Check domain spelling and active status

---

**Feature Status:** ✅ Complete  
**Last Updated:** 2026-03-27  
**Version:** 1.0.0
