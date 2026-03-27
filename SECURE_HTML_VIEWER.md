# QWDE Secure HTML Viewer - Security-First Rendering

## Overview

The QWDE browser includes a **secure HTML viewer** that prioritizes security by showing source code first, then allowing the user to optionally render the HTML after review.

## Security Flow

```
HTML Content Loaded
    │
    ▼
┌─────────────────────────────────────────┐
│  Step 1: Show Source Code               │
│  • User can review HTML/JS/CSS         │
│  • Check for malicious code            │
│  • Verify external links               │
│  • Look for tracking scripts           │
└─────────────────────────────────────────┘
    │
    │ User clicks "Render HTML"
    ▼
┌─────────────────────────────────────────┐
│  Step 2: Security Confirmation          │
│  • Warning dialog appears              │
│  • Lists potential risks               │
│  • User must confirm                   │
│  • Can cancel and stay in source view  │
└─────────────────────────────────────────┘
    │
    │ User confirms
    ▼
┌─────────────────────────────────────────┐
│  Step 3: Render HTML                    │
│  • Opens in rendering window           │
│  • Full HTML/CSS/JS support            │
│  • Can toggle back to source anytime   │
│  • External browser option available   │
└─────────────────────────────────────────┘
```

## Features

### Source-First Display

**Always shows source code first:**
- HTML displayed as text
- Syntax highlighting (if available)
- Line numbers for easy reference
- Search functionality

### Security Confirmation

**Before rendering, shows warning:**
```
┌────────────────────────────────────────────┐
│ ⚠️  HTML Rendering Security Notice         │
├────────────────────────────────────────────┤
│ You are about to render HTML content.     │
│ This may execute:                          │
│ • JavaScript code                          │
│ • External resource requests               │
│ • Tracking scripts                         │
│                                            │
│ Have you reviewed the source code?         │
│                                            │
│ Recommendations:                           │
│ ✓ Check for suspicious scripts             │
│ ✓ Verify external links                    │
│ ✓ Look for tracking code                   │
│                                            │
│ Proceed with rendering?                    │
│                                            │
│ [Yes]  [No]                                │
└────────────────────────────────────────────┘
```

### Toggle Controls

**Toolbar buttons:**
- 📄 **View Source** - Return to source view
- 🌐 **Render HTML** - Render the page
- 🚀 **Open in Browser** - Open in external browser

### Security Indicators

**Status bar shows:**
- Current view mode (Source/Rendered)
- Security warnings
- Content size
- External resource warnings

## Usage

### Automatic Detection

The secure viewer automatically activates when:
1. HTML content is detected (`<!DOCTYPE` or `<html>`)
2. Content is loaded from QWDE network
3. HTML file is opened locally

### Manual Controls

**In secure viewer window:**

| Button | Action |
|--------|--------|
| 📄 View Source | Show HTML source code |
| 🌐 Render HTML | Render HTML (with confirmation) |
| 🚀 Open in Browser | Open in default browser |

**Keyboard Shortcuts:**
- `F5` - Toggle source/render
- `Ctrl+R` - Render HTML
- `Ctrl+U` - View source
- `Ctrl+O` - Open in external browser

## Security Checklist

Before clicking "Render HTML", check for:

### Suspicious Scripts
```html
<!-- Check for: -->
<script src="http://suspicious-domain.com/tracker.js"></script>
<script>eval(atob("base64-encoded-malicious-code"));</script>
```

### External Resources
```html
<!-- Verify these domains are trusted: -->
<img src="https://trusted-cdn.com/image.png">
<link rel="stylesheet" href="https://unknown-domain.com/style.css">
```

### Tracking Code
```html
<!-- Look for tracking pixels/scripts: -->
<img src="https://analytics.com/pixel.gif?user=123">
<script>gtag('event', 'track_user');</script>
```

### Iframe Embeds
```html
<!-- Check embedded content: -->
<iframe src="https://unknown-site.com/embed"></iframe>
```

## Installation Requirements

### Option 1: PyQt5 WebEngine (Recommended)

```bash
pip install PyQt5 PyQtWebEngine
```

**Features:**
- Full HTML5 rendering
- CSS3 support
- JavaScript execution (optional)
- WebGL support
- Best performance

### Option 2: pywebview

```bash
pip install pywebview
```

**Features:**
- Cross-platform
- Uses system WebView
- Good HTML/CSS support
- Lightweight

### Option 3: External Browser Only

**No installation required:**
- Source view works without dependencies
- "Open in Browser" uses your default browser
- No rendering in QWDE browser itself

## API Usage

### Programmatic Use

```python
from qwde_secure_html_viewer import SecureHTMLWindow

# Create secure viewer
viewer = SecureHTMLWindow(
    parent=browser_window,
    title="My QWDE Site",
    html_content="<h1>Hello World</h1>"
)

# Viewer opens with source shown first
# User must confirm before rendering
```

### Integration with Browser

The secure viewer is automatically used when:
```python
# In qwde_browser.py
def _display_site(self, site, url):
    content = site['site_data'].decode()
    
    # Check if HTML
    if content.startswith('<!DOCTYPE') or content.startswith('<html'):
        # Use secure viewer
        self._display_secure_html(content, url)
    else:
        # Show as plain text
        self.content_display.insert('1.0', content)
```

## Comparison: Secure vs Standard Viewers

| Feature | Secure Viewer | Standard Browser |
|---------|--------------|------------------|
| **Source First** | ✅ Yes | ❌ No |
| **Security Confirm** | ✅ Yes | ❌ No |
| **Toggle Source** | ✅ Yes | ❌ No |
| **External Option** | ✅ Yes | N/A |
| **Auto-Render** | ❌ No | ✅ Yes |
| **JS Execution** | ⚠️ After confirm | ✅ Always |
| **Security Warning** | ✅ Yes | ❌ No |

## Best Practices

### For Users

1. **Always review source first**
   - Check for suspicious code
   - Verify external resources
   - Look for tracking scripts

2. **Only render trusted sites**
   - Sites you created
   - Sites from known creators
   - Sites with verified ownership

3. **Use external browser for complex sites**
   - Better security isolation
   - Full browser security features
   - Easier to close if suspicious

### For Site Creators

1. **Minimize external resources**
   - Host assets locally
   - Use trusted CDNs only
   - Avoid third-party scripts

2. **Include security notice**
   ```html
   <!-- 
     QWDE Site Security Info:
     - No external scripts
     - No tracking code
     - All assets hosted locally
   -->
   ```

3. **Provide plain text fallback**
   ```html
   <noscript>
     This site works without JavaScript.
   </noscript>
   ```

## Troubleshooting

### "Renderer not available" Error

**Cause:** PyQt5 or pywebview not installed

**Solution:**
```bash
# Install renderer
pip install PyQt5 PyQtWebEngine

# Or use external browser option
# Click "Open in Browser" button
```

### HTML Shows as Source Only

**Cause:** Content not detected as HTML

**Solution:**
- Ensure HTML starts with `<!DOCTYPE html>` or `<html>`
- Check file encoding is UTF-8
- Try "Open in Browser" button

### Rendering Slow

**Cause:** Large HTML file or complex CSS/JS

**Solutions:**
- Use external browser for better performance
- Optimize HTML/CSS
- Reduce JavaScript usage

## Security Audit Log

The secure viewer logs all rendering actions:

```
[12:34:56] HTML loaded: qwde://mysite.qwde
[12:34:57] Source view displayed
[12:35:10] User clicked "Render HTML"
[12:35:10] Security confirmation shown
[12:35:15] User confirmed rendering
[12:35:15] HTML rendered in viewer
```

## Version History

### Version 1.0 (Current)
- ✅ Source-first display
- ✅ Security confirmation dialog
- ✅ Toggle source/render
- ✅ External browser option
- ✅ Automatic HTML detection

### Planned Features
- Syntax highlighting for source
- Search in source code
- Security score/rating
- Malware detection
- Script blocking options

---

**Last Updated:** 2026-03-27  
**Version:** 1.0  
**Status:** ✅ Production Ready
