"""
QWDE Protocol - Main Integration Module
Brings together all components of the QWDE protocol system
"""

import sys
import os
import threading
import time
import argparse
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qwde_ddns_server import DDNSServer, DDNSClient, run_central_server
from qwde_peer_network import QWDEPeer, create_peer
from qwde_encryption import EncryptionManager, QWDEEncryptionLayer
from qwde_browser import QWDEBrowserGUI, run_browser

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class QWDEProtocol:
    """
    Main QWDE Protocol Controller
    Integrates all components into a unified system
    """
    
    VERSION = "1.0.0"
    PROTOCOL_NAME = "qwde"
    
    def __init__(self, 
                 ddns_host: str = 'localhost',
                 ddns_port: int = 8765,
                 peer_port: int = 8766,
                 is_server: bool = False):
        """
        Initialize QWDE Protocol
        
        Args:
            ddns_host: DDNS server host
            ddns_port: DDNS server port
            peer_port: Local peer port
            is_server: Run as central DDNS server
        """
        self.ddns_host = ddns_host
        self.ddns_port = ddns_port
        self.peer_port = peer_port
        self.is_server = is_server
        
        self.ddns_server: Optional[DDNSServer] = None
        self.ddns_client: Optional[DDNSClient] = None
        self.peer: Optional[QWDEPeer] = None
        self.encryption_manager: Optional[EncryptionManager] = None
        self.browser_gui: Optional[QWDEBrowserGUI] = None
        
        self.running = False
    
    def start_server(self):
        """Start as central DDNS server"""
        print("""
╔═══════════════════════════════════════════════════════════╗
║         QWDE Protocol - Central DDNS Server               ║
╠═══════════════════════════════════════════════════════════╣
║  Starting Central Server...                               ║
║                                                           ║
║  Components:                                              ║
║    ✓ DDNS Server (Port 8765)                             ║
║    ✓ Peer Registry                                        ║
║    ✓ Site Database (fwild indexing)                      ║
║    ✓ Live Peer Selection (Pin Wheel)                     ║
╚═══════════════════════════════════════════════════════════╝
        """)
        
        self.ddns_server = DDNSServer(port=self.ddns_port, is_central=True)
        
        try:
            self.ddns_server.start()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            self.ddns_server.stop()
    
    def start_peer(self, headless: bool = False):
        """Start as peer node"""
        print(f"""
╔═══════════════════════════════════════════════════════════╗
║           QWDE Protocol - Peer Node                       ║
╠═══════════════════════════════════════════════════════════╣
║  Connecting to: {self.ddns_host}:{self.ddns_port}                          ║
║  Local Port: {self.peer_port}                                     ║
║                                                           ║
║  Components:                                              ║
║    • Pin Wheel Connection System                         ║
║    • P2P Site Distribution                               ║
║    • RSA + AES Encryption                                ║
║    • Seeded Rolling Encryption                           ║
║    • fwild Quick Lookup                                  ║
╚═══════════════════════════════════════════════════════════╝
        """)
        
        # Create peer
        self.peer = create_peer(
            ddns_host=self.ddns_host,
            ddns_port=self.ddns_port,
            port=self.peer_port
        )
        
        # Create encryption manager
        self.encryption_manager = EncryptionManager(self.peer.peer_id)
        
        # Create DDNS client
        self.ddns_client = DDNSClient(self.ddns_host, self.ddns_port)
        
        # Start peer in background thread
        peer_thread = threading.Thread(target=self.peer.start, daemon=True)
        peer_thread.start()
        
        # Wait for connection
        time.sleep(2)
        
        print(f"\n[+] Peer started: {self.peer.peer_id}")
        print(f"[+] Connected to DDNS: {self.ddns_host}:{self.ddns_port}")
        
        if not headless:
            # Start browser GUI
            self.start_browser()
        
        return self.peer
    
    def start_browser(self):
        """Start the browser GUI"""
        print("\n[+] Starting Browser GUI...")
        self.browser_gui = QWDEBrowserGUI()
        self.browser_gui.mainloop()
    
    def create_site(self, domain: str, content: str) -> dict:
        """
        Create and register a new site
        
        Args:
            domain: Site domain name
            content: Site content
            
        Returns:
            Registration result with fwild number
        """
        if not self.peer:
            raise RuntimeError("Peer not started")
        
        site_data = content.encode('utf-8')
        result = self.peer.register_site(domain, site_data)
        
        if result:
            logger.info(f"Created site: {domain} (fwild={result['fwild']})")
        else:
            logger.error(f"Failed to create site: {domain}")
        
        return result
    
    def get_site(self, identifier: str) -> Optional[bytes]:
        """
        Get site content by domain or fwild
        
        Args:
            identifier: Domain name or fwild:number
            
        Returns:
            Site content bytes or None
        """
        if not self.peer:
            raise RuntimeError("Peer not started")
        
        url = f"qwde://{identifier}"
        site = self.peer.resolve_qwde_url(url)
        
        if site:
            return site.site_data
        return None
    
    def resolve(self, qwde_url: str) -> Optional[dict]:
        """
        Resolve a qwde:// URL
        
        Args:
            qwde_url: Full qwde:// URL
            
        Returns:
            Site information dict or None
        """
        if not self.peer:
            raise RuntimeError("Peer not started")
        
        site = self.peer.resolve_qwde_url(qwde_url)
        
        if site:
            return {
                'domain': site.domain,
                'fwild': site.fwild,
                'size': len(site.site_data),
                'content': site.site_data,
                'creator': site.creator_peer_id,
                'version': site.version
            }
        return None
    
    def stop(self):
        """Stop all components"""
        self.running = False
        
        if self.peer:
            self.peer.stop()
        
        if self.ddns_client:
            self.ddns_client.close()
        
        if self.ddns_server:
            self.ddns_server.stop()
        
        logger.info("QWDE Protocol stopped")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='QWDE Protocol - Decentralized Web System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python qwde_protocol.py --server
      Start as central DDNS server
  
  python qwde_protocol.py --peer
      Start as peer node with browser
  
  python qwde_protocol.py --peer --headless
      Start as peer node (command line only)
  
  python qwde_protocol.py --create mysite "Hello World"
      Create a new site
  
  python qwde_protocol.py --get mysite
      Get site content
  
  python qwde_protocol.py --resolve qwde://mysite
      Resolve qwde:// URL
        """
    )
    
    parser.add_argument('--server', action='store_true',
                       help='Run as central DDNS server')
    parser.add_argument('--peer', action='store_true',
                       help='Run as peer node')
    parser.add_argument('--headless', action='store_true',
                       help='Run without GUI')
    parser.add_argument('--ddns-host', default='localhost',
                       help='DDNS server host (default: localhost)')
    parser.add_argument('--ddns-port', type=int, default=8765,
                       help='DDNS server port (default: 8765)')
    parser.add_argument('--peer-port', type=int, default=8766,
                       help='Local peer port (default: 8766)')
    parser.add_argument('--create', nargs=2, metavar=('DOMAIN', 'CONTENT'),
                       help='Create a new site')
    parser.add_argument('--get', metavar='DOMAIN',
                       help='Get site content')
    parser.add_argument('--resolve', metavar='URL',
                       help='Resolve qwde:// URL')
    parser.add_argument('--stats', action='store_true',
                       help='Show network statistics')
    
    args = parser.parse_args()
    
    # Create protocol instance
    protocol = QWDEProtocol(
        ddns_host=args.ddns_host,
        ddns_port=args.ddns_port,
        peer_port=args.peer_port
    )
    
    try:
        if args.server:
            protocol.start_server()
        
        elif args.peer:
            protocol.start_peer(headless=args.headless)
        
        elif args.create:
            # Quick site creation
            protocol.start_peer(headless=True)
            time.sleep(2)
            result = protocol.create_site(args.create[0], args.create[1])
            if result:
                print(f"\n[✓] Site created successfully!")
                print(f"    Domain: {args.create[0]}")
                print(f"    fwild: {result['fwild']}")
                print(f"    Version: {result['version']}")
            protocol.stop()
        
        elif args.get:
            # Get site content
            protocol.start_peer(headless=True)
            time.sleep(2)
            content = protocol.get_site(args.get)
            if content:
                print(f"\n[✓] Site content:")
                print(content.decode('utf-8'))
            else:
                print(f"\n[✗] Site not found: {args.get}")
            protocol.stop()
        
        elif args.resolve:
            # Resolve URL
            protocol.start_peer(headless=True)
            time.sleep(2)
            result = protocol.resolve(args.resolve)
            if result:
                print(f"\n[✓] Resolved:")
                print(f"    Domain: {result['domain']}")
                print(f"    fwild: {result['fwild']}")
                print(f"    Size: {result['size']} bytes")
                print(f"    Version: {result['version']}")
                print(f"    Creator: {result['creator']}")
            else:
                print(f"\n[✗] URL not found: {args.resolve}")
            protocol.stop()
        
        elif args.stats:
            # Show statistics
            client = DDNSClient(args.ddns_host, args.ddns_port)
            stats = client.get_stats()
            print(f"\n{'='*50}")
            print("QWDE Network Statistics")
            print(f"{'='*50}")
            print(f"Total Peers:  {stats.get('total_peers', 0)}")
            print(f"Live Peers:   {stats.get('live_peers', 0)}")
            print(f"Total Sites:  {stats.get('total_sites', 0)}")
            print(f"fwild Counter: {stats.get('fwild_counter', 0)}")
            print(f"{'='*50}")
            client.close()
        
        else:
            # Default: show help
            parser.print_help()
            
            print(f"""

╔═══════════════════════════════════════════════════════════╗
║              QWDE Protocol v{QWDEProtocol.VERSION}                      ║
╠═══════════════════════════════════════════════════════════╣
║  Quick Start:                                             ║
║                                                           ║
║  1. Start Central Server (first time):                   ║
║     python qwde_protocol.py --server                     ║
║                                                           ║
║  2. Start Peer with Browser:                             ║
║     python qwde_protocol.py --peer                       ║
║                                                           ║
║  3. Create a Site:                                       ║
║     python qwde_protocol.py --create mysite "Hello"      ║
║                                                           ║
║  4. Browse Sites:                                        ║
║     Use the GUI or:                                      ║
║     python qwde_protocol.py --resolve qwde://mysite      ║
╚═══════════════════════════════════════════════════════════╝
            """)
    
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        protocol.stop()
    except Exception as e:
        logger.error(f"Error: {e}")
        protocol.stop()
        sys.exit(1)


if __name__ == '__main__':
    main()
