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
        
        # Page 7: Deployment Path
        self.page_deployment = self._create_deployment_page()
        self.notebook.add(self.page_deployment, text="Deployment Path")
        
        # Page 8: Self-Host Guide
        self.page_selfhost = self._create_selfhost_page()
        self.notebook.add(self.page_selfhost, text="Self-Host Guide")
        
        # Page 9: Review & Save
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
            text="Use secupgrade.com/switch domain",
            variable=self.server_type,
            value="switch",
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
        
        # Database type selection
        self.db_type = tk.StringVar(value="mysql")
        ttk.Radiobutton(
            db_frame,
            text="MySQL (from XAMPP or installed MySQL)",
            variable=self.db_type,
            value="mysql"
        ).grid(row=0, column=0, columnspan=2, sticky='w', pady=5)
        
        ttk.Radiobutton(
            db_frame,
            text="SQLite (simpler, no installation needed)",
            variable=self.db_type,
            value="sqlite"
        ).grid(row=1, column=0, columnspan=2, sticky='w', pady=5)
        
        # MySQL fields
        ttk.Label(db_frame, text="Host:").grid(row=2, column=0, sticky='w', pady=5)
        self.db_host = ttk.Entry(db_frame, width=30)
        self.db_host.insert(0, 'localhost')
        self.db_host.grid(row=2, column=1, pady=5, padx=10)
        
        ttk.Label(db_frame, text="Port:").grid(row=3, column=0, sticky='w', pady=5)
        self.db_port = ttk.Entry(db_frame, width=30)
        self.db_port.insert(0, '3306')
        self.db_port.grid(row=3, column=1, pady=5, padx=10)
        
        ttk.Label(db_frame, text="Database Name:").grid(row=4, column=0, sticky='w', pady=5)
        self.db_name = ttk.Entry(db_frame, width=30)
        self.db_name.insert(0, 'qwde_directory')
        self.db_name.grid(row=4, column=1, pady=5, padx=10)
        
        ttk.Label(db_frame, text="Username:").grid(row=5, column=0, sticky='w', pady=5)
        self.db_user = ttk.Entry(db_frame, width=30)
        self.db_user.insert(0, 'qwde_user')
        self.db_user.grid(row=5, column=1, pady=5, padx=10)
        
        ttk.Label(db_frame, text="Password:").grid(row=6, column=0, sticky='w', pady=5)
        self.db_password = ttk.Entry(db_frame, width=30, show='*')
        self.db_password.grid(row=6, column=1, pady=5, padx=10)
        
        # SQLite path field (hidden by default)
        ttk.Label(db_frame, text="SQLite File Path:").grid(row=7, column=0, sticky='w', pady=5)
        self.db_sqlite_path = ttk.Entry(db_frame, width=30)
        self.db_sqlite_path.insert(0, 'qwde_ddns.db')
        self.db_sqlite_path.grid(row=7, column=1, pady=5, padx=10)
        
        # Test button
        ttk.Button(db_frame, text="🧪 Test Database Connection", command=self._test_database).grid(
            row=8, column=1, pady=10, sticky='e'
        )
        
        # Toggle fields based on database type
        self._toggle_db_fields()
        
        # Bind to toggle
        self.db_type.trace('w', lambda *args: self._toggle_db_fields())
        
        # Info text
        info_text = """
Note: The database stores:
• Peer IP addresses and metadata
• Site directory (domain, fwild, creator)
• Ownership tokens for deletion
• Cache invalidation records

Site content is stored on peer computers, NOT in the database.

MySQL: Requires XAMPP or MySQL installation
SQLite: No installation needed, single file database
        """
        
        info = scrolledtext.ScrolledText(frame, height=8, wrap=tk.WORD)
        info.insert('1.0', info_text)
        info.config(state='disabled')
        info.pack(fill=tk.X, pady=10)
        
        return frame
    
    def _toggle_db_fields(self):
        """Toggle database fields based on type"""
        if self.db_type.get() == "sqlite":
            # Disable MySQL fields
            for widget in [self.db_host, self.db_port, self.db_name, self.db_user, self.db_password]:
                widget.config(state='disabled')
            # Enable SQLite field
            self.db_sqlite_path.config(state='normal')
        else:
            # Enable MySQL fields
            for widget in [self.db_host, self.db_port, self.db_name, self.db_user, self.db_password]:
                widget.config(state='normal')
            # Disable SQLite field
            self.db_sqlite_path.config(state='disabled')
    
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
    
    def _create_deployment_page(self):
        """Create deployment path configuration page"""
        frame = ttk.Frame(self.root, padding=20)
        
        title = ttk.Label(
            frame,
            text="PHP Files Deployment Path",
            font=('Arial', 14, 'bold')
        )
        title.pack(pady=10)
        
        # Deployment location selection
        location_frame = ttk.LabelFrame(frame, text="Deploy switch/ folder to:", padding=10)
        location_frame.pack(fill=tk.X, pady=10)
        
        self.deployment_type = tk.StringVar(value="xampp")
        
        ttk.Radiobutton(
            location_frame,
            text="XAMPP htdocs (C:\\xampp\\htdocs\\switch)",
            variable=self.deployment_type,
            value="xampp",
            command=self._update_deployment_path
        ).pack(anchor=tk.W, pady=5)
        
        ttk.Radiobutton(
            location_frame,
            text="Custom path (specify below)",
            variable=self.deployment_type,
            value="custom",
            command=self._update_deployment_path
        ).pack(anchor=tk.W, pady=5)
        
        ttk.Radiobutton(
            location_frame,
            text="FTP/SFTP (upload to remote server)",
            variable=self.deployment_type,
            value="ftp",
            command=self._update_deployment_path
        ).pack(anchor=tk.W, pady=5)
        
        # Path entry
        path_frame = ttk.LabelFrame(frame, text="Deployment Path", padding=10)
        path_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(path_frame, text="Path:").grid(row=0, column=0, sticky='w', pady=5)
        self.deployment_path = ttk.Entry(path_frame, width=60)
        self.deployment_path.insert(0, 'C:\\xampp\\htdocs\\switch')
        self.deployment_path.grid(row=0, column=1, pady=5, padx=10)
        
        ttk.Button(path_frame, text="📂 Browse", command=self._browse_path).grid(
            row=0, column=2, pady=5, padx=5
        )
        
        # FTP settings (hidden by default)
        ftp_frame = ttk.LabelFrame(frame, text="FTP/SFTP Settings", padding=10)
        ftp_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(ftp_frame, text="Host:").grid(row=0, column=0, sticky='w', pady=5)
        self.ftp_host = ttk.Entry(ftp_frame, width=30)
        self.ftp_host.grid(row=0, column=1, pady=5, padx=10)
        
        ttk.Label(ftp_frame, text="Port:").grid(row=1, column=0, sticky='w', pady=5)
        self.ftp_port = ttk.Entry(ftp_frame, width=30)
        self.ftp_port.insert(0, '21')
        self.ftp_port.grid(row=1, column=1, pady=5, padx=10)
        
        ttk.Label(ftp_frame, text="Username:").grid(row=2, column=0, sticky='w', pady=5)
        self.ftp_user = ttk.Entry(ftp_frame, width=30)
        self.ftp_user.grid(row=2, column=1, pady=5, padx=10)
        
        ttk.Label(ftp_frame, text="Password:").grid(row=3, column=0, sticky='w', pady=5)
        self.ftp_password = ttk.Entry(ftp_frame, width=30, show='*')
        self.ftp_password.grid(row=3, column=1, pady=5, padx=10)
        
        ttk.Label(ftp_frame, text="Remote Path:").grid(row=4, column=0, sticky='w', pady=5)
        self.ftp_path = ttk.Entry(ftp_frame, width=30)
        self.ftp_path.insert(0, '/var/www/html/switch')
        self.ftp_path.grid(row=4, column=1, pady=5, padx=10)
        
        # Deploy button
        deploy_frame = ttk.Frame(frame)
        deploy_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(
            deploy_frame,
            text="🚀 Deploy switch/ Folder Now",
            command=self._deploy_files,
            style='Accent.TButton'
        ).pack()
        
        # Status
        self.deploy_status = ttk.Label(frame, text="", foreground='#888888')
        self.deploy_status.pack(pady=10)
        
        # Initialize fields
        self._update_deployment_path()
        
        return frame
    
    def _update_deployment_path(self):
        """Update deployment path based on selection"""
        if self.deployment_type.get() == "xampp":
            self.deployment_path.delete(0, tk.END)
            self.deployment_path.insert(0, 'C:\\xampp\\htdocs\\switch')
            self.deployment_path.config(state='normal')
        elif self.deployment_type.get() == "custom":
            self.deployment_path.config(state='normal')
        elif self.deployment_type.get() == "ftp":
            self.deployment_path.config(state='disabled')
        
        # Show/hide FTP fields
        for widget in [self.ftp_host, self.ftp_port, self.ftp_user, self.ftp_password, self.ftp_path]:
            if self.deployment_type.get() == "ftp":
                widget.config(state='normal')
            else:
                widget.config(state='disabled')
    
    def _browse_path(self):
        """Browse for deployment path"""
        from tkinter import filedialog
        path = filedialog.askdirectory(title="Select Deployment Folder")
        if path:
            self.deployment_path.delete(0, tk.END)
            self.deployment_path.insert(0, path)
    
    def _deploy_files(self):
        """Deploy switch/ folder files"""
        import shutil
        import os
        
        # Find switch folder
        script_dir = os.path.dirname(os.path.abspath(__file__))
        switch_folder = os.path.join(script_dir, 'switch')
        
        if not os.path.exists(switch_folder):
            # Try current directory
            switch_folder = 'switch'
        
        if not os.path.exists(switch_folder):
            messagebox.showerror(
                "Error",
                "switch/ folder not found!\n\n"
                "Please run build_all.bat first to create the switch/ folder."
            )
            return
        
        if self.deployment_type.get() == "xampp":
            dest_path = self.deployment_path.get()
            
            # Create parent directory if needed
            parent_dir = os.path.dirname(dest_path)
            if not os.path.exists(parent_dir):
                if not messagebox.askyesno(
                    "Directory Not Found",
                    f"XAMPP htdocs not found at:\n{parent_dir}\n\n"
                    f"Create directory and continue?"
                ):
                    return
                try:
                    os.makedirs(parent_dir)
                except:
                    pass
            
            try:
                # Copy files
                if os.path.exists(dest_path):
                    shutil.rmtree(dest_path)
                shutil.copytree(switch_folder, dest_path)
                
                self.deploy_status.config(
                    text=f"✓ Deployed to: {dest_path}",
                    foreground='#00ff88'
                )
                messagebox.showinfo(
                    "Success",
                    f"switch/ folder deployed to:\n{dest_path}\n\n"
                    f"Access at: http://localhost/switch/"
                )
            except Exception as e:
                self.deploy_status.config(
                    text=f"✗ Deployment failed",
                    foreground='#ff4444'
                )
                messagebox.showerror("Error", f"Deployment failed:\n{e}")
        
        elif self.deployment_type.get() == "custom":
            dest_path = self.deployment_path.get()
            
            try:
                if os.path.exists(dest_path):
                    shutil.rmtree(dest_path)
                shutil.copytree(switch_folder, dest_path)
                
                self.deploy_status.config(
                    text=f"✓ Deployed to: {dest_path}",
                    foreground='#00ff88'
                )
                messagebox.showinfo(
                    "Success",
                    f"switch/ folder deployed to:\n{dest_path}"
                )
            except Exception as e:
                self.deploy_status.config(
                    text=f"✗ Deployment failed",
                    foreground='#ff4444'
                )
                messagebox.showerror("Error", f"Deployment failed:\n{e}")
        
        elif self.deployment_type.get() == "ftp":
            # FTP deployment instructions
            ftp_instructions = f"""
FTP/SFTP Deployment Instructions
═══════════════════════════════════

Host: {self.ftp_host.get()}
Port: {self.ftp_port.get()}
Username: {self.ftp_user.get()}
Remote Path: {self.ftp_path.get()}

Manual Steps:
1. Connect to your server via FTP/SFTP
2. Navigate to: {self.ftp_path.get()}
3. Upload ALL files from switch/ folder
4. Verify files are uploaded correctly
5. Test: https://{self.ftp_host.get()}/switch/peer_directory_api.php?action=get_stats

Files to upload:
• peer_directory_api.php
• api_handler.php
• setup_central_database.sql
• qwde_config.ini
• index.html
• css/ (folder)
• js/ (folder)
"""
            
            # Save instructions to file
            instruction_file = 'FTP_Deployment_Instructions.txt'
            with open(instruction_file, 'w') as f:
                f.write(ftp_instructions)
            
            self.deploy_status.config(
                text=f"✓ FTP instructions saved to {instruction_file}",
                foreground='#00ff88'
            )
            messagebox.showinfo(
                "FTP Deployment",
                ftp_instructions +
                f"\n\nInstructions saved to: {instruction_file}"
            )
    
    def _create_selfhost_page(self):
        """Create self-hosting guide page"""
        frame = ttk.Frame(self.root, padding=20)
        
        title = ttk.Label(
            frame,
            text="Self-Hosting Guide (Optional)",
            font=('Arial', 14, 'bold')
        )
        title.pack(pady=10)
        
        guide_text = scrolledtext.ScrolledText(frame, height=30, wrap=tk.WORD)
        guide_text.pack(fill=tk.BOTH, expand=True, pady=10)
        
        guide_content = """
═══════════════════════════════════════════════════════════
SELF-HOSTING QWDE CENTRAL DIRECTORY
═══════════════════════════════════════════════════════════

If you want to host your own central directory instead of
using secupgrade.com, follow these steps:

STEP 1: INSTALL XAMPP
───────────────────────────────────────────────────────────
1. Download XAMPP from: https://www.apachefriends.org
2. Install XAMPP to C:\\xampp
3. Start Apache and MySQL from XAMPP Control Panel

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

STEP 3: DEPLOY PHP BACKEND
───────────────────────────────────────────────────────────
1. Copy peer_directory_api.php to:
   C:\\xampp\\htdocs\\api\\peer_directory_api.php

2. Create folder: C:\\xampp\\htdocs\\api\\

3. Edit peer_directory_api.php:
   - Find: $db_config array
   - Set password: 'password' => 'your_mysql_password'

4. Test: http://localhost/api/peer_directory_api.php?action=get_stats

STEP 4: CONFIGURE FIREWALL
───────────────────────────────────────────────────────────
1. Open Windows Firewall
2. Add inbound rule for port 80 (HTTP)
3. Add inbound rule for port 443 (HTTPS if using SSL)
4. Add inbound rule for port 8765 (DDNS server)

STEP 5: SETUP SSL (RECOMMENDED)
───────────────────────────────────────────────────────────
1. Get SSL certificate (Let's Encrypt free)
2. Configure Apache for HTTPS
3. Update config: protocol = https

STEP 6: PORT FORWARDING (FOR EXTERNAL ACCESS)
───────────────────────────────────────────────────────────
1. Open router admin panel
2. Forward port 80 to your PC's IP
3. Forward port 8765 to your PC's IP
4. Use Dynamic DNS (No-IP, DuckDNS) for domain

STEP 7: UPDATE CONFIGURATION
───────────────────────────────────────────────────────────
In this wizard, select:
  - Server Type: "Host your own central server"
  - Host: Your public IP or domain
  - Port: 80 (HTTP) or 443 (HTTPS)
  - API Path: /api/peer_directory_api.php

═══════════════════════════════════════════════════════════

WEBSITE FILES NEEDED:
───────────────────────────────────────────────────────────
Upload these to your web server:

1. peer_directory_api.php  (Main API handler)
2. setup_central_database.sql  (Database setup)

Optional:
3. qwde_config.ini  (Configuration template)
4. START_HERE.txt  (Setup instructions for users)

═══════════════════════════════════════════════════════════

TESTING YOUR SETUP:
───────────────────────────────────────────────────────────
1. Test API: http://your-domain.com/api/peer_directory_api.php?action=get_stats
2. Expected: {"status":"success","total_peers":0,...}
3. If error: Check database connection in PHP file

═══════════════════════════════════════════════════════════

MIRROR SERVER SETUP (OPTIONAL):
───────────────────────────────────────────────────────────
1. Install Python 3.8+
2. Install dependencies:
   pip install -r requirements.txt
3. Run mirror server:
   python qwde_mirror_server.py
4. Configure in this wizard (Step 5)

═══════════════════════════════════════════════════════════

NEED HELP?
───────────────────────────────────────────────────────────
• Check documentation in output/Documentation/
• Review SYSTEM_DIAGRAM.md for architecture
• Check logs for error messages
• Test with localhost first before going live

═══════════════════════════════════════════════════════════
"""
        
        guide_text.insert('1.0', guide_content)
        guide_text.config(state='disabled')
        
        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        def open_phpmyadmin():
            import webbrowser
            webbrowser.open('http://localhost/phpmyadmin')
        
        ttk.Button(
            btn_frame,
            text="🌐 Open phpMyAdmin",
            command=open_phpmyadmin
        ).pack(side=tk.LEFT, padx=5)
        
        def open_xampp():
            import os
            os.startfile('C:\\xampp\\xampp-control.exe')
        
        ttk.Button(
            btn_frame,
            text="⚙️ Open XAMPP Control",
            command=open_xampp
        ).pack(side=tk.LEFT, padx=5)
        
        def copy_setup_sql():
            import shutil
            try:
                shutil.copy('setup_central_database.sql', 'C:\\xampp\\htdocs\\')
                messagebox.showinfo(
                    "Success",
                    "setup_central_database.sql copied to:\n"
                    "C:\\xampp\\htdocs\\\n\n"
                    "You can now import it in phpMyAdmin!"
                )
            except Exception as e:
                messagebox.showerror("Error", f"Failed to copy file:\n{e}")
        
        ttk.Button(
            btn_frame,
            text="📋 Copy SQL to htdocs",
            command=copy_setup_sql
        ).pack(side=tk.LEFT, padx=5)
        
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
        elif self.server_type.get() == "switch":
            self.central_host.delete(0, tk.END)
            self.central_host.insert(0, 'secupgrade.com')
            self.central_path.delete(0, tk.END)
            self.central_path.insert(0, '/switch')
        else:  # self_hosted
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
                protocol = self.config.get('central_server', 'protocol', fallback='https')
                host = self.config.get('central_server', 'host', fallback='secupgrade.com')
                path = self.config.get('central_server', 'api_path', fallback='/peer_directory_api.php')
                
                self.central_protocol.set(protocol)
                self.central_host.delete(0, tk.END)
                self.central_host.insert(0, host)
                self.central_port.set(self.config.get('central_server', 'port', fallback='443'))
                self.central_path.delete(0, tk.END)
                self.central_path.insert(0, path)
                
                # Determine server type from saved config
                if host == 'secupgrade.com' and path == '/switch':
                    self.server_type.set('switch')
                elif host == 'secupgrade.com':
                    self.server_type.set('external')
                else:
                    self.server_type.set('self_hosted')

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
        if self.db_type.get() == "sqlite":
            # Test SQLite
            try:
                conn = sqlite3.connect(self.db_sqlite_path.get())
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                conn.close()
                messagebox.showinfo(
                    "Success",
                    f"SQLite database connection successful!\n\n"
                    f"File: {os.path.abspath(self.db_sqlite_path.get())}"
                )
            except Exception as e:
                messagebox.showerror(
                    "Connection Failed",
                    f"Could not connect to SQLite database:\n\n{e}"
                )
        else:
            # Test MySQL
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
                        "MySQL database connection successful!\n\n"
                        f"Host: {self.db_host.get()}:{self.db_port.get()}\n"
                        f"Database: {self.db_name.get()}"
                    )
                    connection.close()
            except Error as e:
                messagebox.showerror(
                    "Connection Failed",
                    f"Could not connect to MySQL database:\n\n{e}"
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

        if 'database' not in self.config:
            self.config['database'] = {}
        self.config['database']['type'] = self.db_type.get()
        self.config['database']['sqlite_path'] = self.db_sqlite_path.get()
        
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
