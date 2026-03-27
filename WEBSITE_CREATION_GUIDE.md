# QWDE Protocol - Website Creation Guide

## Overview

Create websites for the QWDE decentralized network. Sites are:
- **Encrypted** with QWDE encryption (HMAC + AES-GCM)
- **Stored locally** on your computer (peer)
- **Registered** with central directory (metadata only)
- **Served via P2P** to other peers

## Quick Start: Create Your First Site

### Method 1: Using Browser GUI (Easiest)

1. **Open Browser**
   ```bash
   QWDE_Browser.exe
   ```

2. **Click "Create Site"** button (or Ctrl+N)

3. **Write Your Content**
   ```html
   <!DOCTYPE html>
   <html>
   <head>
       <title>My QWDE Site</title>
   </head>
   <body>
       <h1>Welcome to My Site!</h1>
       <p>This is hosted on the QWDE protocol.</p>
   </body>
   </html>
   ```

4. **Enter Domain Name**
   - Example: `mysite`
   - Full domain: `mysite.qwde`

5. **Enable Encryption** (recommended)
   - ☑ Encrypt site data
   - ☑ Add error correction

6. **Click "Publish"**
   - Site registered with central directory
   - Assigned a `fwild` number
   - Available on P2P network

### Method 2: Programmatic Creation

```python
from qwde_peer_network import create_peer

# Create peer connection
peer = create_peer()

# Create site
result = peer.register_site(
    domain='mysite.qwde',
    site_data=b'<h1>Hello QWDE!</h1>'
)

print(f"Site created!")
print(f"  Domain: mysite.qwde")
print(f"  Fwild: {result['fwild']}")
print(f"  Version: {result['version']}")
```

---

## HTML Rendering Engine

The QWDE browser includes an **HTML rendering engine** similar to C# WebView control.

### Available Renderers

| Renderer | Quality | Install | Best For |
|----------|---------|---------|----------|
| **PyQt5 WebEngine** | ⭐⭐⭐⭐⭐ | `pip install PyQt5 PyQtWebEngine` | Full HTML/CSS/JS |
| **pywebview** | ⭐⭐⭐⭐ | `pip install pywebview` | Cross-platform |
| **Tkinter Widget** | ⭐⭐ | Built-in | Basic text display |

### Enable HTML Rendering

**Option 1: Install PyQt5 (Recommended)**
```bash
pip install PyQt5 PyQtWebEngine
```

**Option 2: Install pywebview**
```bash
pip install pywebview
```

**Option 3: Use Basic Text Display**
- No installation needed
- Shows HTML source code
- Good for debugging

### HTML Features Supported

| Feature | PyQt5 | pywebview | Tkinter |
|---------|-------|-----------|---------|
| **HTML5** | ✅ Full | ✅ Full | ⚠️ Basic |
| **CSS3** | ✅ Full | ✅ Full | ⚠️ Limited |
| **JavaScript** | ✅ Optional | ✅ Optional | ❌ No |
| **Images** | ✅ Yes | ✅ Yes | ❌ No |
| **Video/Audio** | ✅ Yes | ✅ Yes | ❌ No |
| **WebGL** | ✅ Yes | ✅ Yes | ❌ No |

---

## Website Templates

### Basic HTML Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{SITE_TITLE}}</title>
    <meta name="generator" content="QWDE Protocol">
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #1a1a2e;
            color: #00ff88;
        }
        h1 { color: #00ff88; }
        a { color: #00aaff; }
        .qwde-badge {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #16213e;
            padding: 10px 20px;
            border-radius: 25px;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <h1>My QWDE Site</h1>
    <p>Welcome to the decentralized web!</p>
    
    <div class="qwde-badge">
        🔐 Powered by QWDE Protocol
    </div>
</body>
</html>
```

### Blog Template

```html
<!DOCTYPE html>
<html>
<head>
    <title>My QWDE Blog</title>
    <style>
        body { font-family: Georgia, serif; max-width: 700px; margin: 0 auto; padding: 20px; }
        article { margin-bottom: 40px; }
        .date { color: #888; font-size: 0.9em; }
        h1 { color: #e94560; }
    </style>
</head>
<body>
    <header>
        <h1>My Decentralized Blog</h1>
        <p>Thoughts on the QWDE network</p>
    </header>
    
    <main>
        <article>
            <h2>First Post</h2>
            <p class="date">March 27, 2026</p>
            <p>This is my first post on the QWDE network!</p>
        </article>
        
        <article>
            <h2>Second Post</h2>
            <p class="date">March 28, 2026</p>
            <p>More content here...</p>
        </article>
    </main>
</body>
</html>
```

### Portfolio Template

```html
<!DOCTYPE html>
<html>
<head>
    <title>My Portfolio</title>
    <style>
        body { font-family: Arial; margin: 0; padding: 0; }
        .header { background: #1a1a2e; color: #00ff88; padding: 40px; text-align: center; }
        .projects { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; padding: 40px; }
        .project { border: 2px solid #00ff88; padding: 20px; border-radius: 8px; }
        .contact { background: #16213e; padding: 40px; text-align: center; }
    </style>
</head>
<body>
    <div class="header">
        <h1>John Doe</h1>
        <p>Developer on QWDE Protocol</p>
    </div>
    
    <div class="projects">
        <div class="project">
            <h3>Project 1</h3>
            <p>Description here...</p>
        </div>
        <div class="project">
            <h3>Project 2</h3>
            <p>Description here...</p>
        </div>
    </div>
    
    <div class="contact">
        <h2>Contact</h2>
        <p>qwde://contact.john</p>
    </div>
</body>
</html>
```

---

## Export to Standard Web Format

You can export QWDE sites to standard website folders:

### Export from Browser

1. **Open Site Creator**
2. **Write/Edit Content**
3. **Click "Export to Folder"**
4. **Choose Location**

### Output Structure

```
mysite.qwde/
├── index.html              # Main page
├── css/
│   └── style.css           # Styles
├── js/
│   └── main.js             # JavaScript
├── assets/
│   ├── image_0.png         # Extracted images
│   └── image_1.jpg
├── qwde_metadata.json      # QWDE metadata
└── original_content.txt    # Original content
```

### Use Exported Sites

- ✅ Upload to web hosting
- ✅ Open in any browser
- ✅ Edit in code editors
- ✅ Import back to QWDE

---

## Advanced Features

### Site Metadata

Each site includes:
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

### Encryption Options

| Option | Purpose | Recommended |
|--------|---------|-------------|
| **Encrypt Site** | QWDE encryption | ✅ Yes |
| **Error Correction** | Data integrity | ✅ Yes |
| **Ownership Token** | Deletion rights | ✅ Auto-generated |

### Update Your Site

1. **Open Site Creator**
2. **Load Existing Site** (File → Open)
3. **Edit Content**
4. **Click "Publish"** (updates version)

---

## Best Practices

### Content Guidelines

1. **Keep it Simple**
   - Start with basic HTML
   - Add CSS gradually
   - Test in browser

2. **Optimize Size**
   - Under 1MB recommended
   - Compress images
   - Minify CSS/JS

3. **Use UTF-8**
   - Always save as UTF-8
   - Include `<meta charset="UTF-8">`
   - Avoid special encodings

4. **Test Locally**
   - Export and test in standard browser
   - Check HTML validity
   - Verify links work

### Security

1. **Enable Encryption**
   - Protects content in transit
   - Verifies data integrity
   - Required for private sites

2. **Keep Ownership Token Safe**
   - Required for deletion
   - Stored locally
   - Don't share with others

3. **Use HTTPS for External Links**
   - Prevents MITM attacks
   - Verify certificates
   - Avoid HTTP links

---

## Troubleshooting

### Site Not Displaying

**Problem:** Site shows blank or errors

**Solutions:**
1. Check HTML is valid
2. Verify encoding is UTF-8
3. Try basic HTML first
4. Check browser console for errors

### HTML Not Rendering

**Problem:** Shows source code instead of rendered page

**Solutions:**
1. Install PyQt5: `pip install PyQt5 PyQtWebEngine`
2. Or install pywebview: `pip install pywebview`
3. Check renderer is enabled in settings

### Site Not Found

**Problem:** `qwde://mysite` shows "Not Found"

**Solutions:**
1. Verify site was published successfully
2. Check domain spelling
3. Try fwild lookup: `qwde://fwild:42`
4. Check peer is online

---

## Examples

### Example 1: Personal Homepage

```html
<!DOCTYPE html>
<html>
<head>
    <title>Alice's QWDE Home</title>
    <style>
        body { 
            font-family: Arial; 
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container { text-align: center; }
        h1 { font-size: 3em; color: #00ff88; }
        .links a { 
            color: #00aaff; 
            text-decoration: none; 
            margin: 0 10px;
            font-size: 1.2em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>👋 Hi, I'm Alice</h1>
        <p>Welcome to my corner of the QWDE network</p>
        <div class="links">
            <a href="qwde://blog.alice">Blog</a>
            <a href="qwde://projects.alice">Projects</a>
            <a href="qwde://contact.alice">Contact</a>
        </div>
    </div>
</body>
</html>
```

### Example 2: Decentralized Forum

```html
<!DOCTYPE html>
<html>
<head>
    <title>QWDE Community Forum</title>
    <style>
        body { font-family: Arial; max-width: 900px; margin: 0 auto; padding: 20px; }
        .post { border: 1px solid #00ff88; margin: 20px 0; padding: 20px; border-radius: 8px; }
        .author { color: #00ff88; font-weight: bold; }
        .timestamp { color: #888; font-size: 0.8em; }
        .new-post { background: #16213e; padding: 20px; margin-bottom: 20px; }
        textarea { width: 100%; height: 100px; }
        button { background: #00ff88; color: #1a1a2e; padding: 10px 20px; border: none; cursor: pointer; }
    </style>
</head>
<body>
    <h1>🗨️ QWDE Community Forum</h1>
    
    <div class="new-post">
        <h3>Create New Post</h3>
        <textarea placeholder="What's on your mind?"></textarea>
        <br><br>
        <button>Post</button>
    </div>
    
    <div class="post">
        <div class="author">user123</div>
        <div class="timestamp">2026-03-27 12:34</div>
        <p>Welcome to the forum!</p>
    </div>
    
    <div class="post">
        <div class="author">alice</div>
        <div class="timestamp">2026-03-27 13:45</div>
        <p>Excited to be on QWDE!</p>
    </div>
</body>
</html>
```

---

## Resources

### Documentation
- [SUPPORTED_FILE_TYPES.md](SUPPORTED_FILE_TYPES.md) - File format support
- [README.md](README.md) - Complete system docs
- [ENHANCED_ENCRYPTION_GUIDE.md](ENHANCED_ENCRYPTION_GUIDE.md) - Encryption details

### Tools
- **Site Creator** - Built into browser
- **Export Tool** - Export to standard web format
- **HTML Renderer** - PyQt5/pywebview

### Community
- Share your sites: `qwde://showcase`
- Get help: `qwde://support`
- Plugin repository: `qwde://plugins`

---

**Last Updated:** 2026-03-27  
**Version:** 3.0  
**Status:** ✅ Production Ready
