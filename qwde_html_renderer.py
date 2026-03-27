"""
QWDE Protocol - HTML Rendering Engine
Uses WebView2 (Edge/Chromium) or embedded browser for HTML rendering
Similar to C# WebView control
"""

import tkinter as tk
from tkinter import ttk
import os
import sys

# Try to import webview (cross-platform WebView)
try:
    import webview
    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False
    print("webview not installed. Install with: pip install pywebview")

# Alternative: Try to import PyQt5 WebEngine
try:
    from PyQt5.QtCore import QUrl
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


class HTMLRendererWindow:
    """
    Standalone HTML rendering window using WebView
    Similar to C# WebView control
    """
    
    def __init__(self, title="QWDE HTML Viewer", width=1024, height=768):
        self.title = title
        self.width = width
        self.height = height
        self.window = None
    
    def load_html(self, html_content: str):
        """Load HTML content string"""
        if not WEBVIEW_AVAILABLE:
            print("WebView not available")
            return
        
        # Create window
        self.window = webview.create_window(
            title=self.title,
            html=html_content,
            width=self.width,
            height=self.height
        )
        
        # Start renderer
        webview.start()
    
    def load_url(self, url: str):
        """Load URL"""
        if not WEBVIEW_AVAILABLE:
            print("WebView not available")
            return
        
        self.window = webview.create_window(
            title=self.title,
            url=url,
            width=self.width,
            height=self.height
        )
        
        webview.start()
    
    def load_file(self, filepath: str):
        """Load HTML file"""
        if not WEBVIEW_AVAILABLE:
            print("WebView not available")
            return
        
        file_url = f'file://{os.path.abspath(filepath)}'
        self.load_url(file_url)


class PyQtHTMLRenderer:
    """
    HTML Renderer using PyQt5 WebEngine
    Most similar to C# WebView control
    """
    
    def __init__(self):
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 not installed")
        
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.browser = QWebEngineView()
        self.browser.resize(1024, 768)
    
    def load_html(self, html_content: str):
        """Load HTML content"""
        self.browser.setHtml(html_content)
        self.browser.show()
        self.app.exec_()
    
    def load_url(self, url: str):
        """Load URL"""
        self.browser.setUrl(QUrl(url))
        self.browser.show()
        self.app.exec_()
    
    def load_file(self, filepath: str):
        """Load HTML file"""
        file_url = QUrl.fromLocalFile(filepath)
        self.load_url(file_url.toString())


class TkinterHTMLWidget:
    """
    Simple HTML-like widget for Tkinter
    Limited HTML support (basic tags only)
    Good for simple formatted text display
    """
    
    def __init__(self, parent):
        self.parent = parent
        self.text_widget = tk.Text(parent, wrap=tk.WORD)
        self.text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for basic HTML-like formatting
        self._setup_tags()
    
    def _setup_tags(self):
        """Setup text tags for HTML-like formatting"""
        self.text_widget.tag_configure('h1', font=('Arial', 24, 'bold'), spacing3=10)
        self.text_widget.tag_configure('h2', font=('Arial', 20, 'bold'), spacing3=8)
        self.text_widget.tag_configure('h3', font=('Arial', 16, 'bold'), spacing3=6)
        self.text_widget.tag_configure('bold', font=('Arial', 11, 'bold'))
        self.text_widget.tag_configure('italic', font=('Arial', 11, 'italic'))
        self.text_widget.tag_configure('code', font=('Consolas', 10), background='#f0f0f0')
        self.text_widget.tag_configure('link', foreground='#0066cc', underline=True)
    
    def load_html(self, html_content: str):
        """
        Load simplified HTML content
        Supports: h1, h2, h3, p, b, i, code, a, ul, li, br
        """
        self.text_widget.delete('1.0', tk.END)
        
        # Simple HTML parsing (very basic)
        import re
        
        # Remove script and style tags
        content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Process line by line
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            # Headers
            if line.startswith('<h1>'):
                text = re.sub(r'<h1>(.*?)</h1>', r'\1', line, flags=re.IGNORECASE)
                self.text_widget.insert(tk.END, text + '\n\n', 'h1')
            elif line.startswith('<h2>'):
                text = re.sub(r'<h2>(.*?)</h2>', r'\1', line, flags=re.IGNORECASE)
                self.text_widget.insert(tk.END, text + '\n\n', 'h2')
            elif line.startswith('<h3>'):
                text = re.sub(r'<h3>(.*?)</h3>', r'\1', line, flags=re.IGNORECASE)
                self.text_widget.insert(tk.END, text + '\n\n', 'h3')
            
            # Paragraphs
            elif line.startswith('<p>'):
                text = re.sub(r'<p>(.*?)</p>', r'\1', line, flags=re.IGNORECASE)
                # Process inline tags
                text = self._process_inline_html(text)
                self.text_widget.insert(tk.END, text + '\n\n')
            
            # Line breaks
            elif '<br>' in line:
                parts = line.split('<br>')
                for part in parts:
                    if part.strip():
                        text = self._process_inline_html(part.strip())
                        self.text_widget.insert(tk.END, text + '\n')
            
            # List items
            elif line.startswith('<li>'):
                text = re.sub(r'<li>(.*?)</li>', r'\1', line, flags=re.IGNORECASE)
                text = self._process_inline_html(text)
                self.text_widget.insert(tk.END, '  • ' + text + '\n')
            
            # Code blocks
            elif line.startswith('<pre>') or line.startswith('<code>'):
                text = re.sub(r'</?(pre|code)>', '', line, flags=re.IGNORECASE)
                self.text_widget.insert(tk.END, text + '\n', 'code')
            
            # Plain text (strip all tags)
            else:
                text = re.sub(r'<[^>]+>', '', line)
                if text.strip():
                    text = self._process_inline_html(text)
                    self.text_widget.insert(tk.END, text + '\n')
    
    def _process_inline_html(self, text: str) -> str:
        """Process inline HTML tags"""
        import re
        
        # Bold
        text = re.sub(r'<b>(.*?)</b>', r'\1', text, flags=re.IGNORECASE)
        text = re.sub(r'<strong>(.*?)</strong>', r'\1', text, flags=re.IGNORECASE)
        
        # Italic
        text = re.sub(r'<i>(.*?)</i>', r'\1', text, flags=re.IGNORECASE)
        text = re.sub(r'<em>(.*?)</em>', r'\1', text, flags=re.IGNORECASE)
        
        # Code
        text = re.sub(r'<code>(.*?)</code>', r'\1', text, flags=re.IGNORECASE)
        
        # Links (just show text)
        text = re.sub(r'<a[^>]*>(.*?)</a>', r'\1', text, flags=re.IGNORECASE)
        
        return text


def render_html_in_browser(html_content: str, title="QWDE HTML Viewer"):
    """
    Render HTML content in a browser-like window
    
    Args:
        html_content: HTML string to render
        title: Window title
    """
    if PYQT_AVAILABLE:
        # Use PyQt WebEngine (best option)
        renderer = PyQtHTMLRenderer()
        renderer.load_html(html_content)
    elif WEBVIEW_AVAILABLE:
        # Use pywebview (good alternative)
        renderer = HTMLRendererWindow(title=title)
        renderer.load_html(html_content)
    else:
        # Fallback to Tkinter widget (limited HTML)
        print("No full HTML renderer available. Using basic text widget.")
        return False
    
    return True


def create_html_viewer_widget(parent):
    """
    Create an HTML viewer widget that can be embedded in Tkinter app
    
    Returns:
        Widget that can display HTML content
    """
    # Use basic Tkinter widget (embedded in parent)
    return TkinterHTMLWidget(parent)


# Test the renderer
if __name__ == '__main__':
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>QWDE Test Page</title>
        <style>
            body { font-family: Arial; padding: 20px; }
            h1 { color: #00ff88; }
            .highlight { background: #ffff00; }
        </style>
    </head>
    <body>
        <h1>QWDE Protocol HTML Test</h1>
        <p>This is a <b>test page</b> for the HTML rendering engine.</p>
        <h2>Features</h2>
        <ul>
            <li>HTML rendering</li>
            <li>CSS support</li>
            <li>JavaScript (optional)</li>
        </ul>
        <h3>Code Example</h3>
        <pre><code>print("Hello QWDE!")</code></pre>
        <p>Visit <a href="https://secupgrade.com">secupgrade.com</a> for more info.</p>
    </body>
    </html>
    """
    
    print("""
╔═══════════════════════════════════════════════════════════╗
║      QWDE HTML Rendering Engine Test                      ║
╠═══════════════════════════════════════════════════════════╣
║  Available Renderers:                                     ║
║    • PyQt5 WebEngine (Best - like C# WebView)            ║
║    • pywebview (Good - cross-platform)                   ║
║    • Tkinter Widget (Basic - limited HTML)               ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    print(f"PyQt5 Available: {PYQT_AVAILABLE}")
    print(f"pywebview Available: {WEBVIEW_AVAILABLE}")
    print()
    
    if PYQT_AVAILABLE or WEBVIEW_AVAILABLE:
        print("Starting HTML renderer...")
        render_html_in_browser(test_html, "QWDE HTML Test")
    else:
        print("No full HTML renderer available.")
        print("Install one of:")
        print("  pip install PyQt5 PyQtWebEngine")
        print("  pip install pywebview")
