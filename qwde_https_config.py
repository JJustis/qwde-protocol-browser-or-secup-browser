"""
QWDE Browser - HTTPS Configuration Module
Handles HTTPS settings and secure connections to central server
"""

import ssl
import configparser
import os
import certifi
from typing import Optional, Tuple


class HTTPSConfig:
    """Manages HTTPS configuration for QWDE Browser"""
    
    DEFAULT_CONFIG = {
        'central_server': {
            'protocol': 'https',
            'host': 'secupgrade.com',  # Base domain, no subdomain
            'port': '443',
            'api_path': '/qwde_ddns_api.php',
            'url': 'https://secupgrade.com/qwde_ddns_api.php'
        },
        'central_database': {
            'host': 'secupgrade.com',
            'port': '3306',
            'database_name': 'qwde_ddns',
            'username': 'qwde_user',
            'use_ssl': 'True'
        },
        'security': {
            'https_only': 'True',
            'verify_certificates': 'True',
            'verify_ssl_certs': 'True'
        }
    }
    
    def __init__(self, config_path: str = 'qwde_config.ini'):
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file"""
        # Set defaults
        for section, options in self.DEFAULT_CONFIG.items():
            if section not in self.config:
                self.config[section] = {}
            for key, value in options.items():
                if key not in self.config[section]:
                    self.config[section][key] = value
        
        # Load from file if exists
        if os.path.exists(self.config_path):
            self.config.read(self.config_path, encoding='utf-8')
    
    def save_config(self):
        """Save configuration to file"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)
    
    def get_server_url(self) -> str:
        """Get central server URL"""
        protocol = self.config.get('central_server', 'protocol', fallback='https')
        host = self.config.get('central_server', 'host', fallback='ddns.secupgrade.com')
        port = self.config.get('central_server', 'port', fallback='443')
        path = self.config.get('central_server', 'url', fallback=f'{protocol}://{host}/qwde_ddns_api.php')
        
        # If url is explicitly set, use it
        if 'url' in self.config['central_server']:
            return self.config['central_server']['url']
        
        # Otherwise construct from components
        return f'{protocol}://{host}:{port}/qwde_ddns_api.php'
    
    def is_https_only(self) -> bool:
        """Check if HTTPS-only mode is enabled"""
        return self.config.getboolean('security', 'https_only', fallback=True)
    
    def verify_certificates(self) -> bool:
        """Check if certificate verification is enabled"""
        return self.config.getboolean('security', 'verify_certificates', fallback=True)
    
    def get_ssl_context(self) -> Optional[ssl.SSLContext]:
        """Create SSL context for secure connections"""
        if not self.verify_certificates():
            # Create context without verification (for testing)
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            return context
        
        # Create context with verification
        context = ssl.create_default_context(cafile=certifi.where())
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        return context
    
    def is_production(self) -> bool:
        """Check if configured for production (secupgrade.com base domain)"""
        host = self.config.get('central_server', 'host', fallback='')
        return 'secupgrade.com' in host.lower()
    
    def get_database_config(self) -> dict:
        """Get central database configuration"""
        return {
            'host': self.config.get('central_database', 'host', fallback='secupgrade.com'),
            'port': self.config.getint('central_database', 'port', fallback=3306),
            'database': self.config.get('central_database', 'database_name', fallback='qwde_ddns'),
            'user': self.config.get('central_database', 'username', fallback='qwde_user'),
            'password': self.config.get('central_database', 'password', fallback=''),
            'use_ssl': self.config.getboolean('central_database', 'use_ssl', fallback=True)
        }
    
    def get_connection_info(self) -> dict:
        """Get connection information"""
        return {
            'url': self.get_server_url(),
            'protocol': self.config.get('central_server', 'protocol', fallback='https'),
            'host': self.config.get('central_server', 'host', fallback='ddns.secupgrade.com'),
            'port': self.config.getint('central_server', 'port', fallback=443),
            'https_only': self.is_https_only(),
            'verify_certs': self.verify_certificates(),
            'is_production': self.is_production()
        }
    
    def set_https_only(self, enabled: bool):
        """Enable/disable HTTPS-only mode"""
        self.config.set('security', 'https_only', str(enabled))
        self.save_config()
    
    def set_verify_certificates(self, enabled: bool):
        """Enable/disable certificate verification"""
        self.config.set('security', 'verify_certificates', str(enabled))
        self.save_config()
    
    def set_server_url(self, url: str):
        """Set custom server URL"""
        if 'central_server' not in self.config:
            self.config['central_server'] = {}
        self.config.set('central_server', 'url', url)
        self.save_config()
    
    def test_connection(self, timeout: int = 10) -> Tuple[bool, str]:
        """Test connection to central server"""
        import requests
        
        url = self.get_server_url()
        verify = self.verify_certificates()
        
        try:
            response = requests.get(
                url + '?action=get_stats',
                timeout=timeout,
                verify=verify
            )
            
            if response.status_code == 200:
                return True, f"Connected to {url}"
            else:
                return False, f"HTTP {response.status_code}"
                
        except requests.exceptions.SSLError as e:
            return False, f"SSL Error: {str(e)}"
        except requests.exceptions.ConnectionError as e:
            return False, f"Connection Error: {str(e)}"
        except requests.exceptions.Timeout:
            return False, "Connection Timeout"
        except Exception as e:
            return False, f"Error: {str(e)}"


# Global config instance
_config: Optional[HTTPSConfig] = None


def get_config() -> HTTPSConfig:
    """Get global HTTPS config instance"""
    global _config
    if _config is None:
        _config = HTTPSConfig()
    return _config


def get_server_url() -> str:
    """Get central server URL"""
    return get_config().get_server_url()


def is_https_enabled() -> bool:
    """Check if HTTPS is enabled"""
    return get_config().is_https_only()


def get_ssl_context() -> Optional[ssl.SSLContext]:
    """Get SSL context"""
    return get_config().get_ssl_context()


if __name__ == '__main__':
    # Test configuration
    config = HTTPSConfig()
    
    print("QWDE HTTPS Configuration")
    print("=" * 50)
    print(f"Server URL: {config.get_server_url()}")
    print(f"HTTPS Only: {config.is_https_only()}")
    print(f"Verify Certs: {config.verify_certificates()}")
    print(f"Production: {config.is_production()}")
    print()
    
    info = config.get_connection_info()
    print("Connection Info:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    print()
    
    print("Testing connection...")
    success, message = config.test_connection()
    print(f"Result: {'✓' if success else '✗'} {message}")
