"""
QWDE Protocol - Central DDNS Server
Supports both MySQL and SQLite backends
"""

import socket
import threading
import json
import time
import hashlib
import random
from datetime import datetime
from typing import Dict, List, Optional, Set
import logging
import configparser
import os

# MySQL support (optional)
try:
    import mysql.connector
    from mysql.connector import Error
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    logging.warning("mysql-connector-python not installed. MySQL support disabled.")

# SQLite (always available)
import sqlite3

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PeerInfo:
    """Represents a peer in the QWDE network"""
    def __init__(self, peer_id: str, host: str, port: int, sites: List[str] = None):
        self.peer_id = peer_id
        self.host = host
        self.port = port
        self.sites = sites or []
        self.last_seen = time.time()
        self.is_alive = True
    
    def to_dict(self) -> dict:
        return {
            'peer_id': self.peer_id,
            'host': self.host,
            'port': self.port,
            'sites': self.sites,
            'last_seen': self.last_seen,
            'is_alive': self.is_alive
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PeerInfo':
        peer = cls(data['peer_id'], data['host'], data['port'], data.get('sites', []))
        peer.last_seen = data.get('last_seen', time.time())
        peer.is_alive = data.get('is_alive', True)
        return peer


class SiteInfo:
    """Represents a QWDE site"""
    def __init__(self, domain: str, fwild: int, creator_peer_id: str, 
                 site_data: bytes, created_at: float = None):
        self.domain = domain
        self.fwild = fwild
        self.creator_peer_id = creator_peer_id
        self.site_data = site_data
        self.created_at = created_at or time.time()
        self.updated_at = time.time()
        self.version = 1
    
    def to_dict(self) -> dict:
        return {
            'domain': self.domain,
            'fwild': self.fwild,
            'creator_peer_id': self.creator_peer_id,
            'site_data': self.site_data.hex(),
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'version': self.version
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SiteInfo':
        site = cls(
            data['domain'],
            data['fwild'],
            data['creator_peer_id'],
            bytes.fromhex(data['site_data']),
            data.get('created_at')
        )
        site.updated_at = data.get('updated_at', time.time())
        site.version = data.get('version', 1)
        return site


class MySQLDDNSDatabase:
    """MySQL database backend for DDNS"""
    
    def __init__(self, host: str = 'localhost', port: int = 3306,
                 user: str = 'qwde_user', password: str = 'qwde_pass',
                 database: str = 'qwde_ddns'):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self._connect()
    
    def _connect(self):
        """Establish MySQL connection"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self.connection.is_connected():
                logger.info(f"Connected to MySQL at {self.host}:{self.port}")
                self._create_tables()
        except Error as e:
            logger.error(f"MySQL connection error: {e}")
            raise
    
    def _create_tables(self):
        """Create database tables"""
        cursor = self.connection.cursor()
        
        # Peers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS peers (
                peer_id VARCHAR(100) PRIMARY KEY,
                host VARCHAR(50) NOT NULL,
                port INT NOT NULL,
                sites JSON,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                is_alive BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        
        # Sites table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sites (
                domain VARCHAR(255) PRIMARY KEY,
                fwild INT UNIQUE NOT NULL,
                creator_peer_id VARCHAR(100) NOT NULL,
                site_data LONGBLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                version INT DEFAULT 1,
                INDEX idx_fwild (fwild),
                INDEX idx_created (created_at DESC)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        
        # Fwild counter table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fwild_counter (
                id INT PRIMARY KEY AUTO_INCREMENT,
                current_value INT NOT NULL DEFAULT 0
            )
        ''')
        
        # Initialize counter if empty
        cursor.execute('SELECT COUNT(*) FROM fwild_counter')
        if cursor.fetchone()[0] == 0:
            cursor.execute('INSERT INTO fwild_counter (current_value) VALUES (0)')
        
        self.connection.commit()
        cursor.close()
        logger.info("Database tables created/verified")
    
    def get_fwild_counter(self) -> int:
        """Get current fwild counter"""
        cursor = self.connection.cursor()
        cursor.execute('SELECT current_value FROM fwild_counter WHERE id = 1')
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else 0
    
    def increment_fwild(self) -> int:
        """Increment and return new fwild value"""
        cursor = self.connection.cursor()
        cursor.execute('UPDATE fwild_counter SET current_value = current_value + 1 WHERE id = 1')
        cursor.execute('SELECT current_value FROM fwild_counter WHERE id = 1')
        result = cursor.fetchone()
        self.connection.commit()
        cursor.close()
        return result[0]
    
    def save_peer(self, peer: PeerInfo):
        """Save or update peer"""
        cursor = self.connection.cursor()
        sites_json = json.dumps(peer.sites)
        cursor.execute('''
            INSERT INTO peers (peer_id, host, port, sites, is_alive)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                host = VALUES(host),
                port = VALUES(port),
                sites = VALUES(sites),
                is_alive = VALUES(is_alive),
                last_seen = CURRENT_TIMESTAMP
        ''', (peer.peer_id, peer.host, peer.port, sites_json, peer.is_alive))
        self.connection.commit()
        cursor.close()
    
    def delete_peer(self, peer_id: str):
        """Delete peer"""
        cursor = self.connection.cursor()
        cursor.execute('DELETE FROM peers WHERE peer_id = %s', (peer_id,))
        self.connection.commit()
        cursor.close()
    
    def get_peer(self, peer_id: str) -> Optional[PeerInfo]:
        """Get peer by ID"""
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute('SELECT * FROM peers WHERE peer_id = %s', (peer_id,))
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            return PeerInfo(
                row['peer_id'],
                row['host'],
                row['port'],
                json.loads(row['sites']) if row['sites'] else []
            )
        return None
    
    def get_live_peers(self, limit: int = 10, max_age_seconds: int = 300) -> List[PeerInfo]:
        """Get live peers"""
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute('''
            SELECT * FROM peers 
            WHERE is_alive = TRUE 
            AND last_seen > DATE_SUB(NOW(), INTERVAL %s SECOND)
            ORDER BY last_seen DESC
            LIMIT %s
        ''', (max_age_seconds, limit))
        rows = cursor.fetchall()
        cursor.close()
        
        peers = []
        for row in rows:
            peer = PeerInfo(
                row['peer_id'],
                row['host'],
                row['port'],
                json.loads(row['sites']) if row['sites'] else []
            )
            peer.last_seen = row['last_seen'].timestamp() if row['last_seen'] else time.time()
            peers.append(peer)
        return peers
    
    def save_site(self, site: SiteInfo):
        """Save or update site"""
        cursor = self.connection.cursor()
        cursor.execute('''
            INSERT INTO sites (domain, fwild, creator_peer_id, site_data, version)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                site_data = VALUES(site_data),
                version = VALUES(version),
                updated_at = CURRENT_TIMESTAMP
        ''', (site.domain, site.fwild, site.creator_peer_id, site.site_data, site.version))
        self.connection.commit()
        cursor.close()
    
    def get_site(self, domain: str) -> Optional[SiteInfo]:
        """Get site by domain"""
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute('SELECT * FROM sites WHERE domain = %s', (domain,))
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            site = SiteInfo(
                row['domain'],
                row['fwild'],
                row['creator_peer_id'],
                row['site_data'],
                row['created_at'].timestamp() if row['created_at'] else time.time()
            )
            site.updated_at = row['updated_at'].timestamp() if row['updated_at'] else time.time()
            site.version = row['version']
            return site
        return None
    
    def get_site_by_fwild(self, fwild: int) -> Optional[SiteInfo]:
        """Get site by fwild"""
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute('SELECT * FROM sites WHERE fwild = %s', (fwild,))
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            site = SiteInfo(
                row['domain'],
                row['fwild'],
                row['creator_peer_id'],
                row['site_data'],
                row['created_at'].timestamp() if row['created_at'] else time.time()
            )
            site.updated_at = row['updated_at'].timestamp() if row['updated_at'] else time.time()
            site.version = row['version']
            return site
        return None
    
    def get_all_sites(self) -> List[SiteInfo]:
        """Get all sites"""
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute('SELECT * FROM sites ORDER BY fwild DESC')
        rows = cursor.fetchall()
        cursor.close()
        
        sites = []
        for row in rows:
            site = SiteInfo(
                row['domain'],
                row['fwild'],
                row['creator_peer_id'],
                row['site_data'],
                row['created_at'].timestamp() if row['created_at'] else time.time()
            )
            site.updated_at = row['updated_at'].timestamp() if row['updated_at'] else time.time()
            site.version = row['version']
            sites.append(site)
        return sites
    
    def get_recent_sites(self, count: int = 10) -> List[SiteInfo]:
        """Get recently added sites"""
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute('''
            SELECT * FROM sites 
            ORDER BY created_at DESC 
            LIMIT %s
        ''', (count,))
        rows = cursor.fetchall()
        cursor.close()
        
        sites = []
        for row in rows:
            site = SiteInfo(
                row['domain'],
                row['fwild'],
                row['creator_peer_id'],
                row['site_data'],
                row['created_at'].timestamp() if row['created_at'] else time.time()
            )
            site.updated_at = row['updated_at'].timestamp() if row['updated_at'] else time.time()
            site.version = row['version']
            sites.append(site)
        return sites
    
    def get_stats(self) -> dict:
        """Get database statistics"""
        cursor = self.connection.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM peers WHERE is_alive = TRUE')
        total_peers = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM peers 
            WHERE is_alive = TRUE 
            AND last_seen > DATE_SUB(NOW(), INTERVAL 300 SECOND)
        ''')
        live_peers = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM sites')
        total_sites = cursor.fetchone()[0]
        
        cursor.execute('SELECT current_value FROM fwild_counter WHERE id = 1')
        result = cursor.fetchone()
        fwild_counter = result[0] if result else 0
        
        cursor.close()
        
        return {
            'total_peers': total_peers,
            'live_peers': live_peers,
            'total_sites': total_sites,
            'fwild_counter': fwild_counter
        }
    
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("MySQL connection closed")


class SQLiteDDNSDatabase:
    """SQLite database backend for DDNS (fallback)"""
    
    def __init__(self, db_path: str = 'qwde_ddns.db'):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database"""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS peers (
                peer_id TEXT PRIMARY KEY,
                host TEXT,
                port INTEGER,
                sites TEXT,
                last_seen REAL,
                is_alive INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sites (
                domain TEXT PRIMARY KEY,
                fwild INTEGER UNIQUE NOT NULL,
                creator_peer_id TEXT,
                site_data BLOB,
                created_at REAL,
                updated_at REAL,
                version INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fwild_counter (
                id INTEGER PRIMARY KEY,
                current_value INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('SELECT COUNT(*) FROM fwild_counter WHERE id = 1')
        if cursor.fetchone()[0] == 0:
            cursor.execute('INSERT INTO fwild_counter (id, current_value) VALUES (1, 0)')
        
        conn.commit()
        conn.close()
    
    def _get_connection(self):
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_fwild_counter(self) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT current_value FROM fwild_counter WHERE id = 1')
        result = cursor.fetchone()
        conn.close()
        return result['current_value'] if result else 0
    
    def increment_fwild(self) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE fwild_counter SET current_value = current_value + 1 WHERE id = 1')
        cursor.execute('SELECT current_value FROM fwild_counter WHERE id = 1')
        result = cursor.fetchone()
        conn.commit()
        conn.close()
        return result['current_value']
    
    def save_peer(self, peer: PeerInfo):
        conn = self._get_connection()
        cursor = conn.cursor()
        sites_json = json.dumps(peer.sites)
        cursor.execute('''
            INSERT OR REPLACE INTO peers (peer_id, host, port, sites, last_seen, is_alive)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (peer.peer_id, peer.host, peer.port, sites_json, 
              peer.last_seen, 1 if peer.is_alive else 0))
        conn.commit()
        conn.close()
    
    def delete_peer(self, peer_id: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM peers WHERE peer_id = ?', (peer_id,))
        conn.commit()
        conn.close()
    
    def get_peer(self, peer_id: str) -> Optional[PeerInfo]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM peers WHERE peer_id = ?', (peer_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return PeerInfo(
                row['peer_id'],
                row['host'],
                row['port'],
                json.loads(row['sites']) if row['sites'] else []
            )
        return None
    
    def get_live_peers(self, limit: int = 10, max_age_seconds: int = 300) -> List[PeerInfo]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cutoff = time.time() - max_age_seconds
        cursor.execute('''
            SELECT * FROM peers 
            WHERE is_alive = 1 AND last_seen > ?
            ORDER BY last_seen DESC
            LIMIT ?
        ''', (cutoff, limit))
        rows = cursor.fetchall()
        conn.close()
        
        peers = []
        for row in rows:
            peer = PeerInfo(
                row['peer_id'],
                row['host'],
                row['port'],
                json.loads(row['sites']) if row['sites'] else []
            )
            peer.last_seen = row['last_seen']
            peers.append(peer)
        return peers
    
    def save_site(self, site: SiteInfo):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO sites 
            (domain, fwild, creator_peer_id, site_data, created_at, updated_at, version)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (site.domain, site.fwild, site.creator_peer_id, site.site_data,
              site.created_at, site.updated_at, site.version))
        conn.commit()
        conn.close()
    
    def get_site(self, domain: str) -> Optional[SiteInfo]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sites WHERE domain = ?', (domain,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            site = SiteInfo(
                row['domain'],
                row['fwild'],
                row['creator_peer_id'],
                row['site_data'],
                row['created_at']
            )
            site.updated_at = row['updated_at']
            site.version = row['version']
            return site
        return None
    
    def get_site_by_fwild(self, fwild: int) -> Optional[SiteInfo]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sites WHERE fwild = ?', (fwild,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            site = SiteInfo(
                row['domain'],
                row['fwild'],
                row['creator_peer_id'],
                row['site_data'],
                row['created_at']
            )
            site.updated_at = row['updated_at']
            site.version = row['version']
            return site
        return None
    
    def get_all_sites(self) -> List[SiteInfo]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sites ORDER BY fwild DESC')
        rows = cursor.fetchall()
        conn.close()
        
        sites = []
        for row in rows:
            site = SiteInfo(
                row['domain'],
                row['fwild'],
                row['creator_peer_id'],
                row['site_data'],
                row['created_at']
            )
            site.updated_at = row['updated_at']
            site.version = row['version']
            sites.append(site)
        return sites
    
    def get_recent_sites(self, count: int = 10) -> List[SiteInfo]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sites ORDER BY created_at DESC LIMIT ?', (count,))
        rows = cursor.fetchall()
        conn.close()
        
        sites = []
        for row in rows:
            site = SiteInfo(
                row['domain'],
                row['fwild'],
                row['creator_peer_id'],
                row['site_data'],
                row['created_at']
            )
            site.updated_at = row['updated_at']
            site.version = row['version']
            sites.append(site)
        return sites
    
    def get_stats(self) -> dict:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM peers WHERE is_alive = 1')
        total_peers = cursor.fetchone()[0]
        
        cutoff = time.time() - 300
        cursor.execute('SELECT COUNT(*) FROM peers WHERE is_alive = 1 AND last_seen > ?', (cutoff,))
        live_peers = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM sites')
        total_sites = cursor.fetchone()[0]
        
        cursor.execute('SELECT current_value FROM fwild_counter WHERE id = 1')
        result = cursor.fetchone()
        fwild_counter = result['current_value'] if result else 0
        
        conn.close()
        
        return {
            'total_peers': total_peers,
            'live_peers': live_peers,
            'total_sites': total_sites,
            'fwild_counter': fwild_counter
        }
    
    def close(self):
        pass


class MySQLDDNSServer:
    """Central DDNS server with MySQL backend"""
    
    DEFAULT_PORT = 8765
    CENTRAL_SERVER_HOST = "ddns.secupgrade.com"
    
    def __init__(self, host: str = '0.0.0.0', port: int = DEFAULT_PORT,
                 mysql_config: dict = None, use_sqlite: bool = False):
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None
        
        # Initialize database
        if use_sqlite or not MYSQL_AVAILABLE:
            logger.info("Using SQLite database backend")
            self.db = SQLiteDDNSDatabase()
        else:
            if mysql_config is None:
                mysql_config = {
                    'host': 'localhost',
                    'port': 3306,
                    'user': 'qwde_user',
                    'password': 'qwde_pass',
                    'database': 'qwde_ddns'
                }
            logger.info(f"Using MySQL database backend at {mysql_config['host']}")
            self.db = MySQLDDNSDatabase(**mysql_config)
        
        # In-memory cache for performance
        self.peers: Dict[str, PeerInfo] = {}
        self.sites: Dict[str, SiteInfo] = {}
        self._load_cache()
    
    def _load_cache(self):
        """Load data from database to cache"""
        try:
            for peer in self.db.get_live_peers(limit=1000):
                self.peers[peer.peer_id] = peer
            
            for site in self.db.get_all_sites():
                self.sites[site.domain] = site
                if hasattr(self.db, 'get_fwild_counter'):
                    pass  # Counter managed by DB
            
            logger.info(f"Loaded {len(self.peers)} peers and {len(self.sites)} sites to cache")
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
    
    def _save_to_db(self, peer: PeerInfo = None, site: SiteInfo = None):
        """Save to database"""
        try:
            if peer:
                self.db.save_peer(peer)
            if site:
                self.db.save_site(site)
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
    
    def generate_fwild(self) -> int:
        """Generate a new fwild number"""
        return self.db.increment_fwild()
    
    def register_peer(self, peer_id: str, host: str, port: int, 
                     sites: List[str] = None) -> bool:
        """Register a new peer"""
        peer = PeerInfo(peer_id, host, port, sites)
        self.peers[peer_id] = peer
        self._save_to_db(peer=peer)
        logger.info(f"Registered peer: {peer_id} at {host}:{port}")
        return True
    
    def unregister_peer(self, peer_id: str) -> bool:
        """Unregister a peer"""
        if peer_id in self.peers:
            del self.peers[peer_id]
            self.db.delete_peer(peer_id)
            logger.info(f"Unregistered peer: {peer_id}")
            return True
        return False
    
    def heartbeat(self, peer_id: str) -> bool:
        """Update peer heartbeat"""
        if peer_id in self.peers:
            self.peers[peer_id].last_seen = time.time()
            self.peers[peer_id].is_alive = True
            self._save_to_db(peer=self.peers[peer_id])
            return True
        return False
    
    def get_live_peers(self, limit: int = 10) -> List[PeerInfo]:
        """Get random selection of live peers"""
        live_peers = [p for p in self.peers.values() 
                     if p.is_alive and (time.time() - p.last_seen) < 300]
        
        if len(live_peers) > limit:
            return random.sample(live_peers, limit)
        return live_peers
    
    def register_site(self, domain: str, creator_peer_id: str, 
                     site_data: bytes) -> Optional[SiteInfo]:
        """Register a new site"""
        if domain in self.sites:
            site = self.sites[domain]
            site.site_data = site_data
            site.updated_at = time.time()
            site.version += 1
            logger.info(f"Updated site: {domain} (v{site.version})")
        else:
            fwild = self.generate_fwild()
            site = SiteInfo(domain, fwild, creator_peer_id, site_data)
            self.sites[domain] = site
            logger.info(f"Registered new site: {domain} (fwild={fwild})")
        
        self._save_to_db(site=site)
        return site
    
    def get_site(self, domain: str) -> Optional[SiteInfo]:
        """Get site by domain"""
        return self.sites.get(domain)
    
    def get_site_by_fwild(self, fwild: int) -> Optional[SiteInfo]:
        """Get site by fwild number"""
        for site in self.sites.values():
            if site.fwild == fwild:
                return site
        return None
    
    def get_recent_sites(self, count: int = 10) -> List[SiteInfo]:
        """Get recently added sites"""
        sorted_sites = sorted(self.sites.values(), 
                            key=lambda s: s.fwild, reverse=True)
        return sorted_sites[:count]
    
    def get_all_sites_list(self) -> List[dict]:
        """Get list of all sites"""
        return [s.to_dict() for s in self.sites.values()]
    
    def handle_request(self, data: bytes, client_address: tuple) -> bytes:
        """Handle incoming DDNS request"""
        try:
            request = json.loads(data.decode('utf-8'))
            action = request.get('action')
            
            response = {'status': 'error', 'message': 'Unknown action'}
            
            if action == 'register_peer':
                success = self.register_peer(
                    request['peer_id'],
                    request['host'],
                    request['port'],
                    request.get('sites', [])
                )
                response = {'status': 'success' if success else 'error'}
            
            elif action == 'unregister_peer':
                success = self.unregister_peer(request['peer_id'])
                response = {'status': 'success' if success else 'error'}
            
            elif action == 'heartbeat':
                success = self.heartbeat(request['peer_id'])
                response = {'status': 'success' if success else 'error'}
            
            elif action == 'get_peers':
                peers = self.get_live_peers(request.get('limit', 10))
                response = {
                    'status': 'success',
                    'peers': [p.to_dict() for p in peers]
                }
            
            elif action == 'register_site':
                site = self.register_site(
                    request['domain'],
                    request['creator_peer_id'],
                    bytes.fromhex(request['site_data'])
                )
                response = {
                    'status': 'success',
                    'fwild': site.fwild if site else None,
                    'version': site.version if site else None
                }
            
            elif action == 'get_site':
                site = self.get_site(request['domain'])
                if site:
                    response = {
                        'status': 'success',
                        'site': site.to_dict()
                    }
                else:
                    response = {'status': 'not_found'}
            
            elif action == 'get_site_by_fwild':
                site = self.get_site_by_fwild(request['fwild'])
                if site:
                    response = {
                        'status': 'success',
                        'site': site.to_dict()
                    }
                else:
                    response = {'status': 'not_found'}
            
            elif action == 'get_recent_sites':
                sites = self.get_recent_sites(request.get('count', 10))
                response = {
                    'status': 'success',
                    'sites': [s.to_dict() for s in sites]
                }
            
            elif action == 'sync_sites':
                sites = self.get_all_sites_list()
                response = {
                    'status': 'success',
                    'sites': sites,
                    'count': len(sites)
                }
            
            elif action == 'get_stats':
                stats = self.db.get_stats()
                response = {
                    'status': 'success',
                    **stats
                }
            
            return json.dumps(response).encode('utf-8')
            
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return json.dumps({
                'status': 'error',
                'message': str(e)
            }).encode('utf-8')
    
    def start(self):
        """Start the DDNS server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.settimeout(1.0)
        
        self.running = True
        logger.info(f"MySQL DDNS Server started on {self.host}:{self.port}")
        
        # Start cleanup thread
        cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        cleanup_thread.start()
        
        while self.running:
            try:
                data, client_address = self.server_socket.recvfrom(65535)
                response = self.handle_request(data, client_address)
                self.server_socket.sendto(response, client_address)
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"Server error: {e}")
    
    def _cleanup_loop(self):
        """Periodically cleanup stale peers"""
        while self.running:
            time.sleep(60)
            current_time = time.time()
            stale_peers = [pid for pid, p in self.peers.items()
                          if (current_time - p.last_seen) > 600]
            
            for peer_id in stale_peers:
                self.peers[peer_id].is_alive = False
                self._save_to_db(peer=self.peers[peer_id])
                logger.info(f"Marked peer {peer_id} as stale")
    
    def stop(self):
        """Stop the DDNS server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        self.db.close()
        logger.info("DDNS Server stopped")


def load_config(config_path: str = 'qwde_config.ini') -> dict:
    """Load configuration from INI file"""
    config = configparser.ConfigParser()
    config.read(config_path)
    
    mysql_config = {
        'host': config.get('mysql', 'host', fallback='localhost'),
        'port': config.getint('mysql', 'port', fallback=3306),
        'user': config.get('mysql', 'user', fallback='qwde_user'),
        'password': config.get('mysql', 'password', fallback='qwde_pass'),
        'database': config.get('mysql', 'database', fallback='qwde_ddns')
    }
    
    server_config = {
        'host': config.get('server', 'host', fallback='0.0.0.0'),
        'port': config.getint('server', 'port', fallback=8765),
        'use_sqlite': config.getboolean('server', 'use_sqlite', fallback=False)
    }
    
    return {
        'mysql': mysql_config,
        'server': server_config
    }


def create_config_file(config_path: str = 'qwde_config.ini'):
    """Create default configuration file"""
    config = configparser.ConfigParser()
    
    config['mysql'] = {
        'host': 'secupgrade.com',
        'port': '3306',
        'user': 'qwde_user',
        'password': 'qwde_secure_password_here',
        'database': 'qwde_ddns'
    }
    
    config['server'] = {
        'host': '0.0.0.0',
        'port': '8765',
        'use_sqlite': 'False'
    }
    
    config['central_server'] = {
        'host': 'ddns.secupgrade.com',
        'port': '8765'
    }
    
    with open(config_path, 'w') as f:
        config.write(f)
    
    logger.info(f"Configuration file created: {config_path}")


def run_mysql_server():
    """Run the DDNS server (MySQL or SQLite based on config)"""
    config = load_config()
    
    # Determine database type from config
    db_type = config.get('database', {}).get('type', 'mysql')
    use_sqlite = (db_type == 'sqlite')
    
    if use_sqlite:
        sqlite_path = config.get('database', {}).get('sqlite_path', 'qwde_ddns.db')
        db_info = f"SQLite: {sqlite_path}"
    else:
        db_info = f"MySQL: {config['mysql']['user']}@{config['mysql']['host']}:{config['mysql']['port']}/{config['mysql']['database']}"

    server = MySQLDDNSServer(
        host=config['server']['host'],
        port=config['server']['port'],
        mysql_config=config['mysql'],
        use_sqlite=use_sqlite,
        sqlite_path=sqlite_path if use_sqlite else 'qwede_ddns.db'
    )

    print(f"""
╔═══════════════════════════════════════════════════════════╗
║        QWDE Protocol - DDNS Server                        ║
╠═══════════════════════════════════════════════════════════╣
║  Listening on port: {config['server']['port']}                            ║
║  Database: {db_info:<50} ║
║  Central Server: ddns.secupgrade.com                     ║
║                                                           ║
║  Features:                                                ║
║    • {'SQLite' if use_sqlite else 'MySQL'} persistent storage                               ║
║    • Peer discovery & registration                         ║
║    • Site registration with fwild indexing                ║
║    • Live peer selection (pin wheel)                      ║
║    • Automatic site synchronization                       ║
╚═══════════════════════════════════════════════════════════╝
    """)

    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down DDNS server...")
        server.stop()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--create-config':
            create_config_file()
        elif sys.argv[1] == '--server':
            run_mysql_server()
        else:
            print("Usage: python qwde_mysql_ddns.py [--create-config|--server]")
    else:
        run_mysql_server()
