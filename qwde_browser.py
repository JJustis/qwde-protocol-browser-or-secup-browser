"""
QWDE Protocol - Browser GUI with Site Creator, Plugins, and Security Features
Full-featured browser with notepad clone, plugin system, and encryption indicators
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, colorchooser
import threading
import time
from datetime import datetime
from typing import Optional, List, Dict, Callable, Any
import base64
import hashlib
import json
import os
import ssl
import urllib.request
import urllib.error
import re

from qwde_ddns_server import SiteInfo
from qwde_peer_network import QWDEPeer, create_peer
from qwde_encryption import EncryptionManager

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ==================== Plugin System ====================

class QWDEPlugin:
    """Base class for QWDE Browser plugins"""
    
    name = "Base Plugin"
    version = "1.0.0"
    description = "Base plugin class"
    author = "Unknown"
    
    def __init__(self, browser):
        self.browser = browser
        self.enabled = False
        self.settings = {}
    
    def on_enable(self):
        """Called when plugin is enabled"""
        self.enabled = True
    
    def on_disable(self):
        """Called when plugin is disabled"""
        self.enabled = False
    
    def on_page_load(self, url: str, content: str) -> str:
        """Called when a page is loaded. Return modified content."""
        return content
    
    def on_request(self, url: str) -> bool:
        """Called before a request is made. Return False to block."""
        return True
    
    def get_settings_ui(self, parent) -> Optional[tk.Widget]:
        """Return settings UI widget if plugin has settings"""
        return None
    
    def save_settings(self, settings: dict):
        """Save plugin settings"""
        self.settings = settings
    
    def load_settings(self) -> dict:
        """Load plugin settings"""
        return self.settings


class ScriptBlockerPlugin(QWDEPlugin):
    """Plugin to block scripts from running"""
    
    name = "Script Blocker"
    version = "1.0.0"
    description = "Block JavaScript and other scripts from loading"
    author = "QWDE Team"
    
    def __init__(self, browser):
        super().__init__(browser)
        self.block_scripts = True
        self.block_iframes = False
        self.custom_filters = []
    
    def on_page_load(self, url: str, content: str) -> str:
        """Remove scripts from content"""
        if not self.enabled or not self.block_scripts:
            return content
        
        # Remove script tags
        modified = re.sub(r'<script[^>]*>.*?</script>', '<!-- Script blocked by QWDE -->', 
                         content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove event handlers
        modified = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', modified)
        
        if self.block_iframes:
            modified = re.sub(r'<iframe[^>]*>.*?</iframe>', '<!-- Iframe blocked -->', 
                             modified, flags=re.DOTALL | re.IGNORECASE)
        
        return modified
    
    def get_settings_ui(self, parent) -> tk.Widget:
        """Create settings UI"""
        frame = ttk.LabelFrame(parent, text="Script Blocker Settings")
        
        ttk.Checkbutton(frame, text="Block Scripts", 
                       variable=tk.BooleanVar(value=self.block_scripts),
                       command=self._toggle_scripts).pack(padx=5, pady=2)
        
        ttk.Checkbutton(frame, text="Block Iframes",
                       variable=tk.BooleanVar(value=self.block_iframes),
                       command=self._toggle_iframes).pack(padx=5, pady=2)
        
        return frame
    
    def _toggle_scripts(self):
        self.block_scripts = not self.block_scripts
    
    def _toggle_iframes(self):
        self.block_iframes = not self.block_iframes


class AdBlockerPlugin(QWDEPlugin):
    """Plugin to block ads and trackers"""
    
    name = "Ad Blocker"
    version = "1.0.0"
    description = "Block advertisements and tracking scripts"
    author = "QWDE Team"
    
    def __init__(self, browser):
        super().__init__(browser)
        self.ad_patterns = [
            r'adservice\.', r'googleads', r'doubleclick',
            r'facebook.*pixel', r'analytics', r'tracking'
        ]
    
    def on_request(self, url: str) -> bool:
        """Block ad requests"""
        if not self.enabled:
            return True
        
        for pattern in self.ad_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                logger.info(f"Blocked ad request: {url}")
                return False
        return True


class PrivacyPlugin(QWDEPlugin):
    """Plugin for enhanced privacy"""
    
    name = "Privacy Guard"
    version = "1.0.0"
    description = "Enhance privacy by blocking cookies and fingerprinting"
    author = "QWDE Team"
    
    def __init__(self, browser):
        super().__init__(browser)
        self.block_cookies = True
        self.block_storage = True
        self.spoof_user_agent = True
    
    def on_request(self, url: str) -> bool:
        """Check privacy settings"""
        if not self.enabled:
            return True
        return True  # Allow request but modify headers
    
    def get_settings_ui(self, parent) -> tk.Widget:
        """Create settings UI"""
        frame = ttk.LabelFrame(parent, text="Privacy Settings")
        
        ttk.Checkbutton(frame, text="Block Cookies",
                       variable=tk.BooleanVar(value=self.block_cookies)).pack(padx=5, pady=2)
        
        ttk.Checkbutton(frame, text="Block Local Storage",
                       variable=tk.BooleanVar(value=self.block_storage)).pack(padx=5, pady=2)
        
        ttk.Checkbutton(frame, text="Spoof User Agent",
                       variable=tk.BooleanVar(value=self.spoof_user_agent)).pack(padx=5, pady=2)
        
        return frame


class PluginManager:
    """Manages browser plugins"""
    
    def __init__(self, browser):
        self.browser = browser
        self.plugins: Dict[str, QWDEPlugin] = {}
        self.plugin_dir = os.path.join(os.path.dirname(__file__), 'plugins')
        self.enabled_plugins: set = set()
        
        # Load built-in plugins
        self._register_builtin_plugins()
    
    def _register_builtin_plugins(self):
        """Register built-in plugins"""
        builtin_plugins = [
            ScriptBlockerPlugin,
            AdBlockerPlugin,
            PrivacyPlugin
        ]
        
        for plugin_class in builtin_plugins:
            plugin = plugin_class(self.browser)
            self.plugins[plugin.name] = plugin
    
    def load_plugins_from_dir(self):
        """Load plugins from plugin directory"""
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir)
            return
        
        for filename in os.listdir(self.plugin_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                try:
                    import importlib.util
                    spec = importlib.util.spec_from_file_location(
                        filename[:-3],
                        os.path.join(self.plugin_dir, filename)
                    )
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Find plugin class
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type) and issubclass(attr, QWDEPlugin) and attr != QWDEPlugin:
                            plugin = attr(self.browser)
                            self.plugins[plugin.name] = plugin
                            logger.info(f"Loaded plugin: {plugin.name}")
                except Exception as e:
                    logger.error(f"Failed to load plugin {filename}: {e}")
    
    def enable_plugin(self, name: str) -> bool:
        """Enable a plugin"""
        if name in self.plugins:
            self.plugins[name].on_enable()
            self.enabled_plugins.add(name)
            return True
        return False
    
    def disable_plugin(self, name: str) -> bool:
        """Disable a plugin"""
        if name in self.plugins:
            self.plugins[name].on_disable()
            self.enabled_plugins.discard(name)
            return True
        return False
    
    def is_enabled(self, name: str) -> bool:
        """Check if plugin is enabled"""
        return name in self.enabled_plugins
    
    def get_plugin(self, name: str) -> Optional[QWDEPlugin]:
        """Get plugin by name"""
        return self.plugins.get(name)
    
    def on_page_load(self, url: str, content: str) -> str:
        """Apply all enabled plugins to page content"""
        modified_content = content
        for plugin in self.plugins.values():
            if plugin.enabled:
                try:
                    modified_content = plugin.on_page_load(url, modified_content)
                except Exception as e:
                    logger.error(f"Plugin {plugin.name} error: {e}")
        return modified_content
    
    def on_request(self, url: str) -> bool:
        """Check if request should be allowed"""
        for plugin in self.plugins.values():
            if plugin.enabled:
                try:
                    if not plugin.on_request(url):
                        return False
                except Exception as e:
                    logger.error(f"Plugin {plugin.name} error: {e}")
        return True
    
    def get_settings_window(self) -> tk.Toplevel:
        """Create plugin settings window"""
        window = tk.Toplevel(self.browser)
        window.title("Plugin Settings")
        window.geometry("600x500")
        window.transient(self.browser)
        
        # Plugin list
        list_frame = ttk.LabelFrame(window, text="Installed Plugins")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create treeview
        columns = ('name', 'version', 'status', 'description')
        tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        tree.heading('name', text='Name')
        tree.heading('version', text='Version')
        tree.heading('status', text='Status')
        tree.heading('description', text='Description')
        
        tree.column('name', width=150)
        tree.column('version', width=80)
        tree.column('status', width=80)
        tree.column('description', width=250)
        
        # Populate with plugins
        for plugin in self.plugins.values():
            status = "Enabled" if plugin.enabled else "Disabled"
            tree.insert('', 'end', values=(
                plugin.name,
                plugin.version,
                status,
                plugin.description
            ))
        
        tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def toggle_plugin():
            selection = tree.selection()
            if selection:
                item = tree.item(selection[0])
                plugin_name = item['values'][0]
                plugin = self.get_plugin(plugin_name)
                
                if plugin:
                    if plugin.enabled:
                        self.disable_plugin(plugin_name)
                        tree.item(selection[0], values=(
                            plugin.name, plugin.version, "Disabled", plugin.description
                        ))
                    else:
                        self.enable_plugin(plugin_name)
                        tree.item(selection[0], values=(
                            plugin.name, plugin.version, "Enabled", plugin.description
                        ))
        
        ttk.Button(btn_frame, text="Enable/Disable", command=toggle_plugin).pack(side=tk.LEFT, padx=5)
        
        def show_plugin_settings():
            selection = tree.selection()
            if selection:
                item = tree.item(selection[0])
                plugin_name = item['values'][0]
                plugin = self.get_plugin(plugin_name)
                
                if plugin and plugin.get_settings_ui:
                    settings_window = tk.Toplevel(window)
                    settings_window.title(f"{plugin_name} Settings")
                    settings_ui = plugin.get_settings_ui(settings_window)
                    if settings_ui:
                        settings_ui.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Settings", command=show_plugin_settings).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="Open Plugin Folder", 
                  command=lambda: os.startfile(self.plugin_dir)).pack(side=tk.RIGHT, padx=5)
        
        return window


# ==================== Site Creator ====================

class SiteCreatorDialog(tk.Toplevel):
    """Site creation dialog with notepad clone"""
    
    def __init__(self, parent, peer: QWDEPeer = None):
        super().__init__(parent)
        self.title("📝 QWDE Site Creator")
        self.geometry("900x700")
        self.transient(parent)
        self.grab_set()
        
        self.peer = peer
        self.result = None
        
        # State
        self.current_file = None
        self.modified = False
        self.word_count = 0
        self.char_count = 0
        
        self._create_ui()
        self._create_menu()
        self._bind_events()
    
    def _create_ui(self):
        """Create the UI"""
        # Toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="📄 New", width=8, command=self._new_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📂 Open", width=8, command=self._open_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="💾 Save", width=8, command=self._save_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📤 Publish", width=8, command=self._publish).pack(side=tk.LEFT, padx=10)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Label(toolbar, text="Domain:").pack(side=tk.LEFT, padx=5)
        self.domain_entry = ttk.Entry(toolbar, width=30)
        self.domain_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(toolbar, text=".qwde").pack(side=tk.LEFT)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Main editor area
        editor_frame = ttk.Frame(self)
        editor_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Line numbers
        line_numbers = tk.Text(editor_frame, width=4, padx=3, takefocus=0,
                              border=0, background='#2d2d2d', foreground='#888888',
                              state='disabled', wrap='none')
        line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # Text editor
        self.editor = scrolledtext.ScrolledText(
            editor_frame,
            wrap=tk.NONE,
            bg='#1a1a2e',
            fg='#00ff88',
            insertbackground='white',
            font=('Consolas', 11),
            undo=True
        )
        self.editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Sync line numbers with editor
        def sync_lines(*args):
            line_numbers.config(state='normal')
            line_numbers.delete('1.0', tk.END)
            line_count = int(self.editor.index('end-1c').split('.')[0])
            line_numbers.insert('1.0', '\n'.join(str(i) for i in range(1, line_count + 1)))
            line_numbers.config(state='disabled')
        
        self.editor.bind('<KeyRelease>', lambda e: self._update_stats())
        self.editor.bind('<MouseWheel>', lambda e: sync_lines())
        self.editor.bind('<ButtonRelease>', lambda e: sync_lines())
        
        # Right panel with info
        info_frame = ttk.LabelFrame(self, text="📊 Site Info")
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        info_grid = ttk.Frame(info_frame)
        info_grid.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(info_grid, text="Characters:").grid(row=0, column=0, sticky='w', padx=5)
        self.char_label = ttk.Label(info_grid, text="0")
        self.char_label.grid(row=0, column=1, sticky='w', padx=20)
        
        ttk.Label(info_grid, text="Words:").grid(row=0, column=2, sticky='w', padx=20)
        self.word_label = ttk.Label(info_grid, text="0")
        self.word_label.grid(row=0, column=3, sticky='w', padx=20)
        
        ttk.Label(info_grid, text="Lines:").grid(row=0, column=4, sticky='w', padx=20)
        self.line_label = ttk.Label(info_grid, text="0")
        self.line_label.grid(row=0, column=5, sticky='w', padx=20)
        
        ttk.Label(info_grid, text="Size:").grid(row=0, column=6, sticky='w', padx=20)
        self.size_label = ttk.Label(info_grid, text="0 bytes")
        self.size_label.grid(row=0, column=7, sticky='w', padx=20)
        
        # Encryption options
        enc_frame = ttk.LabelFrame(self, text="🔐 Encryption Options")
        enc_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.encrypt_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(enc_frame, text="Encrypt site data with QWDE encryption",
                       variable=self.encrypt_var).pack(side=tk.LEFT, padx=10, pady=5)
        
        self.verify_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(enc_frame, text="Add error correction hash",
                       variable=self.verify_var).pack(side=tk.LEFT, padx=10, pady=5)
    
    def _create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self._new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self._open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self._save_file, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Publish to DDNS", command=self._publish, accelerator="Ctrl+P")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.editor.edit_undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.editor.edit_redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=lambda: self.event_generate('<<Cut>>'))
        edit_menu.add_command(label="Copy", command=lambda: self.event_generate('<<Copy>>'))
        edit_menu.add_command(label="Paste", command=lambda: self.event_generate('<<Paste>>'))
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All", command=self._select_all, accelerator="Ctrl+A")
        
        # Format menu
        format_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Format", menu=format_menu)
        format_menu.add_command(label="Word Wrap", command=self._toggle_wrap)
        format_menu.add_command(label="Font...", command=self._change_font)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
    
    def _bind_events(self):
        """Bind keyboard shortcuts"""
        self.bind('<Control-n>', lambda e: self._new_file())
        self.bind('<Control-o>', lambda e: self._open_file())
        self.bind('<Control-s>', lambda e: self._save_file())
        self.bind('<Control-p>', lambda e: self._publish())
        self.bind('<Control-a>', lambda e: self._select_all())
        self.bind('<Key>', lambda e: self._on_key())
    
    def _on_key(self, event=None):
        """Handle key press"""
        self.modified = True
        self._update_stats()
    
    def _update_stats(self):
        """Update statistics"""
        content = self.editor.get('1.0', 'end-1c')
        self.char_count = len(content)
        self.word_count = len(content.split())
        line_count = int(self.editor.index('end-1c').split('.')[0])
        
        self.char_label.config(text=str(self.char_count))
        self.word_label.config(text=str(self.word_count))
        self.line_label.config(text=str(line_count))
        self.size_label.config(text=f"{self.char_count} bytes")
    
    def _select_all(self):
        """Select all text"""
        self.editor.tag_add(tk.SEL, '1.0', tk.END)
        self.editor.mark_set(tk.INSERT, '1.0')
        self.editor.see(tk.INSERT)
        return 'break'
    
    def _toggle_wrap(self):
        """Toggle word wrap"""
        current = self.editor.cget('wrap')
        if current == tk.NONE:
            self.editor.config(wrap=tk.WORD)
        else:
            self.editor.config(wrap=tk.NONE)
    
    def _change_font(self):
        """Change font"""
        from tkinter import font
        fonts = list(font.families())
        
        dialog = tk.Toplevel(self)
        dialog.title("Choose Font")
        dialog.geometry("400x300")
        dialog.transient(self)
        
        ttk.Label(dialog, text="Font Family:").pack(padx=10, pady=5)
        
        font_list = tk.Listbox(dialog)
        font_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        for f in fonts:
            font_list.insert(tk.END, f)
        
        def apply_font():
            selection = font_list.curselection()
            if selection:
                font_name = font_list.get(selection[0])
                self.editor.config(font=(font_name, 11))
            dialog.destroy()
        
        ttk.Button(dialog, text="Apply", command=apply_font).pack(pady=5)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack()
    
    def _new_file(self):
        """Create new file"""
        if self.modified:
            if messagebox.askyesno("Save", "Save changes before creating new file?"):
                self._save_file()
        
        self.editor.delete('1.0', tk.END)
        self.current_file = None
        self.modified = False
        self.domain_entry.delete(0, tk.END)
        self.status_var.set("New file")
        self._update_stats()
    
    def _open_file(self):
        """Open file"""
        filename = filedialog.askopenfilename(
            filetypes=[
                ("Text Files", "*.txt"),
                ("HTML Files", "*.html *.htm"),
                ("All Files", "*.*")
            ]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.editor.delete('1.0', tk.END)
                self.editor.insert('1.0', content)
                self.current_file = filename
                self.modified = False
                self.status_var.set(f"Opened: {filename}")
                self._update_stats()
                
                # Suggest domain from filename
                if not self.domain_entry.get():
                    suggested = os.path.splitext(os.path.basename(filename))[0]
                    self.domain_entry.insert(0, suggested)
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {e}")
    
    def _save_file(self):
        """Save file"""
        if self.current_file:
            try:
                content = self.editor.get('1.0', 'end-1c')
                with open(self.current_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.modified = False
                self.status_var.set(f"Saved: {self.current_file}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")
        else:
            self._save_as()
    
    def _save_as(self):
        """Save as new file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("Text Files", "*.txt"),
                ("HTML Files", "*.html"),
                ("All Files", "*.*")
            ]
        )
        
        if filename:
            self.current_file = filename
            self._save_file()
    
    def _publish(self):
        """Publish site to DDNS"""
        domain = self.domain_entry.get().strip()
        
        if not domain:
            messagebox.showerror("Error", "Please enter a domain name")
            return
        
        # Add .qwde if not present
        if not domain.endswith('.qwde'):
            domain = domain + '.qwde'
        
        content = self.editor.get('1.0', 'end-1c').encode('utf-8')
        
        if not content:
            messagebox.showerror("Error", "Cannot publish empty site")
            return
        
        # Check encryption option
        encrypt = self.encrypt_var.get()
        
        try:
            if self.peer:
                result = self.peer.register_site(domain, content, encrypt=encrypt)
                
                if result:
                    self.result = {
                        'domain': domain,
                        'fwild': result.get('fwild'),
                        'version': result.get('version'),
                        'content': content
                    }
                    
                    messagebox.showinfo(
                        "Success",
                        f"Site published successfully!\n\n"
                        f"Domain: {domain}\n"
                        f"fwild: {result.get('fwild')}\n"
                        f"Version: {result.get('version')}\n"
                        f"Encrypted: {encrypt}"
                    )
                    self.status_var.set(f"Published: {domain} (fwild={result.get('fwild')})")
                else:
                    messagebox.showerror("Error", "Failed to publish site")
            else:
                messagebox.showerror("Error", "Not connected to peer network")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to publish: {e}")
            logger.error(f"Publish error: {e}")
    
    def _show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About Site Creator",
            "QWDE Site Creator\n\n"
            "A notepad clone for creating and publishing\n"
            "websites to the QWDE decentralized network.\n\n"
            "Features:\n"
            "• Syntax highlighting\n"
            "• Line numbers\n"
            "• Word/character count\n"
            "• QWDE encryption support\n"
            "• Direct DDNS publishing"
        )


# ==================== Main Browser GUI ====================

class QWDEBrowserGUI(tk.Tk):
    """QWDE Browser with Site Creator, Plugins, and Security Features"""
    
    def __init__(self):
        super().__init__()
        
        self.title("🌐 QWDE Protocol Browser")
        self.geometry("1400x900")
        self.configure(bg='#1a1a2e')
        
        # State
        self.peer: Optional[QWDEPeer] = None
        self.encryption_manager: Optional[EncryptionManager] = None
        self.plugin_manager: Optional[PluginManager] = None
        self.current_site: Optional[dict] = None
        self.history: List[str] = []
        self.history_index = -1
        
        # Security settings
        self.https_only = False
        self.verify_certificates = True
        self.encryption_state = "unknown"
        
        # Configure styles
        self._configure_styles()
        
        # Build UI
        self._create_menu()
        self._create_toolbar()
        self._create_main_layout()
        self._create_status_bar()
        
        # Initialize plugin manager
        self.plugin_manager = PluginManager(self)
        self.plugin_manager.load_plugins_from_dir()
        
        self.is_connected = False
    
    def _configure_styles(self):
        """Configure modern dark theme styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Colors
        bg_dark = '#1a1a2e'
        bg_medium = '#16213e'
        bg_light = '#0f3460'
        accent = '#e94560'
        text_light = '#ffffff'
        text_dim = '#a0a0a0'
        
        style.configure('Dark.TFrame', background=bg_dark)
        style.configure('Medium.TFrame', background=bg_medium)
        style.configure('Dark.TLabel', background=bg_dark, foreground=text_light)
        style.configure('Medium.TLabel', background=bg_medium, foreground=text_light)
        style.configure('Accent.TButton', background=accent, foreground=text_light)
        style.configure('Dark.TNotebook', background=bg_dark)
        style.configure('Dark.TNotebook.Tab', background=bg_medium, foreground=text_light, padding=(20, 8))
        style.map('Dark.TNotebook.Tab', background=[('selected', bg_light)])
        
        style.configure('Dark.Treeview', background=bg_medium, foreground=text_light, fieldbackground=bg_medium)
        style.configure('Dark.Treeview.Heading', background=bg_light, foreground=text_light)
    
    def _create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Site", command=self._open_site_creator, accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self._open_site, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_close, accelerator="Alt+F4")
        
        # Network menu
        network_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Network", menu=network_menu)
        network_menu.add_command(label="Connect", command=self._connect)
        network_menu.add_command(label="Disconnect", command=self._disconnect)
        network_menu.add_separator()
        network_menu.add_command(label="🌐 Network Health Map", command=self._show_network_health)
        network_menu.add_command(label="Peer Status", command=self._show_peer_status)
        
        # Security menu
        security_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Security", menu=security_menu)
        security_menu.add_command(label="HTTPS Only Mode", command=self._toggle_https_only)
        security_menu.add_command(label="Certificate Verification", command=self._toggle_cert_verify)
        security_menu.add_separator()
        security_menu.add_command(label="Encryption Info", command=self._show_encryption_info)
        
        # Plugins menu
        plugins_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Plugins", menu=plugins_menu)
        plugins_menu.add_command(label="Manage Plugins", command=self._open_plugin_manager)
        plugins_menu.add_separator()
        
        # Add plugin toggle items
        for plugin_name in self.plugin_manager.plugins.keys():
            plugins_menu.add_command(
                label=plugin_name,
                command=lambda name=plugin_name: self._toggle_plugin(name)
            )
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About QWDE", command=self._show_about)
    
    def _create_toolbar(self):
        """Create toolbar with encryption indicator"""
        toolbar_frame = ttk.Frame(self, style='Medium.TFrame')
        toolbar_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Navigation buttons
        nav_frame = ttk.Frame(toolbar_frame, style='Medium.TFrame')
        nav_frame.pack(side=tk.LEFT)
        
        self.btn_back = ttk.Button(nav_frame, text="◀", width=3, command=self._go_back, state='disabled')
        self.btn_back.pack(side=tk.LEFT, padx=2)
        
        self.btn_forward = ttk.Button(nav_frame, text="▶", width=3, command=self._go_forward, state='disabled')
        self.btn_forward.pack(side=tk.LEFT, padx=2)
        
        self.btn_refresh = ttk.Button(nav_frame, text="⟳", width=3, command=self._refresh)
        self.btn_refresh.pack(side=tk.LEFT, padx=2)
        
        # URL bar with encryption indicator
        url_frame = ttk.Frame(toolbar_frame, style='Medium.TFrame')
        url_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        # Encryption state indicator (left of URL)
        self.encryption_indicator = tk.Label(
            url_frame,
            text="🔓",
            bg='#0f3460',
            fg='#ff4444',
            width=3,
            cursor="hand2"
        )
        self.encryption_indicator.pack(side=tk.LEFT)
        
        # Add tooltip to encryption indicator
        self._create_encryption_tooltip()
        
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var, font=('Consolas', 11))
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.url_entry.bind('<Return>', self._navigate_to_url)
        
        self.btn_go = ttk.Button(url_frame, text="Go", width=5, command=self._navigate_to_url)
        self.btn_go.pack(side=tk.LEFT, padx=5)
        
        # Site creator button
        self.btn_create_site = ttk.Button(
            toolbar_frame,
            text="📝 Create Site",
            command=self._open_site_creator,
            style='Accent.TButton'
        )
        self.btn_create_site.pack(side=tk.RIGHT, padx=5)
        
        # Connection indicator
        self.connection_label = ttk.Label(toolbar_frame, text="●", foreground='#ff4444', font=('Arial', 16))
        self.connection_label.pack(side=tk.RIGHT, padx=10)
        
        ttk.Label(toolbar_frame, text="Network:", style='Medium.TLabel').pack(side=tk.RIGHT, padx=5)
    
    def _create_encryption_tooltip(self):
        """Create tooltip for encryption indicator"""
        self.tooltip = None
        
        def show_tooltip(event=None):
            if self.tooltip:
                self.tooltip.destroy()
            
            x = self.encryption_indicator.winfo_rootx()
            y = self.encryption_indicator.winfo_rooty() + 30
            
            # Get encryption state info
            if self.encryption_state == "encrypted":
                status_text = "🔒 ENCRYPTED\n\nSite data is encrypted with QWDE encryption\nError correction hash verified"
                color = "#00ff88"
            elif self.encryption_state == "https":
                status_text = "🔐 HTTPS SECURE\n\nConnection is encrypted with TLS/SSL\nCertificate verified"
                color = "#00ff88"
            elif self.encryption_state == "http":
                status_text = "⚠️ NOT ENCRYPTED\n\nConnection is unencrypted\nData can be intercepted"
                color = "#ffaa00"
            else:
                status_text = "❓ UNKNOWN\n\nEncryption status unknown"
                color = "#ff4444"
            
            self.tooltip = tk.Toplevel(self)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            label = tk.Label(
                self.tooltip,
                text=status_text,
                bg='#1a1a2e',
                fg=color,
                justify=tk.LEFT,
                padx=10,
                pady=10,
                relief=tk.SOLID,
                borderwidth=1
            )
            label.pack()
        
        def hide_tooltip(event=None):
            if self.tooltip:
                self.tooltip.destroy()
                self.tooltip = None
        
        self.encryption_indicator.bind('<Enter>', show_tooltip)
        self.encryption_indicator.bind('<Leave>', hide_tooltip)
    
    def _create_main_layout(self):
        """Create main layout with notebook"""
        self.notebook = ttk.Notebook(self, style='Dark.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Browser tab
        browser_frame = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.notebook.add(browser_frame, text="🌐 Browser")
        self._create_browser_panel(browser_frame)
        
        # Sites tab
        sites_frame = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.notebook.add(sites_frame, text="📁 Sites")
        self._create_sites_panel(sites_frame)
        
        # Peers tab
        peers_frame = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.notebook.add(peers_frame, text="🔗 Peers")
        self._create_peers_panel(peers_frame)
        
        # Plugins tab
        plugins_frame = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.notebook.add(plugins_frame, text="🔌 Plugins")
        self._create_plugins_panel(plugins_frame)
        
        # Console tab
        console_frame = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.notebook.add(console_frame, text="📜 Console")
        self._create_console_panel(console_frame)
    
    def _create_browser_panel(self, parent):
        """Create browser viewing panel"""
        self.content_display = scrolledtext.ScrolledText(
            parent,
            bg='#0a0a1a',
            fg='#00ff88',
            insertbackground='white',
            font=('Consolas', 11),
            wrap=tk.WORD
        )
        self.content_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Site info bar
        info_frame = ttk.Frame(parent, style='Dark.TFrame')
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.site_info_label = ttk.Label(info_frame, text="No site loaded", style='Dark.TLabel')
        self.site_info_label.pack(side=tk.LEFT)
    
    def _create_sites_panel(self, parent):
        """Create sites management panel"""
        paned = ttk.PanedWindow(parent, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Local sites
        local_frame = ttk.LabelFrame(paned, text="Local Sites")
        paned.add(local_frame, weight=1)
        
        columns = ('domain', 'fwild', 'size', 'updated')
        self.local_sites_tree = ttk.Treeview(local_frame, columns=columns, show='headings', height=10)
        for col in columns:
            self.local_sites_tree.heading(col, text=col.capitalize())
            self.local_sites_tree.column(col, width=100)
        self.local_sites_tree.column('domain', width=200)
        self.local_sites_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Remote sites
        remote_frame = ttk.LabelFrame(paned, text="Remote Sites")
        paned.add(remote_frame, weight=1)
        
        self.remote_sites_tree = ttk.Treeview(remote_frame, columns=columns, show='headings', height=10)
        for col in columns:
            self.remote_sites_tree.heading(col, text=col.capitalize())
            self.remote_sites_tree.column(col, width=100)
        self.remote_sites_tree.column('domain', width=200)
        self.remote_sites_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.remote_sites_tree.bind('<Double-1>', self._on_site_double_click)
        
        btn_frame = ttk.Frame(remote_frame, style='Dark.TFrame')
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Refresh", command=self._refresh_sites).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Sync from DDNS", command=self._sync_from_ddns).pack(side=tk.LEFT, padx=2)
    
    def _create_peers_panel(self, parent):
        """Create peers panel"""
        columns = ('peer_id', 'host', 'port', 'sites', 'status')
        self.peers_tree = ttk.Treeview(parent, columns=columns, show='headings', height=20)
        
        for col in columns:
            self.peers_tree.heading(col, text=col.capitalize())
            self.peers_tree.column(col, width=100)
        self.peers_tree.column('peer_id', width=200)
        self.peers_tree.column('host', width=150)
        self.peers_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        btn_frame = ttk.Frame(parent, style='Dark.TFrame')
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Discover Peers", command=self._discover_peers).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Refresh", command=self._refresh_peers).pack(side=tk.LEFT, padx=2)
    
    def _create_plugins_panel(self, parent):
        """Create plugins management panel"""
        # Plugin list
        columns = ('name', 'version', 'status', 'description')
        self.plugins_tree = ttk.Treeview(parent, columns=columns, show='headings', height=15)
        
        self.plugins_tree.heading('name', text='Name')
        self.plugins_tree.heading('version', text='Version')
        self.plugins_tree.heading('status', text='Status')
        self.plugins_tree.heading('description', text='Description')
        
        self.plugins_tree.column('name', width=150)
        self.plugins_tree.column('version', width=80)
        self.plugins_tree.column('status', width=80)
        self.plugins_tree.column('description', width=300)
        
        self.plugins_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Populate with plugins
        self._refresh_plugins_list()
        
        # Buttons
        btn_frame = ttk.Frame(parent, style='Dark.TFrame')
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Enable/Disable", command=self._toggle_selected_plugin).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Settings", command=self._plugin_settings).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Open Plugin Folder", command=self._open_plugin_folder).pack(side=tk.RIGHT, padx=2)
    
    def _create_console_panel(self, parent):
        """Create console panel"""
        self.console_output = scrolledtext.ScrolledText(
            parent,
            bg='#0a0a1a',
            fg='#88ff88',
            insertbackground='white',
            font=('Consolas', 10),
            wrap=tk.WORD
        )
        self.console_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        input_frame = ttk.Frame(parent, style='Dark.TFrame')
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.console_input = ttk.Entry(input_frame, font=('Consolas', 10))
        self.console_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.console_input.bind('<Return>', self._execute_console_command)
        
        ttk.Button(input_frame, text="Execute", command=self._execute_console_command).pack(side=tk.LEFT, padx=5)
        ttk.Button(input_frame, text="Clear", command=self._clear_console).pack(side=tk.RIGHT, padx=5)
    
    def _create_status_bar(self):
        """Create status bar"""
        status_frame = ttk.Frame(self, style='Dark.TFrame')
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(status_frame, text="Status: Disconnected", style='Dark.TLabel')
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        self.security_label = ttk.Label(status_frame, text="🔓 HTTP | Cert: ✓", style='Dark.TLabel')
        self.security_label.pack(side=tk.RIGHT, padx=10)
        
        self.peer_count_label = ttk.Label(status_frame, text="Peers: 0 | Sites: 0", style='Dark.TLabel')
        self.peer_count_label.pack(side=tk.RIGHT, padx=20)
    
    # ==================== Event Handlers ====================
    
    def _open_site_creator(self):
        """Open site creator dialog"""
        dialog = SiteCreatorDialog(self, self.peer)
        self.wait_window(dialog)
        
        if dialog.result:
            self._log_console(f"[+] Site created: {dialog.result['domain']} (fwild={dialog.result['fwild']})")
            self._refresh_sites()
    
    def _toggle_https_only(self):
        """Toggle HTTPS-only mode"""
        self.https_only = not self.https_only
        self._log_console(f"[{'+' if self.https_only else '-'}] HTTPS-only mode: {'enabled' if self.https_only else 'disabled'}")
        self._update_security_status()
    
    def _toggle_cert_verify(self):
        """Toggle certificate verification"""
        self.verify_certificates = not self.verify_certificates
        self._log_console(f"[{'+' if self.verify_certificates else '-'}] Certificate verification: {'enabled' if self.verify_certificates else 'disabled'}")
        self._update_security_status()
    
    def _update_security_status(self):
        """Update security status display"""
        https_status = "HTTPS" if self.https_only else "HTTP"
        cert_status = "✓" if self.verify_certificates else "✗"
        self.security_label.config(text=f"🔒 {https_status} | Cert: {cert_status}")
    
    def _open_plugin_manager(self):
        """Open plugin manager window"""
        self.plugin_manager.get_settings_window()
    
    def _toggle_plugin(self, plugin_name: str):
        """Toggle plugin enabled state"""
        if self.plugin_manager.is_enabled(plugin_name):
            self.plugin_manager.disable_plugin(plugin_name)
            self._log_console(f"[-] Plugin disabled: {plugin_name}")
        else:
            self.plugin_manager.enable_plugin(plugin_name)
            self._log_console(f"[+] Plugin enabled: {plugin_name}")
        
        self._refresh_plugins_list()
    
    def _refresh_plugins_list(self):
        """Refresh plugins treeview"""
        for item in self.plugins_tree.get_children():
            self.plugins_tree.delete(item)
        
        for plugin in self.plugin_manager.plugins.values():
            status = "Enabled" if plugin.enabled else "Disabled"
            self.plugins_tree.insert('', 'end', values=(
                plugin.name,
                plugin.version,
                status,
                plugin.description
            ))
    
    def _toggle_selected_plugin(self):
        """Toggle selected plugin"""
        selection = self.plugins_tree.selection()
        if selection:
            item = self.plugins_tree.item(selection[0])
            plugin_name = item['values'][0]
            self._toggle_plugin(plugin_name)
    
    def _plugin_settings(self):
        """Open settings for selected plugin"""
        selection = self.plugins_tree.selection()
        if selection:
            item = self.plugins_tree.item(selection[0])
            plugin_name = item['values'][0]
            plugin = self.plugin_manager.get_plugin(plugin_name)
            
            if plugin and plugin.get_settings_ui:
                settings_window = tk.Toplevel(self)
                settings_window.title(f"{plugin_name} Settings")
                settings_ui = plugin.get_settings_ui(settings_window)
                if settings_ui:
                    settings_ui.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def _open_plugin_folder(self):
        """Open plugin folder"""
        plugin_dir = os.path.join(os.path.dirname(__file__), 'plugins')
        if not os.path.exists(plugin_dir):
            os.makedirs(plugin_dir)
        os.startfile(plugin_dir)
    
    def _update_encryption_indicator(self, state: str):
        """Update encryption indicator icon and color"""
        self.encryption_state = state
        
        if state == "encrypted":
            self.encryption_indicator.config(text="🔒", fg='#00ff88')
        elif state == "https":
            self.encryption_indicator.config(text="🔐", fg='#00ff88')
        elif state == "http":
            self.encryption_indicator.config(text="⚠️", fg='#ffaa00')
        else:
            self.encryption_indicator.config(text="❓", fg='#ff4444')
    
    def _connect(self):
        """Connect to QWDE network with HTTPS configuration"""
        if self.is_connected:
            messagebox.showinfo("Info", "Already connected")
            return
        
        try:
            from qwde_peer_network import create_peer
            from qwde_https_config import get_config
            
            # Get HTTPS configuration
            https_config = get_config()
            server_url = https_config.get_server_url()
            
            # Extract host from URL for backend connection
            import re
            match = re.search(r'https?://([^:/]+)(?::(\d+))?', server_url)
            if match:
                backend_host = match.group(1)
                backend_port = int(match.group(2)) if match.group(2) else (443 if 'https' in server_url else 80)
            else:
                backend_host = 'localhost'
                backend_port = 8080
            
            # Construct backend URL
            backend_url = f"{server_url.rsplit('/', 1)[0]}/qwde_ddns_api.php"
            
            self.peer = create_peer(backend_url=backend_url)
            self.encryption_manager = EncryptionManager(self.peer.peer_id)
            
            # Store HTTPS config for reference
            self.https_config = https_config
            
            peer_thread = threading.Thread(target=self.peer.start, daemon=True, kwargs={'auto_sync': True})
            peer_thread.start()
            
            time.sleep(2)
            
            self.is_connected = True
            self.connection_label.config(foreground='#00ff88')
            self.status_label.config(text=f"Status: Connected as {self.peer.peer_id}")
            
            # Update security status based on HTTPS config
            if https_config.is_https_only():
                self._toggle_https_only()  # Enable HTTPS-only mode
                self._log_console(f"[+] Connected with HTTPS to {server_url}")
            else:
                self._log_console(f"[+] Connected to {server_url}")
            
            self._discover_peers()
            
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))
            self._log_console(f"[-] Connection failed: {e}")
    
    def _disconnect(self):
        """Disconnect from network"""
        if not self.is_connected:
            return
        
        try:
            if self.peer:
                self.peer.stop()
            
            self.is_connected = False
            self.connection_label.config(foreground='#ff4444')
            self.status_label.config(text="Status: Disconnected")
            
            self._log_console("[-] Disconnected from QWDE network")
            
        except Exception as e:
            self._log_console(f"Error disconnecting: {e}")
    
    def _navigate_to_url(self, event=None):
        """Navigate to URL"""
        url = self.url_var.get().strip()
        
        if not url:
            return
        
        # Check HTTPS-only mode
        if self.https_only and url.startswith('http://'):
            if not messagebox.askyesno("Security Warning", 
                "HTTPS-only mode is enabled.\nDo you want to allow this HTTP connection?"):
                return
        
        # Add protocol if missing
        if not url.startswith(('qwde://', 'http://', 'https://')):
            url = 'qwde://' + url
        
        try:
            if url.startswith('qwde://'):
                self._load_qwde_site(url)
            else:
                self._load_http_site(url)
            
            self._add_to_history(url)
            
        except Exception as e:
            messagebox.showerror("Navigation Error", str(e))
            self._log_console(f"[-] Navigation failed: {e}")
    
    def _load_qwde_site(self, url: str):
        """Load QWDE site"""
        if not self.peer:
            messagebox.showinfo("Not Connected", "Please connect to the network first")
            return
        
        site = self.peer.resolve_qwde_url(url)
        
        if site:
            self._display_site(site, url)
            self._update_encryption_indicator("encrypted")
        else:
            messagebox.showinfo("Not Found", f"Site not found: {url}")
            self._update_encryption_indicator("unknown")
    
    def _load_http_site(self, url: str):
        """Load HTTP/HTTPS site"""
        try:
            # Check if request should be allowed by plugins
            if not self.plugin_manager.on_request(url):
                self._log_console(f"[Plugin] Blocked request: {url}")
                return
            
            # Configure SSL
            context = None
            if self.verify_certificates:
                context = ssl.create_default_context()
            else:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            
            # Make request
            req = urllib.request.Request(url, headers={'User-Agent': 'QWDE-Browser/1.0'})
            
            with urllib.request.urlopen(req, timeout=10, context=context) as response:
                content = response.read().decode('utf-8', errors='replace')
            
            # Apply plugins
            content = self.plugin_manager.on_page_load(url, content)
            
            # Display
            self.content_display.delete('1.0', tk.END)
            self.content_display.insert(tk.END, content)
            
            self.site_info_label.config(text=f"URL: {url} | Size: {len(content)} bytes")
            
            # Update encryption indicator
            if url.startswith('https://'):
                self._update_encryption_indicator("https")
            else:
                self._update_encryption_indicator("http")
            
            self._log_console(f"[+] Loaded: {url}")
            
        except ssl.SSLCertVerificationError:
            messagebox.showerror("Security Error", "SSL certificate verification failed")
            self._update_encryption_indicator("unknown")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load site: {e}")
            self._update_encryption_indicator("unknown")
    
    def _display_site(self, site: dict, url: str):
        """Display site content"""
        self.current_site = site
        
        # Get content (may be encrypted)
        site_data = site.get('site_data', b'')
        if isinstance(site_data, str):
            site_data = bytes.fromhex(site_data)
        
        try:
            content = site_data.decode('utf-8')
        except:
            content = f"[Binary data - {len(site_data)} bytes]\n\n{site_data.hex()}"
        
        # Apply plugins
        content = self.plugin_manager.on_page_load(url, content)
        
        self.content_display.delete('1.0', tk.END)
        self.content_display.insert(tk.END, content)
        
        self.site_info_label.config(
            text=f"Domain: {site.get('domain', 'unknown')} | "
                 f"fwild: {site.get('fwild', 'N/A')} | "
                 f"Size: {len(site_data)} bytes"
        )
        
        self._log_console(f"[+] Loaded site: {url}")
    
    def _add_to_history(self, url: str):
        """Add to navigation history"""
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        
        self.history.append(url)
        self.history_index = len(self.history) - 1
        
        self.btn_back.config(state='normal' if self.history_index > 0 else 'disabled')
        self.btn_forward.config(state='normal' if self.history_index < len(self.history) - 1 else 'disabled')
    
    def _go_back(self):
        """Navigate back"""
        if self.history_index > 0:
            self.history_index -= 1
            self.url_var.set(self.history[self.history_index])
            self._navigate_to_url()
    
    def _go_forward(self):
        """Navigate forward"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.url_var.set(self.history[self.history_index])
            self._navigate_to_url()
    
    def _refresh(self):
        """Refresh current page"""
        if self.url_var.get():
            self._navigate_to_url()
    
    def _refresh_sites(self):
        """Refresh site lists"""
        if self.peer:
            self.local_sites_tree.delete(*self.local_sites_tree.get_children())
            for domain, site in self.peer.sites.items():
                self.local_sites_tree.insert('', 'end', values=(
                    domain,
                    site.get('fwild', 'N/A'),
                    f"{len(site.get('site_data', b''))} B",
                    datetime.fromtimestamp(site.get('updated_at', 0)).strftime('%H:%M:%S')
                ))
            
            self._sync_from_ddns()
    
    def _sync_from_ddns(self):
        """Sync sites from DDNS"""
        if not self.peer:
            return
        
        try:
            sites = self.peer.sync_from_backend()
            
            self.remote_sites_tree.delete(*self.remote_sites_tree.get_children())
            for site in sites:
                self.remote_sites_tree.insert('', 'end', values=(
                    site.get('domain', 'unknown'),
                    site.get('fwild', 'N/A'),
                    f"{len(bytes.fromhex(site.get('site_data', '00')))} B",
                    datetime.fromtimestamp(site.get('updated_at', 0)).strftime('%H:%M:%S')
                ))
            
            self._log_console(f"[+] Synced {len(sites)} sites from DDNS")
            
        except Exception as e:
            self._log_console(f"[-] DDNS sync failed: {e}")
    
    def _on_site_double_click(self, event):
        """Handle double-click on site"""
        selection = self.remote_sites_tree.selection()
        if selection:
            item = self.remote_sites_tree.item(selection[0])
            domain = item['values'][0]
            self.url_var.set(f"qwde://{domain}")
            self._navigate_to_url()
    
    def _discover_peers(self):
        """Discover peers"""
        if not self.peer:
            return
        
        try:
            self.peer.discover_peers()
            
            self.peers_tree.delete(*self.peers_tree.get_children())
            for conn in self.peer.pin_wheel.get_all_peers():
                status = "Active" if conn.is_connected else "Idle"
                self.peers_tree.insert('', 'end', values=(
                    conn.peer_id,
                    conn.host,
                    conn.port,
                    conn.sites_count,
                    status
                ))
            
            peer_count = self.peer.pin_wheel.get_connection_count()
            site_count = len(self.peer.sites) if self.peer else 0
            self.peer_count_label.config(text=f"Peers: {peer_count} | Sites: {site_count}")
            
            self._log_console(f"[+] Discovered {peer_count} peers")
            
        except Exception as e:
            self._log_console(f"[-] Peer discovery failed: {e}")
    
    def _refresh_peers(self):
        """Refresh peer list"""
        self._discover_peers()
    
    def _show_peer_status(self):
        """Show peer status"""
        if not self.peer:
            messagebox.showinfo("Info", "Not connected")
            return
        
        info = f"""Peer Status
═══════════════════════════════════
Peer ID: {self.peer.peer_id}
Host: {self.peer.host}:{self.peer.port}
Connected Peers: {self.peer.pin_wheel.get_connection_count()}
Local Sites: {len(self.peer.sites)}
        """
        messagebox.showinfo("Peer Status", info)
    
    def _show_network_health(self):
        """Show network health and topology map"""
        if not self.peer:
            messagebox.showinfo("Info", "Please connect to the network first")
            return
        
        # Import and show topology window
        from qwde_network_health import NetworkTopologyWindow
        
        self.topology_window = NetworkTopologyWindow(self, self.peer)
    
    def _show_encryption_info(self):
        """Show encryption information"""
        if not self.encryption_manager:
            messagebox.showinfo("Info", "Not connected")
            return
        
        stats = self.encryption_manager.get_stats()
        info = f"""Encryption Session Info
═══════════════════════════════════
Peer ID: {stats['peer_id']}
Active Channels: {stats['active_channels']}
        """
        messagebox.showinfo("Encryption Info", info)
    
    def _show_about(self):
        """Show about dialog"""
        info = """QWDE Protocol Browser
═══════════════════════════════════
Version: 1.0.0

Features:
• Site Creator with Notepad Clone
• Plugin System
• HTTPS-Only Mode
• Certificate Verification
• Encryption State Indicator
• QWDE Encryption Support
• P2P Site Distribution
        """
        messagebox.showinfo("About QWDE", info)
    
    def _on_close(self):
        """Handle window close"""
        self._disconnect()
        self.destroy()
    
    def _log_console(self, message: str):
        """Log to console"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.console_output.insert(tk.END, f"[{timestamp}] {message}\n")
        self.console_output.see(tk.END)
    
    def _clear_console(self):
        """Clear console"""
        self.console_output.delete('1.0', tk.END)
    
    def _execute_console_command(self, event=None):
        """Execute console command"""
        command = self.console_input.get().strip()
        if not command:
            return
        
        self.console_input.delete(0, tk.END)
        self._log_console(f"> {command}")
        
        try:
            if command == 'help':
                self._log_console("Commands: help, peers, sites, status, connect, disconnect")
            elif command == 'peers':
                self._discover_peers()
            elif command == 'sites':
                self._refresh_sites()
            elif command == 'status':
                if self.peer:
                    self._log_console(f"Peer: {self.peer.peer_id}")
                    self._log_console(f"Connections: {self.peer.pin_wheel.get_connection_count()}")
                    self._log_console(f"Sites: {len(self.peer.sites)}")
                else:
                    self._log_console("Not connected")
            elif command == 'connect':
                self._connect()
            elif command == 'disconnect':
                self._disconnect()
            else:
                self._log_console(f"Unknown command: {command}")
        except Exception as e:
            self._log_console(f"Error: {e}")


def run_browser():
    """Run the QWDE browser"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║              QWDE Protocol Browser                        ║
╠═══════════════════════════════════════════════════════════╣
║  Features:                                                ║
║    • Site Creator with Notepad Clone                     ║
║    • Plugin System                                       ║
║    • HTTPS-Only Mode                                     ║
║    • Encryption State Indicator                          ║
║    • Certificate Verification                            ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    app = QWDEBrowserGUI()
    app.mainloop()


if __name__ == '__main__':
    run_browser()
