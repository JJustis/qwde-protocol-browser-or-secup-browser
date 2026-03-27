"""
QWDE Protocol - Full Mirror Server
Downloads ALL sites from ALL peers and caches them
Serves as fallback when peers are offline
Detects site updates via hash/size changes
"""

import socket
import threading
import json
import time
import os
import hashlib
import requests
from typing import Dict, List, Optional
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FullMirrorServer:
    """
    Full mirror server that:
    1. Queries central API for ALL peers and sites
    2. Downloads ALL sites from ALL peers
    3. Stores everything locally (full mirror)
    4. Serves to clients when peers are offline
    5. Detects updates via hash/size changes
    6. Auto-updates cached sites when changes detected
    """
    
    CENTRAL_API = 'https://secupgrade.com/api_handler.php'
    MIRROR_DIR = 'full_mirror'
    P2P_PORT = 8766
    
    def __init__(self, central_api_url: str = None, port: int = 8765):
        self.central_api = central_api_url or self.CENTRAL_API
        self.port = port
        self.mirror_dir = self.MIRROR_DIR
        
        # Local state
        self.peers: Dict[str, dict] = {}  # peer_id -> {ip, port, last_seen, sites}
        self.sites: Dict[str, dict] = {}  # domain -> metadata from central API
        self.site_cache: Dict[str, bytes] = {}  # domain -> content
        self.site_versions: Dict[str, dict] = {}  # domain -> {hash, size, version, timestamp}
        
        # Statistics
        self.stats = {
            'total_peers_known': 0,
            'total_sites_known': 0,
            'sites_cached': 0,
            'sites_updated': 0,
            'last_sync': None,
            'last_full_download': None
        }
        
        # Ensure mirror directory exists
        os.makedirs(self.mirror_dir, exist_ok=True)
        os.makedirs(os.path.join(self.mirror_dir, 'sites'), exist_ok=True)
        
        # Start background threads
        self._start_metadata_sync()
        self._start_full_download_loop()
        self._start_update_detection()
    
    def _start_metadata_sync(self):
        """Sync metadata from central API every 30 seconds"""
        def sync_loop():
            while True:
                try:
                    self._sync_metadata()
                    self.stats['last_sync'] = datetime.now().isoformat()
                except Exception as e:
                    logger.error(f"Metadata sync error: {e}")
                time.sleep(30)  # Every 30 seconds
        
        thread = threading.Thread(target=sync_loop, daemon=True)
        thread.start()
        logger.info("Metadata sync started (30s interval)")
    
    def _start_full_download_loop(self):
        """Download ALL sites from ALL peers every 5 minutes"""
        def download_loop():
            while True:
                try:
                    self._download_all_sites()
                    self.stats['last_full_download'] = datetime.now().isoformat()
                except Exception as e:
                    logger.error(f"Full download error: {e}")
                time.sleep(300)  # Every 5 minutes
        
        thread = threading.Thread(target=download_loop, daemon=True)
        thread.start()
        logger.info("Full site download started (5min interval)")
    
    def _start_update_detection(self):
        """Check for site updates every 60 seconds"""
        def detect_loop():
            while True:
                try:
                    self._detect_and_update_changes()
                except Exception as e:
                    logger.error(f"Update detection error: {e}")
                time.sleep(60)  # Every 60 seconds
        
        thread = threading.Thread(target=detect_loop, daemon=True)
        thread.start()
        logger.info("Update detection started (60s interval)")
    
    def _sync_metadata(self):
        """Sync all metadata from central API"""
        try:
            # Get peer list
            response = requests.get(
                self.central_api,
                params={'action': 'get_peers', 'limit': '200'},
                timeout=10
            )
            data = response.json()
            
            if data.get('status') == 'success':
                old_peer_count = len(self.peers)
                self.peers = {}
                for peer in data.get('peers', []):
                    peer_id = peer.get('peer_id')
                    self.peers[peer_id] = {
                        'ip': peer.get('peer_ip'),
                        'port': peer.get('peer_port', self.P2P_PORT),
                        'last_seen': peer.get('last_seen'),
                        'is_online': True,
                        'sites': []
                    }
                
                new_peer_count = len(self.peers)
                if new_peer_count != old_peer_count:
                    logger.info(f"Peers changed: {old_peer_count} → {new_peer_count}")
            
            # Get all site metadata
            response = requests.get(
                self.central_api,
                params={'action': 'sync_sites'},
                timeout=10
            )
            data = response.json()
            
            if data.get('status') == 'success':
                old_site_count = len(self.sites)
                self.sites = {}
                
                for site in data.get('sites', []):
                    domain = site.get('domain')
                    self.sites[domain] = site
                    
                    # Update peer's site list
                    creator = site.get('creator_peer_id')
                    if creator in self.peers:
                        if domain not in self.peers[creator]['sites']:
                            self.peers[creator]['sites'].append(domain)
                    
                    # Check for updates
                    if domain in self.site_versions:
                        old_version = self.site_versions[domain]
                        new_hash = site.get('site_hash')
                        new_size = site.get('site_size')
                        
                        if old_version.get('hash') != new_hash or old_version.get('size') != new_size:
                            logger.warning(f"Site update detected: {domain}")
                            logger.info(f"  Old: hash={old_version.get('hash')[:16]}..., size={old_version.get('size')}")
                            logger.info(f"  New: hash={new_hash[:16] if new_hash else 'N/A'}..., size={new_size}")
                            # Will be updated in next download cycle
                
                self.stats['total_sites_known'] = len(self.sites)
                self.stats['total_peers_known'] = len(self.peers)
                
                if len(self.sites) != old_site_count:
                    logger.info(f"Sites changed: {old_site_count} → {len(self.sites)}")
                    
        except Exception as e:
            logger.error(f"Failed to sync metadata: {e}")
    
    def _download_all_sites(self):
        """Download ALL sites from ALL peers"""
        logger.info(f"Starting full download of {len(self.sites)} sites...")
        
        downloaded = 0
        failed = 0
        
        for domain, site_meta in self.sites.items():
            try:
                # Check if we need to download
                if domain in self.site_cache:
                    # Already cached, check if update needed
                    current_hash = site_meta.get('site_hash')
                    current_size = site_meta.get('site_size')
                    cached_version = self.site_versions.get(domain, {})
                    
                    if (cached_version.get('hash') == current_hash and 
                        cached_version.get('size') == current_size):
                        # No update needed
                        continue
                
                # Download from peer
                if self._download_site_from_peer(domain, site_meta):
                    downloaded += 1
                else:
                    failed += 1
                    
            except Exception as e:
                logger.error(f"Error downloading {domain}: {e}")
                failed += 1
        
        self.stats['sites_cached'] = len(self.site_cache)
        logger.info(f"Full download complete: {downloaded} downloaded, {failed} failed")
    
    def _download_site_from_peer(self, domain: str, site_meta: dict) -> bool:
        """
        Download site from peer's IP
        
        Returns:
            True if successful, False otherwise
        """
        creator_peer = site_meta.get('creator_peer_id')
        
        if creator_peer not in self.peers:
            logger.warning(f"Peer offline: {creator_peer}, trying cached version")
            return False
        
        peer_info = self.peers[creator_peer]
        peer_ip = peer_info['ip']
        peer_port = peer_info['port']
        
        logger.info(f"Downloading {domain} from {peer_ip}:{peer_port}")
        
        try:
            # Connect directly to peer's P2P port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(15)
            sock.connect((peer_ip, peer_port))
            
            # Send request
            request = {
                'action': 'get_site',
                'domain': domain
            }
            sock.send(json.dumps(request).encode())
            
            # Receive response
            response_data = b''
            sock.settimeout(30)
            while True:
                chunk = sock.recv(8192)
                if not chunk:
                    break
                response_data += chunk
                # Check if we have complete JSON
                try:
                    temp_decode = response_data.decode('utf-8')
                    if temp_decode.endswith('}'):
                        json.loads(temp_decode)
                        break
                except:
                    continue
            
            sock.close()
            
            # Parse response
            response = json.loads(response_data.decode('utf-8'))
            
            if response.get('status') == 'success':
                content = bytes.fromhex(response.get('content', ''))
                
                # Verify hash
                content_hash = hashlib.sha256(content).hexdigest()
                expected_hash = site_meta.get('site_hash')
                
                if expected_hash and content_hash != expected_hash:
                    logger.error(f"Hash mismatch for {domain}")
                    logger.error(f"  Expected: {expected_hash[:16]}...")
                    logger.error(f"  Got:      {content_hash[:16]}...")
                    return False
                
                # Cache in memory
                self.site_cache[domain] = content
                
                # Save version info
                self.site_versions[domain] = {
                    'hash': content_hash,
                    'size': len(content),
                    'version': site_meta.get('version', 1),
                    'timestamp': time.time(),
                    'downloaded_from': f"{peer_ip}:{peer_port}"
                }
                
                # Save to disk
                self._save_to_disk(domain, content)
                
                logger.info(f"✓ Downloaded and cached: {domain} ({len(content)} bytes)")
                return True
            else:
                logger.error(f"Peer returned error for {domain}: {response.get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to download {domain} from peer: {e}")
            
            # Try from disk cache if available
            cached = self._load_from_disk(domain)
            if cached:
                logger.info(f"Using disk cache for {domain}")
                self.site_cache[domain] = cached
                return True
            
            return False
    
    def _save_to_disk(self, domain: str, content: bytes):
        """Save site content to disk"""
        safe_domain = domain.replace('/', '_').replace('\\', '_').replace(':', '_')
        filepath = os.path.join(self.mirror_dir, 'sites', f"{safe_domain}.dat")
        
        with open(filepath, 'wb') as f:
            f.write(content)
        
        # Save metadata
        meta_path = filepath + '.meta'
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(self.site_versions.get(domain, {}), f, indent=2)
    
    def _load_from_disk(self, domain: str) -> Optional[bytes]:
        """Load site content from disk"""
        safe_domain = domain.replace('/', '_').replace('\\', '_').replace(':', '_')
        filepath = os.path.join(self.mirror_dir, 'sites', f"{safe_domain}.dat")
        
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                return f.read()
        return None
    
    def _detect_and_update_changes(self):
        """Detect site changes and update cache"""
        for domain, site_meta in self.sites.items():
            current_hash = site_meta.get('site_hash')
            current_size = site_meta.get('site_size')
            current_version = site_meta.get('version', 1)
            
            if domain not in self.site_versions:
                # Not cached yet, download
                logger.info(f"New site detected: {domain}")
                self._download_site_from_peer(domain, site_meta)
                continue
            
            cached_version = self.site_versions[domain]
            
            # Check if hash or size changed
            if (cached_version.get('hash') != current_hash or 
                cached_version.get('size') != current_size or
                cached_version.get('version') != current_version):
                
                logger.warning(f"Site update detected: {domain}")
                logger.info(f"  Cached:  v{cached_version.get('version')}, size={cached_version.get('size')}")
                logger.info(f"  Current: v{current_version}, size={current_size}")
                
                # Download updated version
                if self._download_site_from_peer(domain, site_meta):
                    self.stats['sites_updated'] += 1
                    logger.info(f"✓ Updated: {domain}")
    
    def get_site(self, domain: str) -> Optional[dict]:
        """
        Get site content (from cache, disk, or download from peer)
        
        Returns:
            dict with content and metadata
        """
        # Check memory cache
        if domain in self.site_cache:
            logger.info(f"Cache hit: {domain}")
            return {
                'status': 'success',
                'content': self.site_cache[domain].hex(),
                'source': 'memory_cache',
                'version': self.site_versions.get(domain, {}).get('version', 1)
            }
        
        # Check disk cache
        cached = self._load_from_disk(domain)
        if cached:
            logger.info(f"Disk cache hit: {domain}")
            self.site_cache[domain] = cached
            return {
                'status': 'success',
                'content': cached.hex(),
                'source': 'disk_cache',
                'version': self.site_versions.get(domain, {}).get('version', 1)
            }
        
        # Download from peer
        logger.info(f"Cache miss, downloading: {domain}")
        site_meta = self.sites.get(domain)
        
        if site_meta and self._download_site_from_peer(domain, site_meta):
            return {
                'status': 'success',
                'content': self.site_cache[domain].hex(),
                'source': 'peer_download',
                'version': self.site_versions.get(domain, {}).get('version', 1)
            }
        
        return {'status': 'not_found', 'message': f'Site not found: {domain}'}
    
    def handle_api_request(self, action: str, params: dict) -> dict:
        """Handle API requests"""
        if action == 'get_site':
            domain = params.get('domain')
            if domain:
                return self.get_site(domain)
            return {'status': 'error', 'message': 'Missing domain'}
        
        elif action == 'sync_sites':
            return {
                'status': 'success',
                'sites': list(self.sites.values()),
                'count': len(self.sites),
                'cached': len(self.site_cache),
                'source': 'mirror_server'
            }
        
        elif action == 'get_stats':
            return {
                'status': 'success',
                **self.stats,
                'memory_cache_size': len(self.site_cache),
                'server_type': 'full_mirror'
            }
        
        elif action == 'check_update':
            # Check if site has updates
            domain = params.get('domain')
            if domain and domain in self.sites:
                current = self.sites[domain]
                cached = self.site_versions.get(domain, {})
                
                has_update = (
                    cached.get('hash') != current.get('site_hash') or
                    cached.get('size') != current.get('site_size') or
                    cached.get('version') != current.get('version')
                )
                
                return {
                    'status': 'success',
                    'domain': domain,
                    'has_update': has_update,
                    'cached_version': cached.get('version', 0),
                    'current_version': current.get('version', 1),
                    'cached_size': cached.get('size', 0),
                    'current_size': current.get('site_size', 0)
                }
            
            return {'status': 'error', 'message': 'Unknown site'}
        
        return {'status': 'error', 'message': 'Unknown action'}


class MirrorHTTPHandler(BaseHTTPRequestHandler):
    """HTTP handler for mirror server"""
    
    mirror_server = None
    
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        params = {k: v[0] if len(v) == 1 else v for k, v in params.items()}
        
        action = params.get('action')
        
        if action and self.mirror_server:
            result = self.mirror_server.handle_api_request(action, params)
            self._send_json_response(result)
        else:
            self._send_json_response({'status': 'error', 'message': 'Missing action'})
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        params = {}
        for item in post_data.decode().split('&'):
            if '=' in item:
                key, value = item.split('=', 1)
                params[key] = value
        
        action = params.get('action')
        
        if action and self.mirror_server:
            result = self.mirror_server.handle_api_request(action, params)
            self._send_json_response(result)
        else:
            self._send_json_response({'status': 'error', 'message': 'Missing action'})
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def _send_json_response(self, data: dict):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def log_message(self, format, *args):
        pass


def run_mirror_server(central_api: str = None, port: int = 8765):
    """Run the full mirror server"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║      QWDE Protocol - Full Mirror Server                   ║
╠═══════════════════════════════════════════════════════════╣
║  Features:                                                ║
║    • Downloads ALL sites from ALL peers                  ║
║    • Stores everything locally (full mirror)             ║
║    • Serves when peers are offline                       ║
║    • Detects updates via hash/size changes               ║
║    • Auto-updates cached sites                           ║
║                                                           ║
║  Sync Intervals:                                          ║
║    • Metadata: Every 30 seconds                          ║
║    • Full Download: Every 5 minutes                      ║
║    • Update Detection: Every 60 seconds                  ║
║                                                           ║
║  Central API: {}                     ║
║  Listening: http://localhost:{}                          ║
╚═══════════════════════════════════════════════════════════╝
    """.format(central_api or 'https://secupgrade.com', port))
    
    mirror = FullMirrorServer(central_api_url=central_api, port=port)
    MirrorHTTPHandler.mirror_server = mirror
    
    server = HTTPServer(('0.0.0.0', port), MirrorHTTPHandler)
    
    print(f"\n[+] Mirror server started on port {port}")
    print(f"[+] Downloading all sites from all peers...")
    print(f"[+] Press Ctrl+C to stop\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        server.shutdown()
        print(f"[✓] Server stopped")
        print(f"[✓] Total sites cached: {len(mirror.site_cache)}")


if __name__ == '__main__':
    central_api = 'https://secupgrade.com/api_handler.php'
    run_mirror_server(central_api=central_api, port=8765)
