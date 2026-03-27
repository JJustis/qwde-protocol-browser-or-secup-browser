"""
QWDE PHP Server Launcher
Wraps PHP built-in server to serve the DDNS API
This allows running the PHP backend without installing Apache/Nginx
"""

import subprocess
import sys
import os
import socket
import webbrowser
import threading
import time

DEFAULT_PORT = 8080
PHP_FILE = 'qwde_ddns_api.php'

def check_php_installed():
    """Check if PHP is installed"""
    try:
        result = subprocess.run(['php', '-v'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ PHP found: {result.stdout.splitlines()[0]}")
            return True
    except FileNotFoundError:
        print("✗ PHP not found in PATH")
        return False
    return False

def find_available_port(start_port=DEFAULT_PORT):
    """Find an available port"""
    for port in range(start_port, start_port + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return port
            except OSError:
                continue
    return DEFAULT_PORT

def run_php_server(port=DEFAULT_PORT):
    """Run PHP built-in server"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    php_file = os.path.join(script_dir, PHP_FILE)
    
    if not os.path.exists(php_file):
        print(f"Error: {PHP_FILE} not found!")
        return
    
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║         QWDE PHP DDNS Server                              ║
╠═══════════════════════════════════════════════════════════╣
║  Starting PHP built-in server...                          ║
║                                                           ║
║  URL: http://localhost:{port}/{PHP_FILE}                  ║
║  API: http://localhost:{port}/qwde_ddns_api.php           ║
║                                                           ║
║  Press Ctrl+C to stop                                     ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Open browser to test page
    test_url = f"http://localhost:{port}/{PHP_FILE}?action=get_stats"
    
    def open_browser():
        time.sleep(2)
        webbrowser.open(test_url)
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    try:
        subprocess.run([
            'php', '-S', f'localhost:{port}', php_file
        ], cwd=script_dir)
    except KeyboardInterrupt:
        print("\nServer stopped.")

def main():
    """Main entry point"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║      QWDE PHP Server Launcher                             ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Check PHP
    if not check_php_installed():
        print("\nPHP is required but not installed.")
        print("Download from: https://windows.php.net/download/")
        print("\nAlternatively, use the MySQL server:")
        print("  QWDE_Central_Server.exe --server")
        input("\nPress Enter to exit...")
        return
    
    # Find port
    port = find_available_port()
    
    # Run server
    run_php_server(port)

if __name__ == '__main__':
    main()
