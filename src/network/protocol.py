import json
import time
import uuid
import struct
from ..crypto.encryption import SecureMessage

class MessageType:
    HANDSHAKE = "handshake"
    MESSAGE = "message"
    SYSTEM = "system"
    CONTROL = "control"
    ACK = "ack"
    ONLINE_USERS = "online_users"

class Protocol:
    @staticmethod
    def create_handshake(username, aes_key, public_key):
        """Create encrypted handshake message"""
        handshake_data = {
            "type": MessageType.HANDSHAKE,
            "username": username,
            "timestamp": time.time(),
            "client_id": str(uuid.uuid4())
        }
        
        # Encrypt AES key with RSA
        encrypted_key = SecureMessage.encrypt_rsa(aes_key, public_key)
        
        # Encode handshake data
        handshake_json = json.dumps(handshake_data).encode()
        
        return {
            "data": handshake_json,
            "key": encrypted_key
        }
    
    @staticmethod
    def create_message(content, message_id=None):
        """Create a message packet"""
        if message_id is None:
            message_id = str(uuid.uuid4())
            
        return {
            "type": MessageType.MESSAGE,
            "content": content,
            "id": message_id,
            "timestamp": time.time(),
            "expires": time.time() + 10  # 10-second expiration
        }
    
    @staticmethod
    def create_system_message(content):
        """Create a system message"""
        return {
            "type": MessageType.SYSTEM,
            "content": content,
            "id": str(uuid.uuid4()),
            "timestamp": time.time()
        }
    
    @staticmethod
    def create_online_users_message(users):
        """Create a message with online users list"""
        return {
            "type": MessageType.ONLINE_USERS,
            "users": users,
            "count": len(users),
            "timestamp": time.time()
        }
    
    @staticmethod
    def encrypt_message(message, aes_key):
        """Encrypt a message for transmission"""
        message_json = json.dumps(message).encode()
        encrypted = SecureMessage.encrypt_aes(message_json, aes_key)
        return encrypted
    
    @staticmethod
    def decrypt_message(encrypted_data, aes_key):
        """Decrypt and parse a message"""
        decrypted = SecureMessage.decrypt_aes(encrypted_data, aes_key)
        return json.loads(decrypted.decode())
    
    @staticmethod
    def pack_message(nonce, tag, ciphertext):
        """Pack encrypted message components for transmission"""
        # Format: [nonce_length(2)][tag_length(2)][nonce][tag][ciphertext]
        nonce_len = len(nonce)
        tag_len = len(tag)
        
        header = struct.pack("!HH", nonce_len, tag_len)
        return header + nonce + tag + ciphertext
    
    @staticmethod
    def unpack_message(data):
        """Unpack message components from received data"""
        # Extract header
        nonce_len, tag_len = struct.unpack("!HH", data[:4])
        
        # Extract components
        nonce = data[4:4+nonce_len]
        tag = data[4+nonce_len:4+nonce_len+tag_len]
        ciphertext = data[4+nonce_len+tag_len:]
        
        return nonce, tag, ciphertext
