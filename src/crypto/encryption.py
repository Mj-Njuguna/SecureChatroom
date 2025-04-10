from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA256, HMAC
import os

class SecureMessage:
    @staticmethod
    def encrypt_aes(data, key):
        """Encrypt data with AES-GCM (more secure than EAX)"""
        if isinstance(data, str):
            data = data.encode()
        
        cipher = AES.new(key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(data)
        return (cipher.nonce, tag, ciphertext)
    
    @staticmethod
    def decrypt_aes(encrypted_data, key):
        """Decrypt AES-GCM encrypted data"""
        nonce, tag, ciphertext = encrypted_data
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        return cipher.decrypt_and_verify(ciphertext, tag)
    
    @staticmethod
    def encrypt_rsa(data, public_key):
        """Encrypt data with RSA"""
        if isinstance(data, str):
            data = data.encode()
        
        cipher = PKCS1_OAEP.new(public_key)
        return cipher.encrypt(data)
    
    @staticmethod
    def decrypt_rsa(encrypted_data, private_key):
        """Decrypt RSA encrypted data"""
        cipher = PKCS1_OAEP.new(private_key)
        return cipher.decrypt(encrypted_data)
    
    @staticmethod
    def generate_key():
        """Generate a secure AES key"""
        return get_random_bytes(32)  # 256-bit key
    
    @staticmethod
    def key_derivation(password, salt=None):
        """Derive a key from password using PBKDF2"""
        from Crypto.Protocol.KDF import PBKDF2
        
        if salt is None:
            salt = get_random_bytes(16)
        
        key = PBKDF2(password, salt, dkLen=32, count=1000000)
        return key, salt
