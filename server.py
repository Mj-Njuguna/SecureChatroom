#!/usr/bin/env python3
"""
SecureChatroom Server
A secure, anonymous, terminal-based chatroom server using end-to-end encryption.
"""

import sys
import os
import logging
import signal
import time

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.config import Config
from src.network.server import SecureServer
from src.crypto.key_management import KeyManager

def signal_handler(sig, frame):
    """Handle interrupt signals"""
    print("\nShutting down server...")
    sys.exit(0)

def main():
    # Load configuration
    config = Config()
    config.parse_args()
    logger = config.setup_logging()
    
    # Check if keys exist
    if not KeyManager.check_keys_exist():
        logger.error("RSA keys not found. Run generate_keys.py first.")
        print("Error: RSA keys not found. Run generate_keys.py first.")
        return 1
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start server
        server = SecureServer(config.host, config.port)
        print(f"Starting secure server on {config.host}:{config.port}")
        server.start()
    except Exception as e:
        logger.error(f"Server error: {e}")
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
