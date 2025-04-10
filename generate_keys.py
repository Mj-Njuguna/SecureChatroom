#!/usr/bin/env python3
"""
SecureChatroom Key Generator
Generates RSA key pair for secure communication.
"""

import sys
import os
import argparse
import logging

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.crypto.key_management import KeyManager

def main():
    # Setup argument parser
    parser = argparse.ArgumentParser(description="Generate RSA keys for SecureChatroom")
    parser.add_argument("--key-size", type=int, default=2048, 
                        help="RSA key size in bits (default: 2048)")
    parser.add_argument("--private-key", type=str, default="server_private.pem",
                        help="Private key filename (default: server_private.pem)")
    parser.add_argument("--public-key", type=str, default="server_public.pem",
                        help="Public key filename (default: server_public.pem)")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing keys")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Check if keys already exist
    if KeyManager.check_keys_exist(args.private_key, args.public_key) and not args.force:
        print(f"RSA keys already exist. Use --force to overwrite.")
        return 1
    
    # Generate keys
    print(f"Generating {args.key_size}-bit RSA key pair...")
    if KeyManager.generate_rsa_keypair(args.key_size, args.private_key, args.public_key):
        print(f"Keys generated successfully:")
        print(f"  - Private key: {args.private_key}")
        print(f"  - Public key: {args.public_key}")
        print("\nIMPORTANT: Keep your private key secure!")
        return 0
    else:
        print("Failed to generate keys.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
