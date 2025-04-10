import random
import string
import socket
import logging
import subprocess
import os
import sys
import time

logger = logging.getLogger("anonymity")

class AnonymityUtils:
    @staticmethod
    def generate_username():
        """Generate a random anonymous username"""
        animals = [
            'Falcon', 'Wolf', 'Panther', 'Raven', 'Cobra', 'Hawk', 'Fox',
            'Eagle', 'Tiger', 'Shark', 'Viper', 'Lion', 'Dragon', 'Bear',
            'Owl', 'Scorpion', 'Lynx', 'Jaguar', 'Phoenix', 'Mantis'
        ]
        
        adjectives = [
            'Silent', 'Shadow', 'Swift', 'Mystic', 'Phantom', 'Stealth', 'Dark',
            'Crimson', 'Midnight', 'Rogue', 'Ghost', 'Cyber', 'Quantum', 'Frost',
            'Hidden', 'Enigma', 'Covert', 'Nebula', 'Void', 'Cipher'
        ]
        
        return f"{random.choice(adjectives)}{random.choice(animals)}{random.randint(10, 99)}"
    
    @staticmethod
    def check_tor_connection():
        """Check if Tor is running and accessible"""
        try:
            # Try to connect to the Tor SOCKS proxy
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect(('127.0.0.1', 9050))
            s.close()
            return True
        except Exception as e:
            logger.debug(f"Tor connection check failed: {e}")
            return False
    
    @staticmethod
    def start_tor():
        """Attempt to start Tor if not running (platform-specific)"""
        if AnonymityUtils.check_tor_connection():
            logger.info("Tor is already running")
            return True
            
        logger.info("Attempting to start Tor...")
        
        try:
            if sys.platform == 'win32':  # Windows
                # Try to start Tor Browser in the background
                tor_paths = [
                    os.path.expanduser("~\\Desktop\\Tor Browser\\Browser\\TorBrowser\\Tor\\tor.exe"),
                    "C:\\Program Files\\Tor Browser\\Browser\\TorBrowser\\Tor\\tor.exe",
                    "C:\\Program Files (x86)\\Tor Browser\\Browser\\TorBrowser\\Tor\\tor.exe"
                ]
                
                for path in tor_paths:
                    if os.path.exists(path):
                        subprocess.Popen([path], 
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL,
                                        creationflags=subprocess.CREATE_NO_WINDOW)
                        break
            
            elif sys.platform == 'darwin':  # macOS
                subprocess.Popen(["open", "-a", "Tor Browser"], 
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
            
            else:  # Linux
                # Try common paths for Tor
                tor_paths = [
                    "/usr/bin/tor",
                    "/usr/local/bin/tor"
                ]
                
                for path in tor_paths:
                    if os.path.exists(path):
                        subprocess.Popen([path], 
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL)
                        break
            
            # Wait a bit for Tor to start
            time.sleep(5)
            return AnonymityUtils.check_tor_connection()
            
        except Exception as e:
            logger.error(f"Failed to start Tor: {e}")
            return False
    
    @staticmethod
    def get_ip_info(use_tor=False):
        """Get IP information (for testing anonymity)"""
        try:
            import requests
            
            if use_tor:
                # Configure requests to use Tor
                proxies = {
                    'http': 'socks5h://127.0.0.1:9050',
                    'https': 'socks5h://127.0.0.1:9050'
                }
                response = requests.get('https://api.ipify.org?format=json', proxies=proxies, timeout=10)
            else:
                response = requests.get('https://api.ipify.org?format=json', timeout=10)
                
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get IP info: {e}")
            return {"error": str(e)}
