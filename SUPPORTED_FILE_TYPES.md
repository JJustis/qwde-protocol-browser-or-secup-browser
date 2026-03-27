# QWDE Browser - Supported File Types & Content

## Overview

The QWDE Browser is a **custom protocol browser** designed for the decentralized QWDE network. It's not a traditional web browser like Chrome or Firefox - it's specialized for QWDE protocol content.

## Content Types

### 1. QWDE Protocol Sites (`qwde://`)

**Primary Content Type**

```
Protocol: qwde://
Example: qwde://mysite.qwde
Alternative: qwde://fwild:42
```

**What Runs:**
- ✅ **HTML Content** - Displayed as text/source
- ✅ **Plain Text** - `.txt` files
- ✅ **Markdown** - `.md` files
- ✅ **JSON** - `.json` files
- ✅ **XML** - `.xml` files
- ✅ **Binary Data** - Shown as hex dump
- ✅ **Encrypted Content** - QWDE encrypted sites

**What Doesn't Run:**
- ❌ **JavaScript** - Can be blocked by plugin
- ❌ **ActiveX/Flash** - Not supported
- ❌ **Java Applets** - Not supported
- ❌ **WebAssembly** - Not supported

**Display Method:**
- Content is displayed in a **text viewer** (ScrolledText widget)
- HTML is shown as **source code**, not rendered
- Syntax highlighting available via plugins

---

### 2. HTTP/HTTPS Sites (Standard Web)

**Secondary Content Type**

```
Protocol: http:// or https://
Example: https://example.com
```

**What Runs:**
- ✅ **HTML** - Downloaded and displayed as text
- ✅ **Plain Text** - `.txt` files
- ✅ **JSON/XML** - API responses
- ✅ **CSS** - Stylesheets (as text)

**What Doesn't Render:**
- ❌ **No HTML Rendering** - Shows source, not rendered page
- ❌ **No JavaScript Execution** - Code shown but not run
- ❌ **No Images** - Binary data shown as hex
- ❌ **No Multimedia** - No video/audio playback

**Use Case:**
- View source of web pages
- Download text-based content
- API testing/debugging

---

### 3. Local Files

**Tertiary Content Type**

**Supported Formats:**
```
.txt   - Plain text
.html  - HTML source
.htm   - HTML source
.md    - Markdown
.json  - JSON data
.xml   - XML data
.css   - CSS stylesheets
.js    - JavaScript (view only)
.py    - Python source
.qwde  - QWDE site package
.*     - Any text file
```

**How to Open:**
- Menu: `File → Open...` (Ctrl+O)
- Drag and drop (if enabled)

---

## File Extensions

### Natively Supported

| Extension | Type | Display |
|-----------|------|---------|
| `.qwde` | QWDE Site | Decrypted & displayed |
| `.txt` | Plain Text | Text view |
| `.html` | HTML | Source view |
| `.htm` | HTML | Source view |
| `.md` | Markdown | Text view |
| `.json` | JSON | Formatted text |
| `.xml` | XML | Formatted text |
| `.css` | CSS | Text view |
| `.js` | JavaScript | Text view |
| `.py` | Python | Text view |
| `.log` | Log file | Text view |
| `.cfg` | Config | Text view |
| `.ini` | Config | Text view |

### Binary Files (Hex View)

| Extension | Type | Display |
|-----------|------|---------|
| `.png` | Image | Hex dump |
| `.jpg` | Image | Hex dump |
| `.gif` | Image | Hex dump |
| `.exe` | Executable | Hex dump |
| `.zip` | Archive | Hex dump |
| `.dat` | Data | Hex dump |
| `.bin` | Binary | Hex dump |

---

## Plugin-Enhanced Content

Plugins can extend content support:

### With Plugins Installed

| Plugin | Adds Support For |
|--------|-----------------|
| **Markdown Viewer** | `.md` rendered view |
| **JSON Formatter** | Pretty-print JSON |
| **XML Viewer** | Tree view for XML |
| **Image Viewer** | Display images |
| **PDF Viewer** | Display PDFs |
| **Code Highlighter** | Syntax highlighting |

### Example: Markdown Viewer Plugin

```python
# plugins/markdown_viewer.py
from qwde_browser import QWDEPlugin
import markdown

class MarkdownViewerPlugin(QWDEPlugin):
    name = "Markdown Viewer"
    version = "1.0.0"
    description = "Render Markdown files"
    
    def on_page_load(self, url: str, content: str) -> str:
        if url.endswith('.md'):
            # Convert Markdown to HTML
            html = markdown.markdown(content)
            return f"<html><body>{html}</body></html>"
        return content
```

---

## Site Creator Output

When you create a site in the browser, you can export as:

### Website Folder Export

```
mysite.qwde/
├── index.html          # Main page
├── css/
│   └── style.css       # Styles
├── js/
│   └── main.js         # JavaScript
├── assets/
│   ├── image_0.png     # Images
│   └── image_1.jpg
├── qwde_metadata.json  # Metadata
└── original_content.txt
```

**These files can:**
- ✅ Be opened in standard web browsers
- ✅ Be uploaded to web hosts
- ✅ Be viewed in any text editor
- ✅ Be imported back into QWDE browser

---

## Content Restrictions

### Security Features

| Feature | Purpose |
|---------|---------|
| **No JavaScript Execution** | Prevents XSS attacks |
| **No ActiveX/Flash** | Prevents malware |
| **No Auto-Downloads** | Prevents drive-by downloads |
| **Plugin Sandboxing** | Plugins can't access file system |
| **HTTPS-Only Mode** | Prevents MITM attacks |
| **Certificate Verification** | Validates SSL certs |

### Plugin Content Filtering

Plugins can block:
- ❌ Scripts (`<script>` tags)
- ❌ Iframes (`<iframe>` tags)
- ❌ Trackers (analytics domains)
- ❌ Ads (ad service domains)
- ❌ Cookies (if enabled)

---

## Content Size Limits

| Type | Limit |
|------|-------|
| **QWDE Site** | No hard limit (practical: 100MB) |
| **HTTP Download** | No hard limit |
| **Text Display** | ~10MB recommended |
| **Binary Display** | ~1MB recommended |

---

## Encoding Support

### Text Encodings

| Encoding | Supported |
|----------|-----------|
| UTF-8 | ✅ Yes (default) |
| UTF-16 | ✅ Yes |
| ASCII | ✅ Yes |
| Latin-1 | ✅ Yes |
| Windows-1252 | ✅ Yes |

### Automatic Detection

Browser attempts to detect encoding:
1. Check BOM (Byte Order Mark)
2. Check HTTP headers
3. Check meta tags
4. Fallback to UTF-8

---

## Special QWDE Features

### Encrypted Sites

QWDE sites are encrypted with:
- **Layer 1:** QWDE custom encryption
- **Layer 2:** AES-GCM per quadrant
- **Layer 3:** AES-GCM outer layer
- **Layer 4:** HMAC-SHA256 authentication

**Decryption happens automatically** when browsing `qwde://` URLs.

### Site Metadata

Each QWDE site includes:
```json
{
  "domain": "mysite.qwde",
  "fwild": 42,
  "version": 1,
  "creator_peer_id": "peer-123",
  "site_hash": "abc123...",
  "site_size": 1234,
  "created_at": "2026-03-27T12:00:00Z",
  "ownership_token": "xyz789..."
}
```

---

## Comparison Table

| Feature | QWDE Browser | Chrome | Firefox |
|---------|-------------|--------|---------|
| **QWDE Protocol** | ✅ Native | ❌ No | ❌ No |
| **HTTP/HTTPS** | ✅ View source | ✅ Full render | ✅ Full render |
| **JavaScript** | ❌ View only | ✅ Execute | ✅ Execute |
| **HTML Render** | ❌ Source only | ✅ Full | ✅ Full |
| **Images** | ❌ Hex view | ✅ Display | ✅ Display |
| **Plugins** | ✅ Python | ❌ Extensions | ❌ Extensions |
| **Encryption** | ✅ QWDE + AES-GCM | ✅ TLS | ✅ TLS |
| **P2P** | ✅ Native | ❌ No | ❌ No |

---

## Best Practices

### For Site Creators

1. **Use Text-Based Content**
   - HTML, Markdown, Plain text
   - Avoid large binary files

2. **Optimize for Text Display**
   - Keep sites under 1MB
   - Use simple HTML structure
   - Include plain text fallback

3. **Test in Browser**
   - Verify content displays correctly
   - Check encoding is UTF-8
   - Test with plugins enabled

### For Plugin Developers

1. **Content Modification**
   - Use `on_page_load()` to modify content
   - Return modified string
   - Handle errors gracefully

2. **Request Blocking**
   - Use `on_request()` to block URLs
   - Return `False` to block
   - Log blocked requests

3. **Settings UI**
   - Use `get_settings_ui()` for configuration
   - Save settings to file
   - Load on plugin init

---

## Future Content Support

### Planned Features

- [ ] Markdown rendering (plugin)
- [ ] Image display (plugin)
- [ ] PDF viewing (plugin)
- [ ] Syntax highlighting (built-in)
- [ ] Full HTML rendering (optional)
- [ ] WebAssembly support (experimental)

### Request Content Support

To request support for new file types:
1. Create plugin for the format
2. Submit to plugin repository
3. Or request via GitHub issues

---

**Last Updated:** 2026-03-27  
**Version:** 3.0  
**Status:** ✅ Production Ready
