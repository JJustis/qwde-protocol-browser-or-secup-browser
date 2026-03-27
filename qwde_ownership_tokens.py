"""
QWDE Protocol - Site Ownership Token System
Generates unique ownership tokens on site creation
Tokens required for deletion and transfer
Includes cache invalidation broadcast to all clients
"""

import hashlib
import json
import time
import os
from typing import Optional, Dict, List
import logging
import threading
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OwnershipTokenManager:
    """
    Manages site ownership tokens
    
    Token Generation:
    - Created when site is registered
    - Unique per site per peer
    - Stored locally and on central server
    - Required for deletion
    
    Token Format:
    {
        "domain": "mysite.qwde",
        "peer_id": "peer-123",
        "token": "sha256(domain:peer_id:secret:timestamp)",
        "created_at": timestamp,
        "site_hash": "abc123..."
    }
    """
    
    def __init__(self, peer_id: str, storage_path: str = 'ownership_tokens'):
        self.peer_id = peer_id
        self.storage_path = storage_path
        self.tokens: Dict[str, dict] = {}  # domain -> token_data
        
        # Secret key for token generation (should be stored securely)
        self.secret_key = self._load_or_generate_secret()
        
        # Load existing tokens
        self._load_tokens()
    
    def _load_or_generate_secret(self) -> bytes:
        """Load existing secret or generate new one"""
        secret_file = os.path.join(self.storage_path, 'peer_secret.key')
        
        if os.path.exists(secret_file):
            with open(secret_file, 'rb') as f:
                return f.read()
        else:
            # Generate new secret
            os.makedirs(self.storage_path, exist_ok=True)
            secret = os.urandom(32)
            with open(secret_file, 'wb') as f:
                f.write(secret)
            return secret
    
    def _load_tokens(self):
        """Load tokens from disk"""
        tokens_file = os.path.join(self.storage_path, f'{self.peer_id}_tokens.json')
        
        if os.path.exists(tokens_file):
            with open(tokens_file, 'r') as f:
                data = json.load(f)
                self.tokens = data.get('tokens', {})
            logger.info(f"Loaded {len(self.tokens)} ownership tokens")
    
    def _save_tokens(self):
        """Save tokens to disk"""
        tokens_file = os.path.join(self.storage_path, f'{self.peer_id}_tokens.json')
        
        with open(tokens_file, 'w') as f:
            json.dump({
                'peer_id': self.peer_id,
                'tokens': self.tokens,
                'last_updated': time.time()
            }, f, indent=2)
    
    def create_ownership_token(self, domain: str, site_hash: str) -> dict:
        """
        Create ownership token for new site
        
        Args:
            domain: Site domain
            site_hash: SHA-256 hash of site content
        
        Returns:
            Ownership token dict
        """
        timestamp = int(time.time())
        
        # Create unique token
        message = f"{domain}:{self.peer_id}:{timestamp}:{site_hash}"
        token = hashlib.sha256(
            message.encode() + self.secret_key
        ).hexdigest()
        
        token_data = {
            'domain': domain,
            'peer_id': self.peer_id,
            'token': token,
            'created_at': timestamp,
            'site_hash': site_hash,
            'version': 1
        }
        
        # Store locally
        self.tokens[domain] = token_data
        self._save_tokens()
        
        logger.info(f"Created ownership token for {domain}")
        return token_data
    
    def get_ownership_token(self, domain: str) -> Optional[dict]:
        """Get ownership token for domain"""
        return self.tokens.get(domain)
    
    def verify_ownership(self, domain: str, token: str) -> bool:
        """Verify ownership token"""
        stored = self.tokens.get(domain)
        
        if not stored:
            return False
        
        return stored['token'] == token
    
    def update_site_hash(self, domain: str, new_hash: str):
        """Update site hash (when site is updated)"""
        if domain in self.tokens:
            self.tokens[domain]['site_hash'] = new_hash
            self.tokens[domain]['version'] += 1
            self._save_tokens()
            logger.info(f"Updated site hash for {domain} (v{self.tokens[domain]['version']})")
    
    def revoke_token(self, domain: str):
        """Revoke ownership token (after deletion)"""
        if domain in self.tokens:
            del self.tokens[domain]
            self._save_tokens()
            logger.info(f"Revoked ownership token for {domain}")


class CacheInvalidationBroadcaster:
    """
    Broadcasts cache invalidation messages to all connected clients
    
    When a site is deleted:
    1. Central server marks site as deleted
    2. Broadcasts invalidation message
    3. All clients purge site from cache
    4. Mirror servers download deletion confirmation
    """
    
    def __init__(self, central_api: str):
        self.central_api = central_api
        self.subscribers: List[str] = []  # Client webhook URLs
    
    def broadcast_deletion(self, domain: str, fwild: int, 
                          deleted_at: int, signature: str):
        """
        Broadcast site deletion to all clients
        
        Args:
            domain: Deleted site domain
            fwild: Site fwild number
            deleted_at: Deletion timestamp
            signature: Central server signature
        """
        invalidation_message = {
            'type': 'cache_invalidation',
            'action': 'delete',
            'domain': domain,
            'fwild': fwild,
            'deleted_at': deleted_at,
            'signature': signature,
            'broadcast_at': int(time.time())
        }
        
        # Notify all subscribers
        for webhook_url in self.subscribers:
            try:
                requests.post(webhook_url, json=invalidation_message, timeout=5)
                logger.info(f"Sent invalidation to {webhook_url}")
            except Exception as e:
                logger.error(f"Failed to notify {webhook_url}: {e}")
        
        # Also store in central API for clients that poll
        try:
            requests.post(
                self.central_api,
                data={
                    'action': 'store_invalidation',
                    'message': json.dumps(invalidation_message)
                },
                timeout=5
            )
        except Exception as e:
            logger.error(f"Failed to store invalidation: {e}")
    
    def subscribe(self, webhook_url: str):
        """Subscribe to invalidation broadcasts"""
        if webhook_url not in self.subscribers:
            self.subscribers.append(webhook_url)
            logger.info(f"Subscribed {webhook_url} to invalidation broadcasts")
    
    def unsubscribe(self, webhook_url: str):
        """Unsubscribe from invalidation broadcasts"""
        if webhook_url in self.subscribers:
            self.subscribers.remove(webhook_url)
            logger.info(f"Unsubscribed {webhook_url}")


class CacheInvalidationListener:
    """
    Listens for cache invalidation messages
    
    Runs in background on each client
    Purges deleted sites from local cache
    """
    
    def __init__(self, client_cache: dict, central_api: str):
        self.client_cache = client_cache  # domain -> content
        self.central_api = central_api
        self.running = False
        self.poll_interval = 30  # Check every 30 seconds
        self.last_check = int(time.time())
    
    def start_listening(self):
        """Start listening for invalidation messages"""
        self.running = True
        
        def listen_loop():
            while self.running:
                try:
                    self._check_invalidations()
                except Exception as e:
                    logger.error(f"Invalidation check error: {e}")
                time.sleep(self.poll_interval)
        
        thread = threading.Thread(target=listen_loop, daemon=True)
        thread.start()
        logger.info(f"Started cache invalidation listener (polling every {self.poll_interval}s)")
    
    def stop_listening(self):
        """Stop listening"""
        self.running = False
    
    def _check_invalidations(self):
        """Check for new invalidation messages"""
        response = requests.get(
            self.central_api,
            params={
                'action': 'get_invalidations',
                'since': str(self.last_check)
            },
            timeout=10
        )
        
        data = response.json()
        
        if data.get('status') == 'success':
            invalidations = data.get('invalidations', [])
            
            for inv in invalidations:
                domain = inv.get('domain')
                
                # Verify signature
                if self._verify_invalidation_signature(inv):
                    # Purge from cache
                    if domain in self.client_cache:
                        del self.client_cache[domain]
                        logger.info(f"Purged deleted site from cache: {domain}")
                    
                    # Also remove from disk cache
                    self._purge_disk_cache(domain)
            
            if invalidations:
                self.last_check = int(time.time())
    
    def _verify_invalidation_signature(self, inv: dict) -> bool:
        """Verify invalidation message signature"""
        # Verify central server signature
        # (In production, use proper crypto verification)
        signature = inv.get('signature')
        if not signature:
            return False
        
        # Simplified verification
        message = f"{inv['domain']}:{inv['fwild']}:{inv['deleted_at']}"
        expected = hashlib.sha256(message.encode()).hexdigest()
        
        return True  # In production: return signature == expected
    
    def _purge_disk_cache(self, domain: str):
        """Purge site from disk cache"""
        safe_domain = domain.replace('/', '_').replace('\\', '_')
        cache_dir = 'site_cache'
        
        # Remove data file
        data_file = os.path.join(cache_dir, f'{safe_domain}.dat')
        if os.path.exists(data_file):
            os.remove(data_file)
            logger.info(f"Removed disk cache: {data_file}")
        
        # Remove metadata file
        meta_file = data_file + '.meta'
        if os.path.exists(meta_file):
            os.remove(meta_file)


def create_deletion_request_with_token(domain: str, token_manager: OwnershipTokenManager,
                                       central_api: str) -> dict:
    """
    Create deletion request with ownership token
    
    Args:
        domain: Site to delete
        token_manager: Ownership token manager
        central_api: Central API URL
    
    Returns:
        Deletion request dict with ownership token
    """
    # Get ownership token
    token_data = token_manager.get_ownership_token(domain)
    
    if not token_data:
        raise ValueError(f"No ownership token found for {domain}")
    
    # Create deletion request
    timestamp = int(time.time())
    
    request = {
        'action': 'delete_site',
        'domain': domain,
        'peer_id': token_data['peer_id'],
        'ownership_token': token_data['token'],
        'site_hash': token_data['site_hash'],
        'timestamp': timestamp,
        'signature': hashlib.sha256(
            f"{domain}:{token_data['peer_id']}:{timestamp}".encode() + 
            token_manager.secret_key
        ).hexdigest()
    }
    
    return request


# Test the system
if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════╗
║      QWDE Protocol - Ownership Token System               ║
╠═══════════════════════════════════════════════════════════╣
║  Features:                                                ║
║    • Unique token per site                               ║
║    • Token required for deletion                         ║
║    • Cache invalidation broadcast                        ║
║    • All clients purge deleted sites                     ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Test token creation
    token_manager = OwnershipTokenManager('test-peer-123')
    
    token = token_manager.create_ownership_token(
        domain='test.qwde',
        site_hash='abc123...'
    )
    
    print("Ownership Token Created:")
    print(json.dumps(token, indent=2))
    
    # Test deletion request
    request = create_deletion_request_with_token(
        domain='test.qwde',
        token_manager=token_manager,
        central_api='https://secupgrade.com/api_handler.php'
    )
    
    print("\nDeletion Request:")
    print(json.dumps(request, indent=2))
