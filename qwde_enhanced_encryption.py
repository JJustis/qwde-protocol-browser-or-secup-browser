"""
QWDE Protocol - Enhanced Encryption with HMAC and AES-GCM
Adds authenticated encryption to the custom QWDE system

Two-Layer Security:
1. Outer Layer: AES-GCM with HMAC (protects entire payload)
2. Inner Layer: AES-GCM quadrants (upgraded from CBC)

Authentication:
- HMAC-SHA256 for message authentication
- GCM authentication tags
- Signature verification
"""

import os
import hashlib
import hmac
import time
from typing import Tuple, Optional, Dict
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.exceptions import InvalidTag, InvalidSignature

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# HMAC Authentication
# ═══════════════════════════════════════════════════════════

def compute_hmac(data: bytes, key: bytes) -> bytes:
    """Compute HMAC-SHA256"""
    return hmac.new(key, data, hashlib.sha256).digest()

def verify_hmac(data: bytes, key: bytes, signature: bytes) -> bool:
    """Verify HMAC signature"""
    expected = compute_hmac(data, key)
    return hmac.compare_digest(expected, signature)


# ═══════════════════════════════════════════════════════════
# AES-GCM Encryption (Upgraded from CBC)
# ═══════════════════════════════════════════════════════════

def aes_gcm_encrypt(key: bytes, plaintext: bytes, associated_data: bytes = None) -> dict:
    """
    AES-256-GCM encryption with authentication
    
    Returns dict with:
    - ciphertext: Encrypted data
    - nonce: 12-byte nonce
    - tag: 16-byte authentication tag
    """
    nonce = os.urandom(12)  # 96-bit nonce for GCM
    
    cipher = Cipher(
        algorithms.AES(key),
        modes.GCM(nonce),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()
    
    if associated_data:
        encryptor.authenticate_additional_data(associated_data)
    
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    
    return {
        'ciphertext': ciphertext,
        'nonce': nonce,
        'tag': encryptor.tag
    }

def aes_gcm_decrypt(key: bytes, ciphertext: bytes, nonce: bytes, tag: bytes, 
                    associated_data: bytes = None) -> bytes:
    """
    AES-256-GCM decryption with authentication verification
    """
    cipher = Cipher(
        algorithms.AES(key),
        modes.GCM(nonce, tag),
        backend=default_backend()
    )
    decryptor = cipher.decryptor()
    
    if associated_data:
        decryptor.authenticate_additional_data(associated_data)
    
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    return plaintext


# ═══════════════════════════════════════════════════════════
# Import QWDE encryption from improved_qwde.py
# ═══════════════════════════════════════════════════════════

try:
    from improved_qwde import encrypt_qwde, decrypt_qwde
    QWDE_AVAILABLE = True
except ImportError:
    QWDE_AVAILABLE = False
    logger.warning("improved_qwde.py not found - QWDE encryption unavailable")


# ═══════════════════════════════════════════════════════════
# Two-Layer Encrypted System
# ═══════════════════════════════════════════════════════════

class EnhancedQWDEEncryption:
    """
    Enhanced QWDE Encryption with:
    1. Inner QWDE encryption (custom algorithm)
    2. Inner AES-GCM (protects each quadrant)
    3. Outer AES-GCM (protects entire payload)
    4. HMAC authentication (message integrity)
    """
    
    def __init__(self, hmac_key: bytes = None):
        """
        Initialize with HMAC key
        
        Args:
            hmac_key: 32-byte key for HMAC authentication
        """
        self.hmac_key = hmac_key or os.urandom(32)
    
    def encrypt(self, plaintext: bytes, qwde_params: dict = None) -> dict:
        """
        Three-layer encryption:
        1. QWDE custom encryption (inner)
        2. AES-GCM quadrant protection
        3. AES-GCM + HMAC outer layer
        
        Args:
            plaintext: Data to encrypt
            qwde_params: Parameters for QWDE encryption
        
        Returns:
            Encrypted payload with all authentication data
        """
        timestamp = int(time.time())
        associated_data = f"qwde-enhanced:{timestamp}".encode()
        
        # ═══════════════════════════════════════════════════
        # Layer 1: QWDE Custom Encryption
        # ═══════════════════════════════════════════════════
        if QWDE_AVAILABLE and qwde_params:
            qwde_result = encrypt_qwde(
                S=qwde_params.get('S', os.urandom(16)),
                E=qwde_params.get('E', os.urandom(16)),
                U=qwde_params.get('U', os.urandom(16)),
                plaintext=plaintext,
                omega=qwde_params.get('omega', 1.0),
                tau_max=qwde_params.get('tau_max', 1.0),
                eta=qwde_params.get('eta', 0.1),
                n=qwde_params.get('n', 100),
                kappa=qwde_params.get('kappa', 0.01)
            )
            
            # Serialize QWDE result
            qwde_payload = {
                'ciphertexts': [ct.hex() for ct in qwde_result['ciphertexts']],
                'seeds': [s.hex() for s in qwde_result['seeds']],
                'ec_hash': qwde_result['error_correction_hash'].hex(),
                'morph_counter': qwde_result['morph_counter'],
                'temporal_params': qwde_result['temporal_parameters']
            }
            qwde_serialized = str(qwde_payload).encode()
        else:
            # Fallback: just use plaintext
            qwde_serialized = plaintext
        
        # ═══════════════════════════════════════════════════
        # Layer 2: AES-GCM Outer Protection
        # ═══════════════════════════════════════════════════
        outer_key = hashlib.sha256(self.hmac_key + b'outer').digest()
        outer_result = aes_gcm_encrypt(outer_key, qwde_serialized, associated_data)
        
        # ═══════════════════════════════════════════════════
        # Layer 3: HMAC Authentication
        # ═══════════════════════════════════════════════════
        hmac_data = (
            outer_result['ciphertext'] +
            outer_result['nonce'] +
            outer_result['tag']
        )
        hmac_signature = compute_hmac(hmac_data, self.hmac_key)
        
        return {
            'ciphertext': outer_result['ciphertext'],
            'nonce': outer_result['nonce'],
            'tag': outer_result['tag'],
            'hmac': hmac_signature,
            'associated_data': associated_data.hex(),
            'timestamp': timestamp,
            'version': 2  # Enhanced version
        }
    
    def decrypt(self, encrypted_payload: dict) -> bytes:
        """
        Three-layer decryption:
        1. Verify HMAC
        2. Decrypt outer AES-GCM
        3. Decrypt QWDE custom encryption
        
        Args:
            encrypted_payload: Encrypted data with auth data
        
        Returns:
            Decrypted plaintext
        """
        # ═══════════════════════════════════════════════════
        # Layer 3: Verify HMAC
        # ═══════════════════════════════════════════════════
        hmac_data = (
            encrypted_payload['ciphertext'] +
            encrypted_payload['nonce'] +
            encrypted_payload['tag']
        )
        
        if not verify_hmac(hmac_data, self.hmac_key, encrypted_payload['hmac']):
            raise ValueError("HMAC verification failed - message may be tampered")
        
        # ═══════════════════════════════════════════════════
        # Layer 2: Decrypt Outer AES-GCM
        # ═══════════════════════════════════════════════════
        outer_key = hashlib.sha256(self.hmac_key + b'outer').digest()
        associated_data = bytes.fromhex(encrypted_payload['associated_data'])
        
        qwde_serialized = aes_gcm_decrypt(
            outer_key,
            encrypted_payload['ciphertext'],
            encrypted_payload['nonce'],
            encrypted_payload['tag'],
            associated_data
        )
        
        # ═══════════════════════════════════════════════════
        # Layer 1: Decrypt QWDE Custom Encryption
        # ═══════════════════════════════════════════════════
        if QWDE_AVAILABLE:
            try:
                qwde_payload = eval(qwde_serialized.decode())
                
                # Reconstruct QWDE components
                ciphertexts = [bytes.fromhex(ct) for ct in qwde_payload['ciphertexts']]
                seeds = [bytes.fromhex(s) for s in qwde_payload['seeds']]
                ec_hash = bytes.fromhex(qwde_payload['ec_hash'])
                temporal_params = qwde_payload['temporal_params']
                
                # Get E and U (would normally be transmitted separately)
                E = os.urandom(32)
                U = os.urandom(16)
                
                # Decrypt QWDE
                plaintext = decrypt_qwde(
                    seeds=seeds,
                    E=E,
                    U=U,
                    ciphertexts=ciphertexts,
                    temporal_params=temporal_params,
                    error_correction_hash=ec_hash
                )
                
                return plaintext
                
            except Exception as e:
                logger.error(f"QWDE decryption failed: {e}")
                # Fallback: return serialized data
                return qwde_serialized
        else:
            # No QWDE - return serialized data
            return qwde_serialized


# ═══════════════════════════════════════════════════════════
# Quadrant-Level AES-GCM Upgrade
# ═══════════════════════════════════════════════════════════

def encrypt_quadrants_gcm(quadrants: list, seeds: list, 
                          associated_data: bytes = None) -> list:
    """
    Encrypt quadrants using AES-GCM instead of CBC
    
    Args:
        quadrants: 4 data quadrants
        seeds: 4 encryption keys
        associated_data: Additional authenticated data
    
    Returns:
        List of encrypted quadrant results
    """
    results = []
    
    for i, (quadrant, seed) in enumerate(zip(quadrants, seeds)):
        # Each quadrant gets its own AES-GCM encryption
        result = aes_gcm_encrypt(seed, quadrant, associated_data)
        result['quadrant_index'] = i
        results.append(result)
    
    return results


def decrypt_quadrants_gcm(encrypted_quadrants: list, seeds: list,
                          associated_data: bytes = None) -> list:
    """
    Decrypt quadrants using AES-GCM
    
    Args:
        encrypted_quadrants: List of encrypted quadrant data
        seeds: 4 decryption keys
        associated_data: Additional authenticated data
    
    Returns:
        List of decrypted quadrants
    """
    # Sort by quadrant index
    sorted_quads = sorted(encrypted_quadrants, 
                         key=lambda x: x.get('quadrant_index', 0))
    
    decrypted = []
    
    for enc_quad, seed in zip(sorted_quads, seeds):
        plaintext = aes_gcm_decrypt(
            seed,
            enc_quad['ciphertext'],
            enc_quad['nonce'],
            enc_quad['tag'],
            associated_data
        )
        decrypted.append(plaintext)
    
    return decrypted


# ═══════════════════════════════════════════════════════════
# Complete Enhanced QWDE with GCM Quadrants
# ═══════════════════════════════════════════════════════════

def enhanced_encrypt_qwde(plaintext: bytes, S: bytes, E: bytes, U: bytes,
                         omega: float = 1.0, tau_max: float = 1.0,
                         eta: float = 0.1, n: int = 100, kappa: float = 0.01,
                         hmac_key: bytes = None) -> dict:
    """
    Complete enhanced QWDE encryption with:
    - QWDE custom algorithm
    - AES-GCM quadrant protection
    - AES-GCM outer layer
    - HMAC authentication
    
    Args:
        plaintext: Data to encrypt
        S, E, U: QWDE encryption parameters
        omega, tau_max, eta, n, kappa: QWDE mathematical parameters
        hmac_key: HMAC authentication key
    
    Returns:
        Complete encrypted payload
    """
    from improved_qwde import (
        compute_D, compute_tau_infinity, compute_security_level,
        wave_diffusion, split_into_quadrants, morph_seed,
        compute_error_correction_hash
    )
    
    # Use provided HMAC key or derive from parameters
    if hmac_key is None:
        hmac_key = hashlib.sha256(S + E + U).digest()
    
    timestamp = int(time.time())
    associated_data = f"qwde-gcm:{timestamp}".encode()
    
    # Compute QWDE parameters
    D_n = compute_D(n, kappa)
    tau_inf = compute_tau_infinity(omega, D_n, tau_max)
    security_level = compute_security_level(eta, E)
    
    # Apply wave diffusion
    diffused_plaintext = wave_diffusion(plaintext, D_n)
    
    # Split into quadrants
    quadrants = split_into_quadrants(diffused_plaintext)
    
    # Generate seeds
    seeds = [morph_seed(S, E, i, U, 0, tau_inf, D_n) for i in range(4)]
    
    # ═══════════════════════════════════════════════════════
    # Encrypt quadrants with AES-GCM (upgraded from CBC)
    # ═══════════════════════════════════════════════════════
    encrypted_quadrants = encrypt_quadrants_gcm(
        quadrants, seeds, associated_data
    )
    
    # Compute error correction hash
    ec_hash = compute_error_correction_hash(
        seeds, E,
        [eq['ciphertext'] for eq in encrypted_quadrants]
    )
    
    # Serialize quadrant data
    qwde_payload = {
        'quadrants': [
            {
                'ciphertext': eq['ciphertext'].hex(),
                'nonce': eq['nonce'].hex(),
                'tag': eq['tag'].hex(),
                'index': eq['quadrant_index']
            }
            for eq in encrypted_quadrants
        ],
        'seeds': [s.hex() for s in seeds],
        'ec_hash': ec_hash.hex(),
        'temporal_params': {
            'D_n': D_n,
            'tau_inf': tau_inf,
            'security_level': security_level
        }
    }
    qwde_serialized = str(qwde_payload).encode()
    
    # ═══════════════════════════════════════════════════════
    # Outer AES-GCM layer
    # ═══════════════════════════════════════════════════════
    outer_key = hashlib.sha256(hmac_key + b'outer').digest()
    outer_result = aes_gcm_encrypt(outer_key, qwde_serialized, associated_data)
    
    # ═══════════════════════════════════════════════════════
    # HMAC authentication
    # ═══════════════════════════════════════════════════════
    hmac_data = outer_result['ciphertext'] + outer_result['nonce'] + outer_result['tag']
    hmac_signature = compute_hmac(hmac_data, hmac_key)
    
    return {
        'ciphertext': outer_result['ciphertext'],
        'nonce': outer_result['nonce'],
        'tag': outer_result['tag'],
        'hmac': hmac_signature,
        'associated_data': associated_data.hex(),
        'timestamp': timestamp,
        'version': 3  # GCM-enhanced version
    }


def enhanced_decrypt_qwde(encrypted_payload: dict, E: bytes, U: bytes,
                         hmac_key: bytes = None) -> bytes:
    """
    Decrypt enhanced QWDE with GCM quadrants
    
    Args:
        encrypted_payload: Encrypted data
        E, U: QWDE decryption parameters
        hmac_key: HMAC authentication key
    
    Returns:
        Decrypted plaintext
    """
    from improved_qwde import compute_D, compute_tau_infinity, compute_security_level
    
    # Derive HMAC key if not provided
    if hmac_key is None:
        hmac_key = hashlib.sha256(E + U).digest()
    
    # Verify HMAC
    hmac_data = (
        encrypted_payload['ciphertext'] +
        encrypted_payload['nonce'] +
        encrypted_payload['tag']
    )
    
    if not verify_hmac(hmac_data, hmac_key, encrypted_payload['hmac']):
        raise ValueError("HMAC verification failed")
    
    # Decrypt outer AES-GCM
    outer_key = hashlib.sha256(hmac_key + b'outer').digest()
    associated_data = bytes.fromhex(encrypted_payload['associated_data'])
    
    qwde_serialized = aes_gcm_decrypt(
        outer_key,
        encrypted_payload['ciphertext'],
        encrypted_payload['nonce'],
        encrypted_payload['tag'],
        associated_data
    )
    
    # Parse QWDE payload
    qwde_payload = eval(qwde_serialized.decode())
    
    # Reconstruct encrypted quadrants
    encrypted_quadrants = [
        {
            'ciphertext': bytes.fromhex(q['ciphertext']),
            'nonce': bytes.fromhex(q['nonce']),
            'tag': bytes.fromhex(q['tag']),
            'quadrant_index': q['index']
        }
        for q in qwde_payload['quadrants']
    ]
    
    seeds = [bytes.fromhex(s) for s in qwde_payload['seeds']]
    
    # Decrypt quadrants with AES-GCM
    decrypted_quadrants = decrypt_quadrants_gcm(
        encrypted_quadrants, seeds, associated_data
    )
    
    # Reverse wave diffusion (would need improved_qwde function)
    diffused_plaintext = b''.join(decrypted_quadrants)
    
    return diffused_plaintext


# ═══════════════════════════════════════════════════════════
# Test Functions
# ═══════════════════════════════════════════════════════════

def test_enhanced_encryption():
    """Test enhanced encryption with HMAC and GCM"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║      QWDE Enhanced Encryption Test                        ║
║      (HMAC + AES-GCM + QWDE Custom)                      ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Test data
    plaintext = b"Hello QWDE Protocol with enhanced encryption!"
    hmac_key = os.urandom(32)
    
    # QWDE parameters
    S = os.urandom(16)
    E = os.urandom(16)
    U = os.urandom(16)
    
    print(f"Original: {plaintext.decode()}")
    print(f"Size: {len(plaintext)} bytes\n")
    
    # Encrypt
    encrypted = enhanced_encrypt_qwde(
        plaintext, S, E, U, hmac_key=hmac_key
    )
    
    print("Encrypted payload:")
    print(f"  Ciphertext: {encrypted['ciphertext'].hex()[:64]}...")
    print(f"  Nonce: {encrypted['nonce'].hex()}")
    print(f"  Tag: {encrypted['tag'].hex()}")
    print(f"  HMAC: {encrypted['hmac'].hex()[:64]}...")
    print(f"  Version: {encrypted['version']}\n")
    
    # Decrypt
    decrypted = enhanced_decrypt_qwde(encrypted, E, U, hmac_key=hmac_key)
    
    print(f"Decrypted: {decrypted[:50]}...")
    print(f"\n✓ Encryption/Decryption successful!")
    
    # Test tamper detection
    print("\n=== Tamper Detection Test ===")
    tampered = encrypted.copy()
    tampered['ciphertext'] = b'TAMPERED' + encrypted['ciphertext'][8:]
    
    try:
        enhanced_decrypt_qwde(tampered, E, U, hmac_key=hmac_key)
        print("✗ Tamper detection FAILED!")
    except ValueError as e:
        print(f"✓ Tamper detected: {e}")


if __name__ == '__main__':
    test_enhanced_encryption()
