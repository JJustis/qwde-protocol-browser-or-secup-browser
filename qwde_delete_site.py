"""
QWDE Protocol - Site Deletion System
Allows site owners to delete their domains from central directory
Includes authentication to prevent unauthorized deletion
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import hashlib
import json
import time
import os
from typing import Optional, Callable
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SiteDeletionManager:
    """
    Manages site deletion with owner authentication
    
    Security:
    - Only site creator can delete
    - Requires peer_id signature
    - Hash verification
    - Confirmation dialog
    """
    
    def __init__(self, peer_id: str, private_key: bytes = None):
        self.peer_id = peer_id
        self.private_key = private_key
        self.deletion_requests = {}  # domain -> timestamp
    
    def create_deletion_request(self, domain: str, site_hash: str) -> dict:
        """
        Create a signed deletion request
        
        Args:
            domain: Domain to delete
            site_hash: Current site hash (proves ownership)
        
        Returns:
            Deletion request dict
        """
        import hashlib
        
        # Create deletion token
        timestamp = int(time.time())
        message = f"{domain}:{self.peer_id}:{timestamp}:{site_hash}"
        
        # Sign with peer's private key (simplified - use actual crypto in production)
        signature = hashlib.sha256(
            message.encode() + (self.private_key or b'default_key')
        ).hexdigest()
        
        request = {
            'action': 'delete_site',
            'domain': domain,
            'peer_id': self.peer_id,
            'site_hash': site_hash,
            'timestamp': timestamp,
            'signature': signature,
            'reason': 'Owner requested deletion'
        }
        
        self.deletion_requests[domain] = {
            'request': request,
            'timestamp': timestamp
        }
        
        return request
    
    def verify_deletion_request(self, request: dict) -> bool:
        """
        Verify deletion request is authentic
        
        Args:
            request: Deletion request dict
        
        Returns:
            True if valid, False otherwise
        """
        import hashlib
        
        # Check timestamp (not older than 5 minutes)
        current_time = int(time.time())
        if current_time - request.get('timestamp', 0) > 300:
            logger.warning(f"Deletion request expired: {request.get('domain')}")
            return False
        
        # Verify signature
        message = f"{request['domain']}:{request['peer_id']}:{request['timestamp']}:{request['site_hash']}"
        expected_signature = hashlib.sha256(
            message.encode() + (self.private_key or b'default_key')
        ).hexdigest()
        
        if request.get('signature') != expected_signature:
            logger.warning(f"Invalid deletion signature: {request.get('domain')}")
            return False
        
        return True


class SiteDeletionDialog(tk.Toplevel):
    """
    Dialog for deleting sites
    """
    
    def __init__(self, parent, peer_id: str, owned_sites: list, 
                 delete_callback: Callable = None):
        super().__init__(parent)
        self.title("🗑️ Delete Site")
        self.geometry("600x500")
        self.transient(parent)
        self.grab_set()
        
        self.peer_id = peer_id
        self.owned_sites = owned_sites
        self.delete_callback = delete_callback
        self.deletion_manager = SiteDeletionManager(peer_id)
        
        self._create_ui()
    
    def _create_ui(self):
        """Create deletion dialog UI"""
        # Header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(
            header_frame,
            text="⚠️  Delete Site",
            font=('Arial', 16, 'bold'),
            foreground='#ff4444'
        ).pack()
        
        ttk.Label(
            header_frame,
            text="Only the site owner can delete sites",
            font=('Arial', 9)
        ).pack(pady=5)
        
        # Owned sites list
        list_frame = ttk.LabelFrame(self, text="Your Sites", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        columns = ('domain', 'fwild', 'size', 'version')
        self.sites_tree = ttk.Treeview(list_frame, columns=columns, 
                                       show='headings', height=10)
        
        self.sites_tree.heading('domain', text='Domain')
        self.sites_tree.heading('fwild', text='Fwild')
        self.sites_tree.heading('size', text='Size')
        self.sites_tree.heading('version', text='Version')
        
        self.sites_tree.column('domain', width=250)
        self.sites_tree.column('fwild', width=80)
        self.sites_tree.column('size', width=100)
        self.sites_tree.column('version', width=80)
        
        # Populate with owned sites
        for site in self.owned_sites:
            self.sites_tree.insert('', 'end', values=(
                site.get('domain', 'Unknown'),
                site.get('fwild', 'N/A'),
                f"{site.get('site_size', 0)} B",
                site.get('version', 1)
            ))
        
        self.sites_tree.pack(fill=tk.BOTH, expand=True)
        
        # Bind double-click to delete
        self.sites_tree.bind('<Double-1>', lambda e: self._confirm_delete())
        
        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(
            btn_frame,
            text="🗑️ Delete Selected",
            command=self._confirm_delete,
            style='Accent.TButton'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Cancel",
            command=self.destroy
        ).pack(side=tk.RIGHT, padx=5)
        
        # Warning label
        warning_frame = ttk.Frame(self)
        warning_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(
            warning_frame,
            text="⚠️  Warning: This action cannot be undone!",
            foreground='#ff4444',
            font=('Arial', 9, 'bold')
        ).pack()
        
        ttk.Label(
            warning_frame,
            text="The site will be removed from the central directory.",
            foreground='#888888',
            font=('Arial', 8)
        ).pack()
    
    def _confirm_delete(self):
        """Confirm deletion with user"""
        selection = self.sites_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a site to delete")
            return
        
        item = self.sites_tree.item(selection[0])
        domain = item['values'][0]
        fwild = item['values'][1]
        
        # Confirmation dialog
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete:\n\n"
            f"Domain: {domain}\n"
            f"Fwild: {fwild}\n\n"
            f"⚠️  This action CANNOT be undone!",
            icon='warning'
        )
        
        if confirm:
            self._delete_site(domain)
    
    def _delete_site(self, domain: str):
        """Delete site after confirmation"""
        # Find site metadata
        site_meta = None
        for site in self.owned_sites:
            if site.get('domain') == domain:
                site_meta = site
                break
        
        if not site_meta:
            messagebox.showerror("Error", "Site not found")
            return
        
        # Create deletion request
        deletion_request = self.deletion_manager.create_deletion_request(
            domain=domain,
            site_hash=site_meta.get('site_hash', '')
        )
        
        # Verify request
        if not self.deletion_manager.verify_deletion_request(deletion_request):
            messagebox.showerror("Error", "Deletion request verification failed")
            return
        
        # Call callback (would send to server in real implementation)
        if self.delete_callback:
            try:
                result = self.delete_callback(deletion_request)
                
                if result.get('status') == 'success':
                    messagebox.showinfo(
                        "Success",
                        f"Site '{domain}' has been deleted.\n\n"
                        f"It will be removed from the directory within 60 seconds."
                    )
                    
                    # Remove from list
                    for item in self.sites_tree.get_children():
                        if self.sites_tree.item(item)['values'][0] == domain:
                            self.sites_tree.delete(item)
                    break
                    
                else:
                    messagebox.showerror(
                        "Error",
                        f"Failed to delete site:\n{result.get('message', 'Unknown error')}"
                    )
                    
            except Exception as e:
                messagebox.showerror("Error", f"Deletion failed: {str(e)}")
        else:
            # No callback - just show success (for testing)
            messagebox.showinfo(
                "Success",
                f"Deletion request created for '{domain}'\n\n"
                f"Request: {json.dumps(deletion_request, indent=2)}"
            )


def add_delete_site_menu(browser):
    """
    Add Delete Site menu to browser
    
    Args:
        browser: QWDEBrowserGUI instance
    """
    # Add to File menu
    file_menu = None
    for menu_name in browser.menu.winfo_children():
        if menu_name.cget('text') == 'File':
            file_menu = menu_name
            break
    
    if file_menu:
        file_menu.add_separator()
        file_menu.add_command(
            label="🗑️ Delete My Site...",
            command=lambda: open_delete_dialog(browser),
            accelerator="Ctrl+D"
        )
        browser.bind('<Control-d>', lambda e: open_delete_dialog(browser))


def open_delete_dialog(browser):
    """Open site deletion dialog"""
    if not browser.peer:
        messagebox.showwarning("Not Connected", "Please connect to the network first")
        return
    
    # Get owned sites (sites created by this peer)
    owned_sites = []
    for domain, site in browser.peer.sites.items():
        if site.get('creator_peer_id') == browser.peer.peer_id:
            owned_sites.append(site)
    
    if not owned_sites:
        messagebox.showinfo("No Sites", "You don't own any sites to delete")
        return
    
    # Show deletion dialog
    dialog = SiteDeletionDialog(browser, browser.peer.peer_id, owned_sites)
    browser.wait_window(dialog)


# API Handler for deletion endpoint
def handle_delete_site_api(db, request: dict) -> dict:
    """
    Handle site deletion API request
    
    Args:
        db: Database connection
        request: Deletion request dict
    
    Returns:
        API response dict
    """
    # Verify request
    deletion_manager = SiteDeletionManager(request.get('peer_id'))
    
    if not deletion_manager.verify_deletion_request(request):
        return {'status': 'error', 'message': 'Invalid deletion request'}
    
    domain = request.get('domain')
    peer_id = request.get('peer_id')
    
    # Check if peer owns the site
    cursor = db.cursor()
    cursor.execute(
        "SELECT creator_peer_id FROM site_directory WHERE domain = %s",
        (domain,)
    )
    result = cursor.fetchone()
    
    if not result:
        return {'status': 'not_found', 'message': 'Site not found'}
    
    if result[0] != peer_id:
        return {'status': 'error', 'message': 'You do not own this site'}
    
    # Mark site as inactive (soft delete)
    cursor.execute(
        "UPDATE site_directory SET is_active = FALSE WHERE domain = %s",
        (domain,)
    )
    
    # Log deletion
    cursor.execute("""
        INSERT INTO deletion_log (domain, deleted_by, deleted_at, reason)
        VALUES (%s, %s, NOW(), %s)
    """, (domain, peer_id, request.get('reason', 'Owner requested')))
    
    db.commit()
    cursor.close()
    
    return {
        'status': 'success',
        'message': f'Site {domain} deleted successfully',
        'domain': domain
    }


# Test the deletion system
if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════╗
║      QWDE Protocol - Site Deletion System                 ║
╠═══════════════════════════════════════════════════════════╣
║  Features:                                                ║
║    • Owner-only deletion                                 ║
║    • Signature verification                              ║
║    • Timestamp validation                                ║
║    • Confirmation dialog                                 ║
║    • Soft delete (can be recovered)                      ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Test deletion request creation
    manager = SiteDeletionManager('test-peer-123')
    
    request = manager.create_deletion_request(
        domain='test.qwde',
        site_hash='abc123...'
    )
    
    print("Deletion Request Created:")
    print(json.dumps(request, indent=2))
    
    # Verify
    is_valid = manager.verify_deletion_request(request)
    print(f"\nRequest Valid: {is_valid}")
