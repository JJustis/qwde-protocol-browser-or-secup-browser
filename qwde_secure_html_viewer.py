"""
QWDE Protocol - Secure HTML Viewer Widget
Shows source first, then user can toggle to render (security feature)
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import webbrowser
import os


class SecureHTMLViewer(tk.Frame):
    """
    Secure HTML viewer that:
    1. Shows source code by default
    2. User reviews source
    3. User clicks "Render" to view rendered HTML
    4. Can toggle back to source anytime
    """
    
    def __init__(self, parent, on_render_request=None):
        super().__init__(parent)
        
        self.on_render_request = on_render_request
        self.current_html = ""
        self.is_rendered = False
        self.renderer_window = None
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the viewer UI"""
        # Toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # Source view button (default)
        self.btn_source = ttk.Button(
            toolbar,
            text="📄 View Source",
            command=self._show_source,
            state='disabled'  # Already showing source
        )
        self.btn_source.pack(side=tk.LEFT, padx=2)
        
        # Render button
        self.btn_render = ttk.Button(
            toolbar,
            text="🌐 Render HTML",
            command=self._request_render,
            style='Accent.TButton'
        )
        self.btn_render.pack(side=tk.LEFT, padx=2)
        
        # Security warning label
        self.security_label = ttk.Label(
            toolbar,
            text="⚠️  Review source before rendering",
            foreground='#ffaa00'
        )
        self.security_label.pack(side=tk.LEFT, padx=10)
        
        # Stretchable space
        ttk.Frame(toolbar).pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        # External browser button
        self.btn_external = ttk.Button(
            toolbar,
            text="🚀 Open in Browser",
            command=self._open_external
        )
        self.btn_external.pack(side=tk.RIGHT, padx=2)
        
        # Main content area (source view)
        self.source_text = scrolledtext.ScrolledText(
            self,
            bg='#1a1a2e',
            fg='#00ff88',
            insertbackground='white',
            font=('Consolas', 10),
            wrap=tk.NONE
        )
        self.source_text.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(
            status_frame,
            text="Source View | Click 'Render HTML' to view rendered page",
            foreground='#888888'
        )
        self.status_label.pack(side=tk.LEFT, padx=10, pady=2)
        
        self.size_label = ttk.Label(
            status_frame,
            text="0 bytes",
            foreground='#888888'
        )
        self.size_label.pack(side=tk.RIGHT, padx=10, pady=2)
    
    def set_content(self, html_content: str):
        """Set HTML content to display"""
        self.current_html = html_content
        
        # Show in source view
        self.source_text.delete('1.0', tk.END)
        self.source_text.insert('1.0', html_content)
        
        # Update size
        size = len(html_content.encode('utf-8'))
        self.size_label.config(text=f"{size} bytes")
        
        # Reset state
        self.is_rendered = False
        self.btn_source.config(state='disabled')
        self.btn_render.config(state='normal')
        self.status_label.config(
            text="Source View | Review code before rendering"
        )
    
    def _show_source(self):
        """Show source view"""
        if self.renderer_window:
            try:
                self.renderer_window.destroy()
            except:
                pass
        
        self.is_rendered = False
        self.btn_source.config(state='disabled')
        self.btn_render.config(state='normal')
        self.status_label.config(
            text="Source View | Review code before rendering"
        )
    
    def _request_render(self):
        """Request to render HTML (with security confirmation)"""
        # Security confirmation dialog
        confirm = messagebox.askyesno(
            "Security Warning",
            "⚠️  HTML Rendering Security Notice\n\n"
            "You are about to render HTML content. This may execute:\n"
            "• JavaScript code\n"
            "• External resource requests\n"
            "• Tracking scripts\n\n"
            "Have you reviewed the source code?\n\n"
            "Recommendations:\n"
            "✓ Check for suspicious scripts\n"
            "✓ Verify external links\n"
            "✓ Look for tracking code\n\n"
            "Proceed with rendering?",
            icon='warning'
        )
        
        if not confirm:
            return
        
        # Check if external renderer is available
        if self.on_render_request:
            self.on_render_request(self.current_html)
        else:
            # Fallback: Open in external browser
            self._open_external()
    
    def _open_external(self):
        """Open HTML in external browser"""
        if not self.current_html:
            return
        
        # Save to temp file
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.html',
            delete=False,
            encoding='utf-8'
        )
        temp_file.write(self.current_html)
        temp_file.close()
        
        # Open in default browser
        webbrowser.open(f'file://{temp_file.name}')
        
        self.status_label.config(
            text="Opened in external browser"
        )


class SecureHTMLWindow(tk.Toplevel):
    """
    Standalone secure HTML viewer window
    """
    
    def __init__(self, parent, title="Secure HTML Viewer", html_content=""):
        super().__init__(parent)
        self.title(title)
        self.geometry("1200x800")
        
        self.viewer = SecureHTMLViewer(self, on_render_request=self._render_html)
        self.viewer.pack(fill=tk.BOTH, expand=True)
        
        if html_content:
            self.viewer.set_content(html_content)
    
    def _render_html(self, html_content):
        """Render HTML in external window"""
        # Try to import HTML renderer
        try:
            from qwde_html_renderer import render_html_in_browser
            render_html_in_browser(html_content, title=self.title())
        except Exception as e:
            messagebox.showerror(
                "Renderer Error",
                f"HTML renderer not available.\n\n"
                f"Install with:\n"
                f"  pip install PyQt5 PyQtWebEngine\n\n"
                f"Or:\n"
                f"  pip install pywebview\n\n"
                f"Error: {e}"
            )


def test_secure_viewer():
    """Test the secure HTML viewer"""
    root = tk.Tk()
    root.withdraw()
    
    test_html = """<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
    <style>
        body { background: #1a1a2e; color: #00ff88; font-family: Arial; }
        h1 { color: #00ff88; }
    </style>
</head>
<body>
    <h1>Secure HTML Viewer Test</h1>
    <p>This is a test page.</p>
    <script>
        // This script would run if rendered
        console.log("Script executed!");
    </script>
</body>
</html>"""
    
    window = SecureHTMLWindow(root, "Test Secure Viewer", test_html)
    root.mainloop()


if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════╗
║      QWDE Secure HTML Viewer                              ║
╠═══════════════════════════════════════════════════════════╣
║  Security Features:                                       ║
║    • Shows source code first                             ║
║    • User must confirm before rendering                  ║
║    • Security warning dialog                             ║
║    • Can toggle back to source anytime                   ║
║    • External browser fallback                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    test_secure_viewer()
