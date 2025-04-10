from Crypto.PublicKey import RSA
import os
import logging

logger = logging.getLogger("key_management")

class KeyManager:
    @staticmethod
    def generate_rsa_keypair(key_size=2048, private_key_file="server_private.pem", public_key_file="server_public.pem"):
        """Generate a new RSA key pair and save to files"""
        try:
            key = RSA.generate(key_size)
            
            # Save private key
            with open(private_key_file, "wb") as f:
                f.write(key.export_key())
                
            # Save public key
            with open(public_key_file, "wb") as f:
                f.write(key.publickey().export_key())
                
            logger.info(f"RSA key pair generated successfully: {key_size} bits")
            return True
        except Exception as e:
            logger.error(f"Error generating RSA key pair: {e}")
            return False
    
    @staticmethod
    def load_private_key(private_key_file="server_private.pem"):
        """Load RSA private key from file"""
        try:
            if not os.path.exists(private_key_file):
                logger.error(f"Private key file not found: {private_key_file}")
                return None
                
            with open(private_key_file, "rb") as f:
                key_data = f.read()
                
            private_key = RSA.import_key(key_data)
            return private_key
        except Exception as e:
            logger.error(f"Error loading private key: {e}")
            return None
    
    @staticmethod
    def load_public_key(public_key_file="server_public.pem"):
        """Load RSA public key from file"""
        try:
            if not os.path.exists(public_key_file):
                logger.error(f"Public key file not found: {public_key_file}")
                return None
                
            with open(public_key_file, "rb") as f:
                key_data = f.read()
                
            public_key = RSA.import_key(key_data)
            return public_key
        except Exception as e:
            logger.error(f"Error loading public key: {e}")
            return None
    
    @staticmethod
    def check_keys_exist(private_key_file="server_private.pem", public_key_file="server_public.pem"):
        """Check if key files exist"""
        private_exists = os.path.exists(private_key_file)
        public_exists = os.path.exists(public_key_file)
        
        return private_exists and public_exists
