"""
QWDE Protocol - Custom Protocol Handler
Reads protocol prefix from configuration file
Allows customization of protocol scheme (e.g., qwde://, this://, etc.)
"""

import configparser
import os
import re


class ProtocolHandler:
    """Handles custom protocol scheme configuration"""
    
    _instance = None
    _protocol_prefix = 'qwde'
    _protocol_separator = '://'
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load protocol configuration from qwde_config.ini"""
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), 'qwde_config.ini')
        
        if os.path.exists(config_path):
            config.read(config_path, encoding='utf-8')
            
            if 'protocol' in config:
                self._protocol_prefix = config.get('protocol', 'protocol_prefix', fallback='qwde')
                self._protocol_separator = config.get('protocol', 'protocol_separator', fallback='://')
        else:
            # Default values
            self._protocol_prefix = 'qwde'
            self._protocol_separator = ':///'
    
    def get_protocol_prefix(self) -> str:
        """Get the protocol prefix (e.g., 'qwde', 'this', 'mysite')"""
        return self._protocol_prefix
    
    def get_protocol_separator(self) -> str:
        """Get the protocol separator (default '://')"""
        return self._protocol_separator
    
    def get_full_protocol(self) -> str:
        """Get the full protocol string (e.g., 'qwde://')"""
        return f"{self._protocol_prefix}{self._protocol_separator}"
    
    def set_protocol_prefix(self, prefix: str):
        """Set a new protocol prefix"""
        self._protocol_prefix = prefix
        self._save_config()
    
    def _save_config(self):
        """Save protocol configuration to file"""
        config_path = os.path.join(os.path.dirname(__file__), 'qwde_config.ini')
        config = configparser.ConfigParser()
        
        if os.path.exists(config_path):
            config.read(config_path, encoding='utf-8')
        
        if 'protocol' not in config:
            config['protocol'] = {}
        
        config['protocol']['protocol_prefix'] = self._protocol_prefix
        config['protocol']['protocol_separator'] = self._protocol_separator
        
        with open(config_path, 'w', encoding='utf-8') as f:
            config.write(f)
    
    def is_valid_url(self, url: str) -> bool:
        """Check if URL matches the configured protocol"""
        pattern = f'^{re.escape(self.get_full_protocol())}'
        return bool(re.match(pattern, url, re.IGNORECASE))
    
    def strip_protocol(self, url: str) -> str:
        """Remove protocol prefix from URL"""
        pattern = f'^{re.escape(self.get_full_protocol())}'
        return re.sub(pattern, '', url, flags=re.IGNORECASE)
    
    def add_protocol(self, target: str) -> str:
        """Add protocol prefix to target if not present"""
        if self.is_valid_url(target):
            return target
        
        # Check if it already has a different protocol
        if re.match(r'^[a-zA-Z]+://', target):
            return target
        
        return f"{self.get_full_protocol()}{target}"
    
    def parse_url(self, url: str) -> dict:
        """
        Parse a protocol URL into components
        
        Returns:
            dict with keys:
            - protocol: The protocol (e.g., 'qwde://')
            - target: The target (domain or fwild:N)
            - type: 'domain' or 'fwild'
            - domain: Domain name (if type is 'domain')
            - fwild: Fwild number (if type is 'fwild')
        """
        if not self.is_valid_url(url):
            return {'error': 'Invalid protocol URL'}
        
        target = self.strip_protocol(url)
        
        result = {
            'protocol': self.get_full_protocol(),
            'target': target,
            'type': None,
            'domain': None,
            'fwild': None
        }
        
        # Check if it's a fwild lookup
        fwild_match = re.match(r'^fwild:(\d+)$', target, re.IGNORECASE)
        if fwild_match:
            result['type'] = 'fwild'
            result['fwild'] = int(fwild_match.group(1))
        else:
            result['type'] = 'domain'
            result['domain'] = target
        
        return result
    
    def create_url(self, target: str, url_type: str = 'domain') -> str:
        """
        Create a protocol URL from components
        
        Args:
            target: Domain name or fwild number
            url_type: 'domain' or 'fwild'
        """
        if url_type == 'fwild':
            return f"{self.get_full_protocol()}fwild:{target}"
        else:
            return f"{self.get_full_protocol()}{target}"


# Global instance
_protocol_handler: ProtocolHandler = None


def get_protocol_handler() -> ProtocolHandler:
    """Get the global protocol handler instance"""
    global _protocol_handler
    if _protocol_handler is None:
        _protocol_handler = ProtocolHandler()
    return _protocol_handler


# Convenience functions
def get_protocol() -> str:
    """Get the full protocol string (e.g., 'qwde://')"""
    return get_protocol_handler().get_full_protocol()


def get_protocol_prefix() -> str:
    """Get the protocol prefix (e.g., 'qwde')"""
    return get_protocol_handler().get_protocol_prefix()


def is_valid_url(url: str) -> bool:
    """Check if URL matches the configured protocol"""
    return get_protocol_handler().is_valid_url(url)


def strip_protocol(url: str) -> str:
    """Remove protocol prefix from URL"""
    return get_protocol_handler().strip_protocol(url)


def add_protocol(target: str) -> str:
    """Add protocol prefix to target"""
    return get_protocol_handler().add_protocol(target)


def parse_url(url: str) -> dict:
    """Parse a protocol URL into components"""
    return get_protocol_handler().parse_url(url)


def create_url(target: str, url_type: str = 'domain') -> str:
    """Create a protocol URL from components"""
    return get_protocol_handler().create_url(target, url_type)


# Test the protocol handler
if __name__ == '__main__':
    handler = ProtocolHandler()
    
    print("QWDE Protocol Handler")
    print("=" * 50)
    print(f"Protocol Prefix: {handler.get_protocol_prefix()}")
    print(f"Protocol Separator: {handler.get_protocol_separator()}")
    print(f"Full Protocol: {handler.get_full_protocol()}")
    print()
    
    # Test URLs
    test_urls = [
        'qwde://mysite.qwde',
        'qwde://fwild:123',
        'qwde://test',
        'http://example.com',
        'this://mysite'
    ]
    
    print("URL Tests:")
    for url in test_urls:
        is_valid = handler.is_valid_url(url)
        parsed = handler.parse_url(url) if is_valid else {'error': 'Invalid'}
        print(f"  {url:30} - Valid: {is_valid} - Parsed: {parsed}")
    
    print()
    print("Create URL Tests:")
    print(f"  Domain 'test.qwde':  {handler.create_url('test.qwde')}")
    print(f"  Fwild 42:            {handler.create_url('42', 'fwild')}")
