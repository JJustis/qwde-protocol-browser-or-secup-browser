"""
QWDE Protocol - Configuration Wizard
Configures browser, mirror server, and central DDNS server
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import configparser
import os
import json
import mysql.connector
from mysql.connector import Error


class QWDEConfigWizard:
    """Configuration wizard for QWDE Protocol"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("QWDE Protocol - Configuration Wizard")
        self.root.geometry("800x700")
        
        self.config = configparser.ConfigParser()
        self.config_path = 'qwde_config.ini'
        
        self._create_wizard()
    
    def _create_wizard(self):
        """Create wizard interface"""
        # Notebook for wizard pages
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Page 1: Welcome
        self.page_welcome = self._create_welcome_page()
        self.notebook.add(self.page_welcome, text="Welcome")
        
        # Page 2: Central Server
        self.page_central = self._create_central_server_page()
        self.notebook.add(self.page_central, text="Central Server")
        
        # Page 3: Database
        self.page_database = self._create_database_page()
        self.notebook.add(self.page_database, text="Database")
        
        # Page 4: Browser Settings
        self.page_browser = self._create_browser_page()
        self.notebook.add(self.page_browser, text="Browser")
        
        # Page 5: Mirror Server
        self.page_mirror = self._create_mirror_page()
        self.notebook.add(self.page_mirror, text="Mirror Server")
        
        # Page 6: Security
        self.page_security = self._create_security_page()
        self.notebook.add(self.page_security, text="Security")
        
        # Page 7: Review & Save
        self.page_review = self._create_review_page()
        self.notebook.add(self.page_review, text="Review")
        
        # Navigation buttons
        nav_frame = ttk.Frame(self.root)
        nav_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.btn_back = ttk.Button(nav_frame, text="← Back", command=self._go_back, state='disabled')
        self.btn_back.pack(side=tk.LEFT, padx=5)
        
        self.btn_next = ttk.Button(nav_frame, text="Next →", command=self._go_next)
        self.btn_next.pack(side=tk.LEFT, padx=5)
        
        self.btn_finish = ttk.Button(nav_frame, text="✓ Save Configuration", command=self._save_config)
        self.btn_finish.pack(side=tk.RIGHT, padx=5)
        
        self.btn_test = ttk.Button(nav_frame, text="🧪 Test Connection", command=self._test_connection)
        self.btn_test.pack(side=tk.RIGHT, padx=5)
        
        # Load existing config
        self._load_config()
    
    def _create_welcome_page(self):
        """Create welcome page"""
        frame = ttk.Frame(self.root, padding=20)
        
        title = ttk.Label(
            frame,
            text="QWDE Protocol Configuration Wizard",
            font=('Arial', 16, 'bold')
        )
        title.pack(pady=20)
        
        welcome_text = """
Welcome to the QWDE Protocol Configuration Wizard!

This wizard will help you configure:

1. Central DDNS Server (secupgrade.com or your server)
2. MySQL Database Connection
3. Browser Settings
4. Mirror Server Configuration
5. Security Settings

Click "Next" to begin configuration.
        """
        
        text = scrolledtext.ScrolledText(frame, height=15, wrap=tk.WORD)
        text.insert('1.0', welcome_text)
        text.config(state='disabled')
        text.pack(fill=tk.BOTH, expand=True, pady=20)
        
        return frame
    
    def _create_central_server_page(self):
        """Create central server configuration page"""
        frame = ttk.Frame(self.root, padding=20)
        
        title = ttk.Label(
            frame,
            text="Central DDNS Server Configuration",
            font=('Arial', 14, 'bold')
        )
        title.pack(pady=10)
        
        # Server type selection
        type_frame = ttk.LabelFrame(frame, text="Server Type", padding=10)
        type_frame.pack(fill=tk.X, pady=10)
        
        self.server_type = tk.StringVar(value="external")
        ttk.Radiobutton(
            type_frame,
            text="Use external server (secupgrade.com)",
            variable=self.server_type,
            value="external",
            command=self._toggle_server_fields
        ).pack(anchor=tk.W, pady=5)
        
        ttk.Radiobutton(
            type_frame,
            text="Host your own central server",
            variable=self.server_type,
            value="self_hosted",
            command=self._toggle_server_fields
        ).pack(anchor=tk.W, pady=5)
        
        # Server details
        details_frame = ttk.LabelFrame(frame, text="Server Details", padding=10)
        details_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(details_frame, text="Protocol:").grid(row=0, column=0, sticky='w', pady=5)
        self.central_protocol = ttk.Combobox(details_frame, values=['https', 'http'], width=30)
        self.central_protocol.set('https')
        self.central_protocol.grid(row=0, column=1, pady=5, padx=10)
        
        ttk.Label(details_frame, text="Host:").grid(row=1, column=0, sticky='w', pady=5)
        self.central_host = ttk.Entry(details_frame, width=30)
        self.central_host.insert(0, 'secupgrade.com')
        self.central_host.grid(row=1, column=1, pady=5, padx=10)
        
        ttk.Label(details_frame, text="Port:").grid(row=2, column=0, sticky='w', pady=5)
        self.central_port = ttk.Entry(details_frame, width=30)
        self.central_port.insert(0, '443')
        self.central_port.grid(row=2, column=1, pady=5, padx=10)
        
        ttk.Label(details_frame, text="API Path:").grid(row=3, column=0, sticky='w', pady=5)
        self.central_path = ttk.Entry(details_frame, width=30)
        self.central_path.insert(0, '/peer_directory_api.php')
        self.central_path.grid(row=3, column=1, pady=5, padx=10)
        
        # Full URL preview
        url_frame = ttk.LabelFrame(frame, text="Full Server URL", padding=10)
        url_frame.pack(fill=tk.X, pady=10)
        
        self.url_preview = ttk.Label(url_frame, text="", foreground='#00ff88')
        self.url_preview.pack()
        
        # Bind to update preview
        for widget in [self.central_protocol, self.central_host, self.central_port, self.central_path]:
            widget.bind('<<ComboboxSelected>>', self._update_url_preview)
            widget.bind('<KeyRelease>', self._update_url_preview)
        
        self._update_url_preview()
        
        return frame
    
    def _create_database_page(self):
        """Create database configuration page"""
        frame = ttk.Frame(self.root, padding=20)
        
        title = ttk.Label(
            frame,
            text="MySQL Database Configuration",
            font=('Arial', 14, 'bold')
        )
        title.pack(pady=10)
        
        # Database details
        db_frame = ttk.LabelFrame(frame, text="Database Connection", padding=10)
        db_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(db_frame, text="Host:").grid(row=0, column=0, sticky='w', pady=5)
        self.db_host = ttk.Entry(db_frame, width=30)
        self.db_host.insert(0, 'localhost')
        self.db_host.grid(row=0, column=1, pady=5, padx=10)
        
        ttk.Label(db_frame, text="Port:").grid(row=1, column=0, sticky='w', pady=5)
        self.db_port = ttk.Entry(db_frame, width=30)
        self.db_port.insert(0, '3306')
        self.db_port.grid(row=1, column=1, pady=5, padx=10)
        
        ttk.Label(db_frame, text="Database Name:").grid(row=2, column=0, sticky='w', pady=5)
        self.db_name = ttk.Entry(db_frame, width=30)
        self.db_name.insert(0, 'qwde_directory')
        self.db_name.grid(row=2, column=1, pady=5, padx=10)
        
        ttk.Label(db_frame, text="Username:").grid(row=3, column=0, sticky='w', pady=5)
        self.db_user = ttk.Entry(db_frame, width=30)
        self.db_user.insert(0, 'qwde_user')
        self.db_user.grid(row=3, column=1, pady=5, padx=10)
        
        ttk.Label(db_frame, text="Password:").grid(row=4, column=0, sticky='w', pady=5)
        self.db_password = ttk.Entry(db_frame, width=30, show='*')
        self.db_password.grid(row=4, column=1, pady=5, padx=10)
        
        # Test button
        ttk.Button(db_frame, text="🧪 Test Database Connection", command=self._test_database).grid(
            row=5, column=1, pady=10, sticky='e'
        )
        
        # Info text
        info_text = """
Note: The database stores:
• Peer IP addresses and metadata
• Site directory (domain, fwild, creator)
• Ownership tokens for deletion
• Cache invalidation records

Site content is stored on peer computers, NOT in the database.
        """
        
        info = scrolledtext.ScrolledText(frame, height=6, wrap=tk.WORD)
        info.insert('1.0', info_text)
        info.config(state='disabled')
        info.pack(fill=tk.X, pady=10)
        
        return frame
    
    def _create_browser_page(self):
        """Create browser configuration page"""
        frame = ttk.Frame(self.root, padding=20)
        
        title = ttk.Label(
            frame,
            text="Browser Settings",
            font=('Arial', 14, 'bold')
        )
        title.pack(pady=10)
        
        # Protocol settings
        proto_frame = ttk.LabelFrame(frame, text="Protocol Settings", padding=10)
        proto_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(proto_frame, text="Protocol Prefix:").grid(row=0, column=0, sticky='w', pady=5)
        self.protocol_prefix = ttk.Entry(proto_frame, width=30)
        self.protocol_prefix.insert(0, 'qwde')
        self.protocol_prefix.grid(row=0, column=1, pady=5, padx=10)
        
        ttk.Label(proto_frame, text="Protocol Separator:").grid(row=1, column=0, sticky='w', pady=5)
        self.protocol_separator = ttk.Entry(proto_frame, width=30)
        self.protocol_separator.insert(0, '://')
        self.protocol_separator.grid(row=1, column=1, pady=5, padx=10)
        
        # HTML rendering
        html_frame = ttk.LabelFrame(frame, text="HTML Rendering", padding=10)
        html_frame.pack(fill=tk.X, pady=10)
        
        self.html_secure = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            html_frame,
            text="Use secure HTML viewer (source-first)",
            variable=self.html_secure
        ).pack(anchor=tk.W, pady=5)
        
        self.html_auto_detect = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            html_frame,
            text="Auto-detect HTML content",
            variable=self.html_auto_detect
        ).pack(anchor=tk.W, pady=5)
        
        return frame
    
    def _create_mirror_page(self):
        """Create mirror server configuration page"""
        frame = ttk.Frame(self.root, padding=20)
        
        title = ttk.Label(
            frame,
            text="Mirror Server Configuration",
            font=('Arial', 14, 'bold')
        )
        title.pack(pady=10)
        
        # Enable mirror
        enable_frame = ttk.LabelFrame(frame, text="Mirror Server", padding=10)
        enable_frame.pack(fill=tk.X, pady=10)
        
        self.mirror_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            enable_frame,
            text="Enable Mirror Server (downloads all sites)",
            variable=self.mirror_enabled
        ).pack(anchor=tk.W, pady=5)
        
        # Settings
        settings_frame = ttk.LabelFrame(frame, text="Mirror Settings", padding=10)
        settings_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(settings_frame, text="Listen Port:").grid(row=0, column=0, sticky='w', pady=5)
        self.mirror_port = ttk.Entry(settings_frame, width=30)
        self.mirror_port.insert(0, '8765')
        self.mirror_port.grid(row=0, column=1, pady=5, padx=10)
        
        ttk.Label(settings_frame, text="Sync Interval (seconds):").grid(row=1, column=0, sticky='w', pady=5)
        self.mirror_sync = ttk.Entry(settings_frame, width=30)
        self.mirror_sync.insert(0, '30')
        self.mirror_sync.grid(row=1, column=1, pady=5, padx=10)
        
        ttk.Label(settings_frame, text="Update Check Interval (seconds):").grid(row=2, column=0, sticky='w', pady=5)
        self.mirror_update = ttk.Entry(settings_frame, width=30)
        self.mirror_update.insert(0, '60')
        self.mirror_update.grid(row=2, column=1, pady=5, padx=10)
        
        # Cache settings
        cache_frame = ttk.LabelFrame(frame, text="Cache Settings", padding=10)
        cache_frame.pack(fill=tk.X, pady=10)
        
        self.cache_purge = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            cache_frame,
            text="Purge deleted sites from cache automatically",
            variable=self.cache_purge
        ).pack(anchor=tk.W, pady=5)
        
        return frame
    
    def _create_security_page(self):
        """Create security configuration page"""
        frame = ttk.Frame(self.root, padding=20)
        
        title = ttk.Label(
            frame,
            text="Security Settings",
            font=('Arial', 14, 'bold')
        )
        title.pack(pady=10)
        
        # HTTPS settings
        https_frame = ttk.LabelFrame(frame, text="HTTPS Settings", padding=10)
        https_frame.pack(fill=tk.X, pady=10)
        
        self.https_only = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            https_frame,
            text="HTTPS-Only Mode (block HTTP connections)",
            variable=self.https_only
        ).pack(anchor=tk.W, pady=5)
        
        self.verify_certs = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            https_frame,
            text="Verify SSL Certificates",
            variable=self.verify_certs
        ).pack(anchor=tk.W, pady=5)
        
        # Ownership token settings
        token_frame = ttk.LabelFrame(frame, text="Ownership Tokens", padding=10)
        token_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(token_frame, text="Token Expiry (minutes):").grid(row=0, column=0, sticky='w', pady=5)
        self.token_expiry = ttk.Entry(token_frame, width=30)
        self.token_expiry.insert(0, '5')
        self.token_expiry.grid(row=0, column=1, pady=5, padx=10)
        
        # Cache invalidation
        invalidation_frame = ttk.LabelFrame(frame, text="Cache Invalidation", padding=10)
        invalidation_frame.pack(fill=tk.X, pady=10)
        
        self.auto_invalidate = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            invalidation_frame,
            text="Auto-purge deleted sites from all caches",
            variable=self.auto_invalidate
        ).pack(anchor=tk.W, pady=5)
        
        ttk.Label(invalidation_frame, text="Polling Interval (seconds):").grid(row=1, column=0, sticky='w', pady=5)
        self.invalidation_poll = ttk.Entry(invalidation_frame, width=30)
        self.invalidation_poll.insert(0, '30')
        self.invalidation_poll.grid(row=1, column=1, pady=5, padx=10)
        
        return frame
    
    def _create_review_page(self):
        """Create review page"""
        frame = ttk.Frame(self.root, padding=20)
        
        title = ttk.Label(
            frame,
            text="Review Configuration",
            font=('Arial', 14, 'bold')
        )
        title.pack(pady=10)
        
        # Review text
        self.review_text = scrolledtext.ScrolledText(frame, height=25, wrap=tk.WORD)
        self.review_text.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Update button
        ttk.Button(frame, text="🔄 Update Preview", command=self._update_review).pack(pady=5)
        
        self._update_review()
        
        return frame
    
    def _update_url_preview(self, event=None):
        """Update URL preview"""
        protocol = self.central_protocol.get()
        host = self.central_host.get()
        port = self.central_port.get()
        path = self.central_path.get()
        
        url = f"{protocol}://{host}"
        if port not in ['80', '443']:
            url += f":{port}"
        url += path
        
        self.url_preview.config(text=url)
    
    def _toggle_server_fields(self):
        """Toggle server fields based on type"""
        if self.server_type.get() == "external":
            self.central_host.delete(0, tk.END)
            self.central_host.insert(0, 'secupgrade.com')
            self.central_path.delete(0, tk.END)
            self.central_path.insert(0, '/peer_directory_api.php')
        else:
            self.central_host.delete(0, tk.END)
            self.central_host.insert(0, 'localhost')
            self.central_path.delete(0, tk.END)
            self.central_path.insert(0, '/api_handler.php')
        
        self._update_url_preview()
    
    def _update_review(self):
        """Update configuration review"""
        review = """
═══════════════════════════════════════════════════════════
QWDE PROTOCOL CONFIGURATION REVIEW
═══════════════════════════════════════════════════════════

CENTRAL SERVER:
  Type: {}
  URL: {}:{}{}{}
  
DATABASE:
  Host: {}:{}
  Database: {}
  Username: {}
  Password: {}
  
BROWSER:
  Protocol: {}{}
  Secure HTML Viewer: {}
  Auto-detect HTML: {}
  
MIRROR SERVER:
  Enabled: {}
  Port: {}
  Sync Interval: {}s
  Update Check: {}s
  Auto-purge deleted sites: {}
  
SECURITY:
  HTTPS-Only: {}
  Verify Certificates: {}
  Token Expiry: {} minutes
  Auto-invalidate cache: {}
  Invalidation polling: {}s

═══════════════════════════════════════════════════════════
        """.format(
            self.server_type.get(),
            self.central_protocol.get(),
            self.central_host.get(),
            f":{self.central_port.get()}" if self.central_port.get() not in ['80', '443'] else "",
            self.central_path.get(),
            self.db_host.get(),
            self.db_port.get(),
            self.db_name.get(),
            self.db_user.get(),
            '*' * len(self.db_password.get()),
            self.protocol_prefix.get(),
            self.protocol_separator.get(),
            "✓" if self.html_secure.get() else "✗",
            "✓" if self.html_auto_detect.get() else "✗",
            "✓" if self.mirror_enabled.get() else "✗",
            self.mirror_port.get(),
            self.mirror_sync.get(),
            self.mirror_update.get(),
            "✓" if self.cache_purge.get() else "✗",
            "✓" if self.https_only.get() else "✗",
            "✓" if self.verify_certs.get() else "✗",
            self.token_expiry.get(),
            "✓" if self.auto_invalidate.get() else "✗",
            self.invalidation_poll.get()
        )
        
        self.review_text.delete('1.0', tk.END)
        self.review_text.insert('1.0', review)
    
    def _load_config(self):
        """Load existing configuration"""
        if os.path.exists(self.config_path):
            self.config.read(self.config_path)
            
            # Load central server
            if 'central_server' in self.config:
                self.central_protocol.set(self.config.get('central_server', 'protocol', fallback='https'))
                self.central_host.set(self.config.get('central_server', 'host', fallback='secupgrade.com'))
                self.central_port.set(self.config.get('central_server', 'port', fallback='443'))
                self.central_path.set(self.config.get('central_server', 'api_path', fallback='/peer_directory_api.php'))
            
            # Load database
            if 'mysql' in self.config:
                self.db_host.set(self.config.get('mysql', 'host', fallback='localhost'))
                self.db_port.set(self.config.get('mysql', 'port', fallback='3306'))
                self.db_name.set(self.config.get('mysql', 'database', fallback='qwde_directory'))
                self.db_user.set(self.config.get('mysql', 'user', fallback='qwde_user'))
            
            # Load protocol
            if 'protocol' in self.config:
                self.protocol_prefix.set(self.config.get('protocol', 'protocol_prefix', fallback='qwde'))
                self.protocol_separator.set(self.config.get('protocol', 'protocol_separator', fallback='://'))
            
            # Load mirror
            if 'mirror' in self.config:
                self.mirror_port.set(self.config.get('mirror', 'port', fallback='8765'))
                self.mirror_sync.set(self.config.get('mirror', 'sync_interval', fallback='30'))
                self.mirror_update.set(self.config.get('mirror', 'update_interval', fallback='60'))
            
            # Load security
            if 'security' in self.config:
                self.https_only.set(self.config.getboolean('security', 'https_only', fallback=True))
                self.verify_certs.set(self.config.getboolean('security', 'verify_certificates', fallback=True))
                self.token_expiry.set(self.config.get('security', 'token_expiry', fallback='5'))
                self.invalidation_poll.set(self.config.get('security', 'invalidation_poll', fallback='30'))
    
    def _test_database(self):
        """Test database connection"""
        try:
            connection = mysql.connector.connect(
                host=self.db_host.get(),
                port=int(self.db_port.get()),
                database=self.db_name.get(),
                user=self.db_user.get(),
                password=self.db_password.get()
            )
            
            if connection.is_connected():
                messagebox.showinfo(
                    "Success",
                    "Database connection successful!\n\n"
                    f"Host: {self.db_host.get()}:{self.db_port.get()}\n"
                    f"Database: {self.db_name.get()}"
                )
                connection.close()
        except Error as e:
            messagebox.showerror(
                "Connection Failed",
                f"Could not connect to database:\n\n{e}"
            )
    
    def _test_connection(self):
        """Test central server connection"""
        import requests
        
        url = f"{self.central_protocol.get()}://{self.central_host.get()}"
        if self.central_port.get() not in ['80', '443']:
            url += f":{self.central_port.get()}"
        url += self.central_path.get()
        
        try:
            response = requests.get(url + '?action=get_stats', timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    messagebox.showinfo(
                        "Success",
                        f"Central server connection successful!\n\n"
                        f"URL: {url}\n"
                        f"Stats: {data}"
                    )
                else:
                    messagebox.showwarning(
                        "Warning",
                        f"Server responded but with error:\n{data}"
                    )
            else:
                messagebox.showerror(
                    "Connection Failed",
                    f"Server returned HTTP {response.status_code}"
                )
        except Exception as e:
            messagebox.showerror(
                "Connection Failed",
                f"Could not connect to central server:\n\n{e}"
            )
    
    def _save_config(self):
        """Save configuration"""
        # Update config
        if 'central_server' not in self.config:
            self.config['central_server'] = {}
        self.config['central_server']['protocol'] = self.central_protocol.get()
        self.config['central_server']['host'] = self.central_host.get()
        self.config['central_server']['port'] = self.central_port.get()
        self.config['central_server']['api_path'] = self.central_path.get()
        self.config['central_server']['url'] = self.url_preview.cget('text')
        
        if 'mysql' not in self.config:
            self.config['mysql'] = {}
        self.config['mysql']['host'] = self.db_host.get()
        self.config['mysql']['port'] = self.db_port.get()
        self.config['mysql']['database'] = self.db_name.get()
        self.config['mysql']['user'] = self.db_user.get()
        self.config['mysql']['password'] = self.db_password.get()
        
        if 'protocol' not in self.config:
            self.config['protocol'] = {}
        self.config['protocol']['protocol_prefix'] = self.protocol_prefix.get()
        self.config['protocol']['protocol_separator'] = self.protocol_separator.get()
        
        if 'mirror' not in self.config:
            self.config['mirror'] = {}
        self.config['mirror']['enabled'] = str(self.mirror_enabled.get())
        self.config['mirror']['port'] = self.mirror_port.get()
        self.config['mirror']['sync_interval'] = self.mirror_sync.get()
        self.config['mirror']['update_interval'] = self.mirror_update.get()
        self.config['mirror']['cache_purge'] = str(self.cache_purge.get())
        
        if 'security' not in self.config:
            self.config['security'] = {}
        self.config['security']['https_only'] = str(self.https_only.get())
        self.config['security']['verify_certificates'] = str(self.verify_certs.get())
        self.config['security']['token_expiry'] = self.token_expiry.get()
        self.config['security']['auto_invalidate'] = str(self.auto_invalidate.get())
        self.config['security']['invalidation_poll'] = self.invalidation_poll.get()
        
        if 'html' not in self.config:
            self.config['html'] = {}
        self.config['html']['secure_viewer'] = str(self.html_secure.get())
        self.config['html']['auto_detect'] = str(self.html_auto_detect.get())
        
        # Save to file
        with open(self.config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)
        
        messagebox.showinfo(
            "Success",
            f"Configuration saved to:\n{os.path.abspath(self.config_path)}\n\n"
            f"Restart browser and servers for changes to take effect."
        )
    
    def _go_back(self):
        """Go to previous page"""
        current = self.notebook.index(self.notebook.select())
        if current > 0:
            self.notebook.select(current - 1)
            self.btn_back.config(state='normal' if current > 1 else 'disabled')
            self.btn_next.config(state='normal')
    
    def _go_next(self):
        """Go to next page"""
        current = self.notebook.index(self.notebook.select())
        max_page = self.notebook.index('end') - 1
        
        if current < max_page:
            self.notebook.select(current + 1)
            self.btn_back.config(state='normal')
            if current + 1 >= max_page:
                self.btn_next.config(state='disabled')
    
    def run(self):
        """Run the wizard"""
        self.root.mainloop()


def main():
    """Main entry point"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║      QWDE Protocol - Configuration Wizard                 ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    wizard = QWDEConfigWizard()
    wizard.run()


if __name__ == '__main__':
    main()
