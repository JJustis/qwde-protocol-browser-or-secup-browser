"""
QWDE Protocol - Encryption Layer
RSA Handshake + AES Key Exchange + Seeded Rolling Encryption
Custom encryption protocol with preshared key establishment
"""

import os
import hashlib
import threading
import time
from typing import Tuple, Optional, Dict, List
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature

from improved_qwde import (
    encrypt_qwde, decrypt_qwde,
    compute_D, compute_tau_infinity, compute_security_level
)

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RSAKeyPair:
    """RSA Key Pair for handshake"""
    
    def __init__(self, key_size: int = 2048):
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
    
    def get_public_key_pem(self) -> bytes:
        """Get public key in PEM format"""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    
    def load_public_key(self, pem_data: bytes) -> None:
        """Load a public key from PEM data"""
        self.remote_public_key = serialization.load_pem_public_key(
            pem_data,
            backend=default_backend()
        )
    
    def sign(self, data: bytes) -> bytes:
        """Sign data with private key"""
        return self.private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
    
    def verify(self, data: bytes, signature: bytes) -> bool:
        """Verify signature with remote public key"""
        try:
            self.remote_public_key.verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except InvalidSignature:
            return False
    
    def encrypt_rsa(self, data: bytes) -> bytes:
        """Encrypt data with remote public key"""
        return self.remote_public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
    
    def decrypt_rsa(self, data: bytes) -> bytes:
        """Decrypt data with private key"""
        return self.private_key.decrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )


class SeededRollingEncryption:
    """
    Custom Seeded Rolling Encryption
    Uses evolving seeds for each message with rolling key derivation
    """
    
    def __init__(self, initial_seed: bytes, rolling_counter: int = 0):
        self.initial_seed = initial_seed
        self.rolling_counter = rolling_counter
        self.lock = threading.Lock()
    
    def _derive_rolling_key(self, counter: int) -> bytes:
        """Derive a key based on rolling counter"""
        # Combine initial seed with counter for unique key per message
        seed_material = self.initial_seed + counter.to_bytes(8, 'big')
        return hashlib.sha256(seed_material).digest()
    
    def _generate_iv(self, counter: int) -> bytes:
        """Generate deterministic IV based on counter"""
        iv_material = self.initial_seed + (counter + 1).to_bytes(8, 'big')
        return hashlib.md5(iv_material).digest()
    
    def encrypt(self, plaintext: bytes) -> Tuple[bytes, int]:
        """
        Encrypt with rolling key
        Returns: (ciphertext, counter_used)
        """
        with self.lock:
            key = self._derive_rolling_key(self.rolling_counter)
            iv = self._generate_iv(self.rolling_counter)
            
            # Pad plaintext
            pad_len = 16 - (len(plaintext) % 16)
            padded = plaintext + bytes([pad_len] * pad_len)
            
            # AES-CBC encryption
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(padded) + encryptor.finalize()
            
            # Prepend counter for decryption
            full_ciphertext = self.rolling_counter.to_bytes(8, 'big') + iv + ciphertext
            
            counter_used = self.rolling_counter
            self.rolling_counter += 1
            
            return full_ciphertext, counter_used
    
    def decrypt(self, full_ciphertext: bytes) -> bytes:
        """
        Decrypt rolling encrypted data
        """
        if len(full_ciphertext) < 24:  # 8 (counter) + 16 (iv)
            raise ValueError("Ciphertext too short")
        
        counter = int.from_bytes(full_ciphertext[:8], 'big')
        iv = full_ciphertext[8:24]
        ciphertext = full_ciphertext[24:]
        
        key = self._derive_rolling_key(counter)
        
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Remove padding
        pad_len = padded[-1]
        if pad_len < 1 or pad_len > 16:
            raise ValueError("Invalid padding")
        
        return padded[:-pad_len]
    
    def reset(self, new_seed: bytes):
        """Reset with new seed"""
        self.initial_seed = new_seed
        self.rolling_counter = 0


class QWDEEncryptionLayer:
    """
    Complete QWDE Encryption Layer
    Combines RSA handshake, AES key exchange, and custom rolling encryption
    """
    
    PROTOCOL_VERSION = b"QWDE-1.0"
    
    def __init__(self, peer_id: str):
        self.peer_id = peer_id
        self.key_pair = RSAKeyPair()
        
        # Session state
        self.session_keys: Dict[str, bytes] = {}  # peer_id -> shared key
        self.rolling_encryptions: Dict[str, SeededRollingEncryption] = {}
        
        # Handshake state
        self.handshake_state: Dict[str, dict] = {}
        
        # QWDE parameters (from improved_qwde.py)
        self.qwde_params = {
            'omega': 1.0,
            'tau_max': 1.0,
            'eta': 0.1,
            'n': 100,
            'kappa': 0.01
        }
    
    def create_handshake_request(self) -> dict:
        """Create initial handshake request"""
        public_key_pem = self.key_pair.get_public_key_pem()
        
        return {
            'type': 'handshake_request',
            'version': self.PROTOCOL_VERSION.decode(),
            'peer_id': self.peer_id,
            'public_key': public_key_pem.decode('utf-8'),
            'timestamp': time.time()
        }
    
    def handle_handshake_request(self, request: dict) -> dict:
        """Handle incoming handshake request"""
        remote_peer_id = request['peer_id']
        remote_public_key = request['public_key'].encode('utf-8')
        
        # Store remote public key
        self.key_pair.load_public_key(remote_public_key)
        
        # Generate preshared key for this session
        preshared_key = os.urandom(32)
        self.session_keys[remote_peer_id] = preshared_key
        
        # Encrypt preshared key with remote public key
        encrypted_psk = self.key_pair.encrypt_rsa(preshared_key)
        
        # Sign the handshake
        handshake_data = f"{self.peer_id}:{request['timestamp']}".encode('utf-8')
        signature = self.key_pair.sign(handshake_data)
        
        # Store handshake state
        self.handshake_state[remote_peer_id] = {
            'preshared_key': preshared_key,
            'initiated': False
        }
        
        # Initialize rolling encryption with preshared key
        self.rolling_encryptions[remote_peer_id] = SeededRollingEncryption(preshared_key)
        
        return {
            'type': 'handshake_response',
            'version': self.PROTOCOL_VERSION.decode(),
            'peer_id': self.peer_id,
            'public_key': self.key_pair.get_public_key_pem().decode('utf-8'),
            'encrypted_psk': encrypted_psk.hex(),
            'signature': signature.hex(),
            'timestamp': time.time()
        }
    
    def handle_handshake_response(self, response: dict, original_request: dict) -> bool:
        """Handle handshake response"""
        remote_peer_id = response['peer_id']
        
        # Verify signature
        handshake_data = f"{remote_peer_id}:{original_request['timestamp']}".encode('utf-8')
        signature = bytes.fromhex(response['signature'])
        
        # Load remote public key
        self.key_pair.load_public_key(response['public_key'].encode('utf-8'))
        
        if not self.key_pair.verify(handshake_data, signature):
            logger.error("Handshake signature verification failed")
            return False
        
        # Decrypt preshared key (if we sent one)
        if 'encrypted_psk' in response:
            encrypted_psk = bytes.fromhex(response['encrypted_psk'])
            try:
                preshared_key = self.key_pair.decrypt_rsa(encrypted_psk)
                self.session_keys[remote_peer_id] = preshared_key
                self.rolling_encryptions[remote_peer_id] = SeededRollingEncryption(preshared_key)
            except Exception as e:
                logger.error(f"Failed to decrypt PSK: {e}")
                return False
        
        self.handshake_state[remote_peer_id] = {
            'completed': True,
            'timestamp': time.time()
        }
        
        logger.info(f"Handshake completed with {remote_peer_id}")
        return True
    
    def encrypt_message(self, peer_id: str, plaintext: bytes) -> dict:
        """
        Encrypt message for peer using custom protocol
        Wraps QWDE encryption in AES with rolling keys
        """
        if peer_id not in self.rolling_encryptions:
            raise ValueError(f"No established session with {peer_id}")
        
        rolling_enc = self.rolling_encryptions[peer_id]
        
        # Step 1: Apply QWDE encryption (from improved_qwde.py)
        S = self.session_keys.get(peer_id, os.urandom(16))
        E = hashlib.sha256(plaintext).digest()
        U = os.urandom(16)
        
        qwde_result = encrypt_qwde(
            S=S, E=E, U=U, plaintext=plaintext,
            omega=self.qwde_params['omega'],
            tau_max=self.qwde_params['tau_max'],
            eta=self.qwde_params['eta'],
            n=self.qwde_params['n'],
            kappa=self.qwde_params['kappa'],
            morph_counter=0
        )
        
        # Serialize QWDE ciphertext
        qwde_data = {
            'ciphertexts': [ct.hex() for ct in qwde_result['ciphertexts']],
            'seeds': [s.hex() for s in qwde_result['seeds']],
            'ec_hash': qwde_result['error_correction_hash'].hex(),
            'morph_counter': qwde_result['morph_counter'],
            'temporal_params': qwde_result['temporal_parameters']
        }
        
        qwde_serialized = str(qwde_data).encode('utf-8')
        
        # Step 2: Apply rolling encryption
        rolled_ciphertext, counter = rolling_enc.encrypt(qwde_serialized)
        
        # Step 3: Create final wrapped message
        message = {
            'type': 'encrypted_message',
            'version': self.PROTOCOL_VERSION.decode(),
            'sender': self.peer_id,
            'counter': counter,
            'payload': rolled_ciphertext.hex(),
            'timestamp': time.time()
        }
        
        return message
    
    def decrypt_message(self, sender_id: str, message: dict) -> bytes:
        """
        Decrypt message from peer
        """
        if sender_id not in self.rolling_encryptions:
            raise ValueError(f"No established session with {sender_id}")
        
        rolling_enc = self.rolling_encryptions[sender_id]
        
        # Extract payload
        payload = bytes.fromhex(message['payload'])
        
        # Step 1: Decrypt rolling encryption
        qwde_serialized = rolling_enc.decrypt(payload)
        
        # Step 2: Parse QWDE data
        qwde_data = eval(qwde_serialized.decode('utf-8'))
        
        # Reconstruct QWDE components
        ciphertexts = [bytes.fromhex(ct) for ct in qwde_data['ciphertexts']]
        seeds = [bytes.fromhex(s) for s in qwde_data['seeds']]
        ec_hash = bytes.fromhex(qwde_data['ec_hash'])
        temporal_params = qwde_data['temporal_params']
        
        # Get E and U (would normally be transmitted separately or derived)
        E = os.urandom(32)  # Placeholder - should be derived from session
        U = os.urandom(16)
        
        # Step 3: Decrypt QWDE
        plaintext = decrypt_qwde(
            seeds=seeds,
            E=E,
            U=U,
            ciphertexts=ciphertexts,
            temporal_params=temporal_params,
            error_correction_hash=ec_hash
        )
        
        return plaintext
    
    def get_session_info(self, peer_id: str) -> dict:
        """Get session information for a peer"""
        return {
            'peer_id': peer_id,
            'has_session': peer_id in self.session_keys,
            'has_rolling_enc': peer_id in self.rolling_encryptions,
            'handshake_complete': self.handshake_state.get(peer_id, {}).get('completed', False)
        }
    
    def rotate_session_key(self, peer_id: str) -> bytes:
        """Rotate session key for forward secrecy"""
        if peer_id not in self.session_keys:
            raise ValueError(f"No session with {peer_id}")
        
        # Generate new key
        new_key = os.urandom(32)
        self.session_keys[peer_id] = new_key
        
        # Reset rolling encryption with new seed
        self.rolling_encryptions[peer_id] = SeededRollingEncryption(new_key)
        
        logger.info(f"Rotated session key for {peer_id}")
        return new_key


class SecureChannel:
    """
    Secure Communication Channel
    Manages encrypted communication between peers
    """
    
    def __init__(self, encryption_layer: QWDEEncryptionLayer, peer_id: str):
        self.encryption = encryption_layer
        self.local_peer_id = encryption_layer.peer_id
        self.remote_peer_id = peer_id
        self.is_established = False
        self.message_queue = []
        self.lock = threading.Lock()
    
    def initiate_handshake(self) -> dict:
        """Initiate handshake with remote peer"""
        return self.encryption.create_handshake_request()
    
    def complete_handshake(self, request: dict, response: dict) -> bool:
        """Complete handshake with response"""
        return self.encryption.handle_handshake_response(response, request)
    
    def send(self, data: bytes) -> dict:
        """Send encrypted data"""
        if not self.is_established:
            raise ValueError("Channel not established")
        
        return self.encryption.encrypt_message(self.remote_peer_id, data)
    
    def receive(self, message: dict) -> bytes:
        """Receive and decrypt data"""
        if not self.is_established:
            raise ValueError("Channel not established")
        
        sender = message.get('sender')
        return self.encryption.decrypt_message(sender, message)
    
    def close(self):
        """Close the secure channel"""
        with self.lock:
            self.is_established = False
            self.message_queue.clear()


class EncryptionManager:
    """
    Central Encryption Manager
    Handles all encryption operations for QWDE protocol
    """
    
    def __init__(self, peer_id: str):
        self.peer_id = peer_id
        self.encryption_layer = QWDEEncryptionLayer(peer_id)
        self.channels: Dict[str, SecureChannel] = {}
        self.lock = threading.Lock()
    
    def get_or_create_channel(self, remote_peer_id: str) -> SecureChannel:
        """Get or create secure channel for peer"""
        with self.lock:
            if remote_peer_id not in self.channels:
                self.channels[remote_peer_id] = SecureChannel(
                    self.encryption_layer, remote_peer_id
                )
            return self.channels[remote_peer_id]
    
    def establish_secure_channel(self, remote_peer_id: str, 
                                  handshake_callback: callable) -> SecureChannel:
        """
        Establish secure channel with remote peer
        handshake_callback: function to send/receive handshake messages
        """
        channel = self.get_or_create_channel(remote_peer_id)
        
        # Initiate handshake
        handshake_request = channel.initiate_handshake()
        
        # Send and get response (via callback)
        handshake_response = handshake_callback(handshake_request)
        
        # Complete handshake
        if channel.complete_handshake(handshake_request, handshake_response):
            channel.is_established = True
        
        return channel
    
    def send_encrypted(self, remote_peer_id: str, data: bytes) -> dict:
        """Send encrypted message to peer"""
        channel = self.get_or_create_channel(remote_peer_id)
        return channel.send(data)
    
    def receive_encrypted(self, message: dict) -> bytes:
        """Receive encrypted message"""
        sender = message.get('sender')
        channel = self.get_or_create_channel(sender)
        return channel.receive(message)
    
    def rotate_all_keys(self):
        """Rotate all session keys for forward secrecy"""
        for peer_id in list(self.channels.keys()):
            try:
                self.encryption_layer.rotate_session_key(peer_id)
            except Exception as e:
                logger.error(f"Failed to rotate key for {peer_id}: {e}")
    
    def get_stats(self) -> dict:
        """Get encryption manager statistics"""
        return {
            'peer_id': self.peer_id,
            'active_channels': len(self.channels),
            'sessions': {
                pid: self.encryption_layer.get_session_info(pid)
                for pid in self.channels.keys()
            }
        }


# Example usage and testing
if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════╗
║         QWDE Protocol Encryption Layer                    ║
╠═══════════════════════════════════════════════════════════╣
║  Features:                                                ║
║    • RSA Handshake with signature verification            ║
║    • AES-encrypted preshared key exchange                 ║
║    • Seeded rolling encryption (per-message keys)         ║
║    • QWDE polymorphic encryption wrapper                  ║
║    • Forward secrecy via key rotation                     ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Create encryption managers for two peers
    manager1 = EncryptionManager("peer-alpha")
    manager2 = EncryptionManager("peer-beta")
    
    # Simulate handshake
    channel1 = manager1.get_or_create_channel("peer-beta")
    channel2 = manager2.get_or_create_channel("peer-alpha")
    
    # Peer 1 initiates
    hs_request = channel1.initiate_handshake()
    
    # Peer 2 responds
    hs_response = manager2.encryption_layer.handle_handshake_request(hs_request)
    
    # Peer 1 completes
    if channel1.complete_handshake(hs_request, hs_response):
        channel1.is_established = True
        print("[+] Handshake completed (peer-alpha -> peer-beta)")
    
    # Peer 2 marks channel as established
    channel2.is_established = True
    
    # Test encrypted communication
    test_message = b"Hello QWDE Protocol!"
    
    encrypted = channel1.send(test_message)
    print(f"[+] Encrypted message: {encrypted['payload'][:64]}...")
    
    decrypted = channel2.receive(encrypted)
    print(f"[+] Decrypted message: {decrypted.decode()}")
    
    print(f"\n[✓] Encryption test passed: {test_message == decrypted}")
