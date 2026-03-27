"""
QWDE Protocol Package
Decentralized Web Protocol with Pin Wheel Connection System

Components:
    - qwde_ddns_server: Central DDNS for peer discovery and site registry
    - qwde_peer_network: P2P network with pin wheel connections
    - qwde_encryption: RSA + AES + Seeded Rolling Encryption
    - qwde_browser: GUI for browsing qwde:// sites
    - qwde_protocol: Main integration module

Protocol URL Format:
    qwde://domain       - Access site by domain
    qwde://fwild:N      - Access site by fwild number

Features:
    • Pin Wheel Connection System for load balancing
    • DDNS-based live peer discovery
    • fwild numbering for quick site lookups
    • RSA handshake with signature verification
    • AES-encrypted preshared key exchange
    • Seeded rolling encryption (per-message keys)
    • P2P site distribution and synchronization
    • GUI for site browsing and management
"""

__version__ = "1.0.0"
__author__ = "QWDE Protocol Team"

from .qwde_ddns_server import DDNSServer, DDNSClient, SiteInfo, PeerInfo
from .qwde_peer_network import QWDEPeer, create_peer, PinWheelConnection
from .qwde_encryption import (
    EncryptionManager, 
    QWDEEncryptionLayer, 
    SecureChannel,
    RSAKeyPair,
    SeededRollingEncryption
)
from .qwde_protocol import QWDEProtocol

__all__ = [
    # Version
    '__version__',
    '__author__',
    
    # DDNS
    'DDNSServer',
    'DDNSClient',
    'SiteInfo',
    'PeerInfo',
    
    # Peer Network
    'QWDEPeer',
    'create_peer',
    'PinWheelConnection',
    
    # Encryption
    'EncryptionManager',
    'QWDEEncryptionLayer',
    'SecureChannel',
    'RSAKeyPair',
    'SeededRollingEncryption',
    
    # Main Protocol
    'QWDEProtocol'
]
