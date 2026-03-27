"""
QWDE Protocol - Peer Network with PHP Backend Integration
Uses custom QWDE encryption for all communications
PHP backend handles MySQL storage with 30-second polling
"""

import socket
import threading
import json
import time
import hashlib
import os
import uuid
import requests
from typing import Dict, List, Optional, Callable, Set
from dataclasses import dataclass, field
import logging
import queue

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class SiteUpdate:
    """Represents a site update event"""
    domain: str
    fwild: int
    site_data: bytes
    timestamp: float
    source_peer: str


@dataclass
class PeerConnection:
    """Represents a connection to another peer"""
    peer_id: str
    host: str
    port: int
    socket: socket.socket = None
    last_activity: float = 0
    is_connected: bool = False
    sites_count: int = 0
    public_key: str = None


class PinWheelConnection:
    """
    Pin Wheel Connection System
    Manages connections to multiple peers in a rotating fashion
    """
    
    def __init__(self, max_connections: int = 8):
        self.max_connections = max_connections
        self.connections: Dict[str, PeerConnection] = {}
        self.current_index = 0
        self.lock = threading.Lock()
        self.rotation_interval = 30
    
    def add_connection(self, peer_id: str, host: str, port: int, public_key: str = None) -> bool:
        """Add a new peer connection"""
        with self.lock:
            if len(self.connections) >= self.max_connections:
                self._remove_oldest()
            
            conn = PeerConnection(
                peer_id=peer_id,
                host=host,
                port=port,
                public_key=public_key,
                last_activity=time.time()
            )
            self.connections[peer_id] = conn
            logger.info(f"Added peer connection: {peer_id} at {host}:{port}")
            return True
    
    def remove_connection(self, peer_id: str) -> bool:
        """Remove a peer connection"""
        with self.lock:
            if peer_id in self.connections:
                conn = self.connections[peer_id]
                if conn.socket:
                    try:
                        conn.socket.close()
                    except:
                        pass
                del self.connections[peer_id]
                logger.info(f"Removed peer connection: {peer_id}")
                return True
            return False
    
    def _remove_oldest(self):
        """Remove the oldest connection"""
        if not self.connections:
            return
        oldest_id = min(self.connections.keys(),
                       key=lambda k: self.connections[k].last_activity)
        self.remove_connection(oldest_id)
    
    def get_next_peer(self) -> Optional[PeerConnection]:
        """Get next peer in rotation (pin wheel)"""
        with self.lock:
            if not self.connections:
                return None
            
            peers = list(self.connections.values())
            conn = peers[self.current_index % len(peers)]
            self.current_index = (self.current_index + 1) % len(peers)
            conn.last_activity = time.time()
            return conn
    
    def get_all_peers(self) -> List[PeerConnection]:
        """Get all connected peers"""
        with self.lock:
            return list(self.connections.values())
    
    def update_activity(self, peer_id: str):
        """Update last activity time"""
        with self.lock:
            if peer_id in self.connections:
                self.connections[peer_id].last_activity = time.time()
    
    def get_connection_count(self) -> int:
        """Get number of active connections"""
        with self.lock:
            return len(self.connections)


class HTTPBackendClient:
    """
    Client for PHP backend with 30-second polling
    Handles all communication with the central MySQL database
    """
    
    def __init__(self, base_url: str = 'http://localhost/qwde_ddns_api.php',
                 timeout: float = 10.0):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'QWDE-Protocol/1.0'
        })
        
        # Polling state
        self.last_check_time = time.time()
        self.polling_interval = 30  # Query every 30 seconds
        self._polling_active = False
        self._poll_thread = None
        self._new_site_callbacks: List[Callable] = []
    
    def _make_request(self, params: dict = None, data: dict = None, 
                     peer_id: str = None) -> dict:
        """Make HTTP request to PHP backend"""
        try:
            headers = {}
            if peer_id:
                headers['X-QWDE-Peer-ID'] = peer_id
            
            if data:
                response = self.session.post(
                    self.base_url,
                    params=params,
                    data=data,
                    timeout=self.timeout,
                    headers=headers
                )
            else:
                response = self.session.get(
                    self.base_url,
                    params=params,
                    timeout=self.timeout,
                    headers=headers
                )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.error("Request timeout")
            return {'status': 'error', 'message': 'Request timeout'}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            return {'status': 'error', 'message': f'Connection error: {e}'}
        except Exception as e:
            logger.error(f"Request error: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def register_peer(self, peer_id: str, host: str, port: int, 
                     public_key: str = None, sites: List[str] = None) -> bool:
        """Register peer with PHP backend"""
        data = {
            'action': 'register_peer',
            'peer_id': peer_id,
            'host': host,
            'port': str(port),
            'sites': json.dumps(sites or [])
        }
        if public_key:
            data['public_key'] = public_key
        
        result = self._make_request(data=data, peer_id=peer_id)
        return result.get('status') == 'success'
    
    def heartbeat(self, peer_id: str) -> bool:
        """Send heartbeat"""
        data = {
            'action': 'register_peer',  # Re-register to update last_seen
            'peer_id': peer_id,
            'host': '0.0.0.0',
            'port': '0'
        }
        result = self._make_request(data=data, peer_id=peer_id)
        return result.get('status') == 'success'
    
    def get_peers(self, limit: int = 10) -> List[dict]:
        """Get active peers"""
        params = {'action': 'get_peers', 'limit': str(limit)}
        result = self._make_request(params=params)
        return result.get('peers', []) if result.get('status') == 'success' else []
    
    def register_site(self, domain: str, creator_peer_id: str, 
                     encrypted_site_data: bytes, metadata: dict = None) -> Optional[dict]:
        """Register encrypted site with backend"""
        data = {
            'action': 'register_site',
            'domain': domain,
            'creator_peer_id': creator_peer_id,
            'site_data_encrypted': encrypted_site_data.hex()
        }
        if metadata:
            data['encryption_metadata'] = json.dumps(metadata)
        
        result = self._make_request(data=data, peer_id=creator_peer_id)
        
        if result.get('status') == 'success':
            return {
                'fwild': result.get('fwild'),
                'version': result.get('version'),
                'updated': result.get('updated', False)
            }
        return None
    
    def get_site(self, domain: str) -> Optional[dict]:
        """Get site by domain"""
        params = {'action': 'get_site', 'domain': domain}
        result = self._make_request(params=params)
        return result.get('site') if result.get('status') == 'success' else None
    
    def get_site_by_fwild(self, fwild: int) -> Optional[dict]:
        """Get site by fwild"""
        params = {'action': 'get_site_by_fwild', 'fwild': str(fwild)}
        result = self._make_request(params=params)
        return result.get('site') if result.get('status') == 'success' else None
    
    def sync_sites(self) -> List[dict]:
        """Sync all sites from backend"""
        params = {'action': 'sync_sites'}
        result = self._make_request(params=params)
        return result.get('sites', []) if result.get('status') == 'success' else []
    
    def get_new_sites(self, since: float = None) -> List[dict]:
        """
        Get new/updated sites since timestamp
        This is the 30-second polling endpoint
        """
        if since is None:
            since = self.last_check_time
        
        params = {
            'action': 'get_new_sites',
            'since': str(int(since))
        }
        result = self._make_request(params=params)
        
        if result.get('status') == 'success':
            self.last_check_time = result.get('current_time', time.time())
            return result.get('sites', [])
        return []
    
    def get_stats(self) -> dict:
        """Get backend statistics"""
        params = {'action': 'get_stats'}
        result = self._make_request(params=params)
        return result if result.get('status') == 'success' else {}
    
    def store_key(self, peer_id: str, key_type: str, key_data: str, 
                 expires_in: int = 3600) -> bool:
        """Store encryption key for peer exchange"""
        data = {
            'action': 'store_key',
            'key_type': key_type,
            'key_data': key_data,
            'expires_in': str(expires_in)
        }
        result = self._make_request(data=data, peer_id=peer_id)
        return result.get('status') == 'success'
    
    def get_key(self, target_peer: str, key_type: str = 'public') -> Optional[str]:
        """Get peer's encryption key"""
        params = {
            'action': 'get_key',
            'peer_id': target_peer,
            'key_type': key_type
        }
        result = self._make_request(params=params)
        return result.get('key_data') if result.get('status') == 'success' else None
    
    # ==================== Polling Methods ====================
    
    def on_new_site(self, callback: Callable):
        """Register callback for new site detection (30-second polling)"""
        self._new_site_callbacks.append(callback)
    
    def _poll_loop(self):
        """Internal polling loop - queries every 30 seconds"""
        while self._polling_active:
            try:
                new_sites = self.get_new_sites()
                
                if new_sites:
                    logger.info(f"[30s Poll] Detected {len(new_sites)} new/updated sites")
                    
                    for callback in self._new_site_callbacks:
                        try:
                            for site_data in new_sites:
                                callback(site_data)
                        except Exception as e:
                            logger.error(f"Callback error: {e}")
                
                # Wait 30 seconds before next poll
                for _ in range(self.polling_interval):
                    if not self._polling_active:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Polling error: {e}")
                time.sleep(5)
    
    def start_polling(self, interval: int = 30):
        """Start 30-second polling for new sites"""
        if self._polling_active:
            return
        
        self.polling_interval = interval
        self._polling_active = True
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()
        logger.info(f"Started 30-second polling for new sites")
    
    def stop_polling(self):
        """Stop polling"""
        self._polling_active = False
        if self._poll_thread:
            self._poll_thread.join(timeout=5)
        logger.info("Stopped polling")
    
    def close(self):
        """Close client"""
        self.stop_polling()
        self.session.close()


class QWDEPeer:
    """
    QWDE Protocol Peer with PHP Backend Integration
    Uses custom QWDE encryption for peer-to-peer communications
    PHP backend handles central MySQL storage
    """
    
    DEFAULT_PORT = 8766
    
    def __init__(self, peer_id: str = None, host: str = '0.0.0.0', 
                 port: int = DEFAULT_PORT,
                 backend_url: str = 'http://localhost/qwde_ddns_api.php'):
        self.peer_id = peer_id or self._generate_peer_id()
        self.host = host
        self.port = port
        
        # PHP Backend client for central storage
        self.backend = HTTPBackendClient(backend_url)
        
        # Pin wheel connections for P2P
        self.pin_wheel = PinWheelConnection()
        
        # Local site cache (stores encrypted data)
        self.sites: Dict[str, dict] = {}
        self.fwild_index: Dict[int, str] = {}
        
        self.running = False
        self.server_socket = None
        
        self._site_callbacks: List[Callable] = []
    
    def _generate_peer_id(self) -> str:
        """Generate unique peer ID"""
        return f"qwde-peer-{uuid.uuid4().hex[:12]}"
    
    def register_site(self, domain: str, site_data: bytes, 
                     encrypt: bool = True) -> Optional[dict]:
        """
        Register a new site
        Site data is encrypted before storage in PHP backend
        """
        # Apply QWDE encryption if requested
        if encrypt:
            from improved_qwde import encrypt_qwde
            import os
            
            S = os.urandom(16)
            E = hashlib.sha256(site_data).digest()
            U = os.urandom(16)
            
            result = encrypt_qwde(
                S=S, E=E, U=U, plaintext=site_data,
                omega=1.0, tau_max=1.0, eta=0.1, n=100, kappa=0.01
            )
            
            # Store encrypted quadrants
            encrypted_data = b''.join(result['ciphertexts'])
            metadata = {
                'seeds': [s.hex() for s in result['seeds']],
                'temporal_params': result['temporal_parameters'],
                'ec_hash': result['error_correction_hash'].hex()
            }
        else:
            encrypted_data = site_data
            metadata = {}
        
        # Register with PHP backend
        backend_result = self.backend.register_site(
            domain=domain,
            creator_peer_id=self.peer_id,
            encrypted_site_data=encrypted_data,
            metadata=metadata
        )
        
        if backend_result:
            # Update local cache
            self.sites[domain] = {
                'fwild': backend_result['fwild'],
                'site_data': encrypted_data,
                'metadata': metadata,
                'version': backend_result['version']
            }
            self.fwild_index[backend_result['fwild']] = domain
            
            # Notify callbacks
            for callback in self._site_callbacks:
                try:
                    callback(SiteUpdate(
                        domain=domain,
                        fwild=backend_result['fwild'],
                        site_data=encrypted_data,
                        timestamp=time.time(),
                        source_peer=self.peer_id
                    ))
                except Exception as e:
                    logger.error(f"Callback error: {e}")
            
            logger.info(f"Registered site: {domain} (fwild={backend_result['fwild']})")
            return backend_result
        
        return None
    
    def get_site(self, domain: str) -> Optional[dict]:
        """Get site from local cache or backend"""
        if domain in self.sites:
            return self.sites[domain]
        
        site = self.backend.get_site(domain)
        if site:
            self.sites[domain] = site
            self.fwild_index[site['fwild']] = domain
        return site
    
    def get_site_by_fwild(self, fwild: int) -> Optional[dict]:
        """Get site by fwild"""
        domain = self.fwild_index.get(fwild)
        if domain:
            return self.sites.get(domain)
        
        site = self.backend.get_site_by_fwild(fwild)
        if site:
            self.sites[site['domain']] = site
            self.fwild_index[site['fwild']] = site['domain']
        return site
    
    def sync_from_backend(self, auto_decrypt: bool = False) -> int:
        """
        Sync all sites from PHP backend
        This is the auto-download on startup
        """
        sites = self.backend.sync_sites()
        count = 0
        
        for site_data in sites:
            domain = site_data['domain']
            if domain not in self.sites:
                self.sites[domain] = site_data
                self.fwild_index[site_data['fwild']] = domain
                count += 1
        
        logger.info(f"Synced {count} sites from PHP backend")
        return count
    
    def discover_peers(self, limit: int = 8):
        """Discover peers from backend and add to pin wheel"""
        peers = self.backend.get_peers(limit)
        
        for peer_data in peers:
            if peer_data.get('peer_id') != self.peer_id:
                self.pin_wheel.add_connection(
                    peer_data.get('peer_id'),
                    peer_data.get('host'),
                    peer_data.get('port'),
                    peer_data.get('public_key')
                )
        
        logger.info(f"Discovered {len(peers)} peers from backend")
    
    def on_site_update(self, callback: Callable):
        """Register callback for site updates"""
        self._site_callbacks.append(callback)
    
    def start(self, auto_sync: bool = True):
        """
        Start peer server with auto-download
        
        Args:
            auto_sync: If True, auto-download all sites on startup
        """
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(10)
        self.server_socket.settimeout(1.0)
        
        self.running = True
        
        # Register with PHP backend
        self.backend.register_peer(
            peer_id=self.peer_id,
            host=self.host,
            port=self.port,
            sites=list(self.sites.keys())
        )
        
        # AUTO-DOWNLOAD: Sync all sites from backend on startup
        if auto_sync:
            logger.info("Auto-sync: Downloading all sites from PHP backend...")
            try:
                count = self.sync_from_backend()
                logger.info(f"Auto-sync complete: {count} sites downloaded")
                
                # Start 30-second polling for new sites
                def on_new_site(site_data):
                    domain = site_data['domain']
                    if domain not in self.sites:
                        self.sites[domain] = site_data
                        self.fwild_index[site_data['fwild']] = domain
                        logger.info(f"[30s Poll] New site: {domain} (fwild={site_data['fwild']})")
                
                self.backend.on_new_site(on_new_site)
                self.backend.start_polling(interval=30)
                
            except Exception as e:
                logger.error(f"Auto-sync error: {e}")
        
        # Start heartbeat thread
        heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        
        # Start peer discovery
        discovery_thread = threading.Thread(target=self._discovery_loop, daemon=True)
        discovery_thread.start()
        
        logger.info(f"QWDE Peer started: {self.peer_id} on {self.host}:{self.port}")
        
        # Accept P2P connections
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                handler_thread = threading.Thread(
                    target=self._client_handler,
                    args=(client_socket, address),
                    daemon=True
                )
                handler_thread.start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"Server error: {e}")
    
    def _heartbeat_loop(self):
        """Send heartbeats to backend every 60 seconds"""
        while self.running:
            try:
                self.backend.heartbeat(self.peer_id)
                self.backend.register_peer(
                    peer_id=self.peer_id,
                    host=self.host,
                    port=self.port,
                    sites=list(self.sites.keys())
                )
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
            time.sleep(60)
    
    def _discovery_loop(self):
        """Periodic peer discovery"""
        while self.running:
            try:
                self.discover_peers()
            except Exception as e:
                logger.error(f"Discovery error: {e}")
            time.sleep(120)
    
    def _client_handler(self, client_socket: socket.socket, address: tuple):
        """Handle P2P client connection"""
        try:
            client_socket.settimeout(30.0)
            while self.running:
                try:
                    data = client_socket.recv(65535)
                    if not data:
                        break
                    # Handle P2P encrypted data here
                except socket.timeout:
                    continue
        except Exception as e:
            logger.error(f"Client handler error: {e}")
        finally:
            client_socket.close()
    
    def stop(self):
        """Stop peer server"""
        self.running = False
        self.backend.close()
        
        if self.server_socket:
            self.server_socket.close()
        
        logger.info(f"QWDE Peer stopped: {self.peer_id}")


def create_peer(backend_url: str = 'http://localhost/qwde_ddns_api.php',
                port: int = QWDEPeer.DEFAULT_PORT) -> QWDEPeer:
    """Factory function to create a QWDE peer"""
    return QWDEPeer(
        host='0.0.0.0',
        port=port,
        backend_url=backend_url
    )


if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════╗
║      QWDE Protocol - Peer with PHP Backend                ║
╠═══════════════════════════════════════════════════════════╣
║  Features:                                                ║
║    • PHP backend for MySQL storage                       ║
║    • 30-second polling for new sites                     ║
║    • Auto-download on startup                            ║
║    • Custom QWDE encryption                              ║
║    • Pin Wheel P2P connections                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Test with local PHP backend
    peer = create_peer('http://localhost/qwde_ddns_api.php')
    
    try:
        peer.start(auto_sync=True)
    except KeyboardInterrupt:
        print("\nShutting down...")
        peer.stop()
