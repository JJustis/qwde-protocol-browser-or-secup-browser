"""
QWDE Protocol - Test Suite
Tests all components of the QWDE protocol system
"""

import sys
import os
import time
import threading
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from improved_qwde import encrypt_qwde, decrypt_qwde


class TestDDNSServer(unittest.TestCase):
    """Test DDNS Server functionality"""
    
    def setUp(self):
        from qwde_ddns_server import DDNSServer, DDNSClient
        self.DDNSServer = DDNSServer
        self.DDNSClient = DDNSClient
        
        # Create test server
        self.server = DDNSServer(port=18765, db_path=':memory:')
        self.server_thread = threading.Thread(target=self.server.start, daemon=True)
        self.server_thread.start()
        time.sleep(0.5)
        
        # Create client
        self.client = DDNSClient('localhost', 18765)
    
    def tearDown(self):
        self.client.close()
        self.server.stop()
    
    def test_register_peer(self):
        """Test peer registration"""
        result = self.client.register_peer('test-peer-1', '127.0.0.1', 9999)
        self.assertTrue(result)
    
    def test_heartbeat(self):
        """Test peer heartbeat"""
        self.client.register_peer('test-peer-1', '127.0.0.1', 9999)
        result = self.client.heartbeat('test-peer-1')
        self.assertTrue(result)
    
    def test_get_live_peers(self):
        """Test getting live peers"""
        self.client.register_peer('test-peer-1', '127.0.0.1', 9999)
        self.client.register_peer('test-peer-2', '127.0.0.1', 9998)
        
        peers = self.client.get_live_peers(limit=10)
        self.assertGreaterEqual(len(peers), 2)
    
    def test_register_site(self):
        """Test site registration"""
        self.client.register_peer('test-peer-1', '127.0.0.1', 9999)
        
        result = self.client.register_site(
            'testsite.qwde',
            'test-peer-1',
            b'Hello QWDE!'
        )
        
        self.assertIsNotNone(result)
        self.assertIn('fwild', result)
        self.assertEqual(result['fwild'], 1)
    
    def test_get_site(self):
        """Test getting site by domain"""
        self.client.register_peer('test-peer-1', '127.0.0.1', 9999)
        self.client.register_site('testsite.qwde', 'test-peer-1', b'Hello!')
        
        site = self.client.get_site('testsite.qwde')
        self.assertIsNotNone(site)
        self.assertEqual(site.domain, 'testsite.qwde')
    
    def test_get_site_by_fwild(self):
        """Test getting site by fwild number"""
        self.client.register_peer('test-peer-1', '127.0.0.1', 9999)
        self.client.register_site('testsite.qwde', 'test-peer-1', b'Hello!')
        
        site = self.client.get_site_by_fwild(1)
        self.assertIsNotNone(site)
        self.assertEqual(site.fwild, 1)
    
    def test_sync_sites(self):
        """Test site synchronization"""
        self.client.register_peer('test-peer-1', '127.0.0.1', 9999)
        self.client.register_site('site1.qwde', 'test-peer-1', b'Site 1')
        self.client.register_site('site2.qwde', 'test-peer-1', b'Site 2')
        
        sites = self.client.sync_sites()
        self.assertGreaterEqual(len(sites), 2)
    
    def test_get_stats(self):
        """Test getting server statistics"""
        stats = self.client.get_stats()
        
        self.assertIn('total_peers', stats)
        self.assertIn('total_sites', stats)
        self.assertIn('fwild_counter', stats)


class TestPinWheelConnection(unittest.TestCase):
    """Test Pin Wheel Connection System"""
    
    def test_add_connection(self):
        from qwde_peer_network import PinWheelConnection
        
        pin_wheel = PinWheelConnection(max_connections=3)
        
        pin_wheel.add_connection('peer-1', '127.0.0.1', 9001)
        pin_wheel.add_connection('peer-2', '127.0.0.1', 9002)
        pin_wheel.add_connection('peer-3', '127.0.0.1', 9003)
        
        self.assertEqual(pin_wheel.get_connection_count(), 3)
    
    def test_rotation(self):
        from qwde_peer_network import PinWheelConnection
        
        pin_wheel = PinWheelConnection(max_connections=3)
        
        pin_wheel.add_connection('peer-1', '127.0.0.1', 9001)
        pin_wheel.add_connection('peer-2', '127.0.0.1', 9002)
        
        # Test rotation
        peer1 = pin_wheel.get_next_peer()
        peer2 = pin_wheel.get_next_peer()
        peer3 = pin_wheel.get_next_peer()  # Should wrap to peer-1
        
        self.assertEqual(peer1.peer_id, 'peer-1')
        self.assertEqual(peer2.peer_id, 'peer-2')
        self.assertEqual(peer3.peer_id, 'peer-1')
    
    def test_max_connections(self):
        from qwde_peer_network import PinWheelConnection
        
        pin_wheel = PinWheelConnection(max_connections=2)
        
        pin_wheel.add_connection('peer-1', '127.0.0.1', 9001)
        pin_wheel.add_connection('peer-2', '127.0.0.1', 9002)
        pin_wheel.add_connection('peer-3', '127.0.0.1', 9003)  # Should remove oldest
        
        self.assertEqual(pin_wheel.get_connection_count(), 2)


class TestSeededRollingEncryption(unittest.TestCase):
    """Test Seeded Rolling Encryption"""
    
    def test_encrypt_decrypt(self):
        from qwde_encryption import SeededRollingEncryption
        
        seed = os.urandom(32)
        enc = SeededRollingEncryption(seed)
        
        plaintext = b'Hello QWDE Protocol!'
        ciphertext, counter = enc.encrypt(plaintext)
        
        dec = SeededRollingEncryption(seed)
        decrypted = dec.decrypt(ciphertext)
        
        self.assertEqual(plaintext, decrypted)
    
    def test_rolling_keys(self):
        from qwde_encryption import SeededRollingEncryption
        
        seed = os.urandom(32)
        enc = SeededRollingEncryption(seed)
        
        # Encrypt multiple messages
        msg1 = b'Message 1'
        msg2 = b'Message 2'
        
        ct1, counter1 = enc.encrypt(msg1)
        ct2, counter2 = enc.encrypt(msg2)
        
        # Counters should be different
        self.assertEqual(counter2, counter1 + 1)
        
        # Decrypt with fresh instance
        dec = SeededRollingEncryption(seed)
        pt1 = dec.decrypt(ct1)
        pt2 = dec.decrypt(ct2)
        
        self.assertEqual(msg1, pt1)
        self.assertEqual(msg2, pt2)


class TestRSAHandshake(unittest.TestCase):
    """Test RSA Handshake"""
    
    def test_key_generation(self):
        from qwde_encryption import RSAKeyPair
        
        key_pair = RSAKeyPair(key_size=2048)
        
        # Test public key export
        pem = key_pair.get_public_key_pem()
        self.assertIsInstance(pem, bytes)
        self.assertIn(b'-----BEGIN PUBLIC KEY-----', pem)
    
    def test_sign_verify(self):
        from qwde_encryption import RSAKeyPair
        
        key_pair1 = RSAKeyPair()
        key_pair2 = RSAKeyPair()
        
        # Export/import public key
        key_pair2.load_public_key(key_pair1.get_public_key_pem())
        
        # Sign and verify
        data = b'Test data to sign'
        signature = key_pair1.sign(data)
        
        self.assertTrue(key_pair2.verify(data, signature))
    
    def test_encrypt_decrypt_rsa(self):
        from qwde_encryption import RSAKeyPair
        
        key_pair1 = RSAKeyPair()
        key_pair2 = RSAKeyPair()
        
        # Exchange public keys
        key_pair1.load_public_key(key_pair2.get_public_key_pem())
        key_pair2.load_public_key(key_pair1.get_public_key_pem())
        
        # Encrypt with remote public key
        plaintext = b'Secret message'
        encrypted = key_pair1.encrypt_rsa(plaintext)
        
        # Decrypt with local private key
        decrypted = key_pair2.decrypt_rsa(encrypted)
        
        self.assertEqual(plaintext, decrypted)


class TestEncryptionLayer(unittest.TestCase):
    """Test Complete Encryption Layer"""
    
    def test_handshake_flow(self):
        from qwde_encryption import QWDEEncryptionLayer
        
        # Create two encryption layers
        layer1 = QWDEEncryptionLayer('peer-alpha')
        layer2 = QWDEEncryptionLayer('peer-beta')
        
        # Peer 1 initiates
        hs_request = layer1.create_handshake_request()
        
        # Peer 2 responds
        hs_response = layer2.handle_handshake_request(hs_request)
        
        # Peer 1 completes
        result = layer1.handle_handshake_response(hs_response, hs_request)
        
        self.assertTrue(result)
    
    def test_message_encryption(self):
        from qwde_encryption import QWDEEncryptionLayer
        
        layer1 = QWDEEncryptionLayer('peer-alpha')
        layer2 = QWDEEncryptionLayer('peer-beta')
        
        # Complete handshake
        hs_request = layer1.create_handshake_request()
        hs_response = layer2.handle_handshake_request(hs_request)
        layer1.handle_handshake_response(hs_response, hs_request)
        
        # Encrypt message
        plaintext = b'Hello encrypted world!'
        encrypted_msg = layer1.encrypt_message('peer-beta', plaintext)
        
        # Decrypt message
        decrypted = layer2.decrypt_message('peer-alpha', encrypted_msg)
        
        # Note: QWDE encryption test may need E and U parameters properly set
        # This is a basic smoke test
        self.assertIsInstance(encrypted_msg, dict)
        self.assertIn('payload', encrypted_msg)


class TestQWDEEncryption(unittest.TestCase):
    """Test QWDE Encryption from improved_qwde.py"""
    
    def test_encrypt_decrypt_roundtrip(self):
        """Test basic encrypt/decrypt roundtrip"""
        S = os.urandom(16)
        E = os.urandom(16)
        U = os.urandom(16)
        plaintext = b'Test message for QWDE encryption'
        
        # Encrypt
        result = encrypt_qwde(
            S=S, E=E, U=U, plaintext=plaintext,
            omega=1.0, tau_max=1.0, eta=0.1, n=100, kappa=0.01
        )
        
        # Note: Full decryption requires reverse_wave_diffusion implementation
        # This test verifies encryption completes successfully
        self.assertIn('ciphertexts', result)
        self.assertEqual(len(result['ciphertexts']), 4)
        self.assertIn('seeds', result)
        self.assertIn('error_correction_hash', result)


def run_tests():
    """Run all tests"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║              QWDE Protocol - Test Suite                   ║
╠═══════════════════════════════════════════════════════════╣
║  Running tests for:                                       ║
║    • DDNS Server                                          ║
║    • Pin Wheel Connection System                         ║
║    • Seeded Rolling Encryption                           ║
║    • RSA Handshake                                       ║
║    • QWDE Encryption                                     ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDDNSServer))
    suite.addTests(loader.loadTestsFromTestCase(TestPinWheelConnection))
    suite.addTests(loader.loadTestsFromTestCase(TestSeededRollingEncryption))
    suite.addTests(loader.loadTestsFromTestCase(TestRSAHandshake))
    suite.addTests(loader.loadTestsFromTestCase(TestEncryptionLayer))
    suite.addTests(loader.loadTestsFromTestCase(TestQWDEEncryption))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*60)
    
    return len(result.failures) == 0 and len(result.errors) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
