import logging
import os
from datetime import datetime
from Crypto.Hash import SHA256
from Crypto.Cipher import AES

class SecureLogger:
    def __init__(self, username, log_file="chatlog.enc"):
        self.username = username
        self.log_file = log_file
        self.enabled = False
        
        # Setup application logging
        self.logger = logging.getLogger("secure_logger")
        
    def enable(self):
        """Enable secure logging"""
        self.enabled = True
        self.logger.info("Secure logging enabled")
        
    def disable(self):
        """Disable secure logging"""
        self.enabled = False
        self.logger.info("Secure logging disabled")
        
    def log_message(self, message):
        """Securely log a message to encrypted file"""
        if not self.enabled:
            return
            
        try:
            # Create a unique key based on username
            key = SHA256.new(self.username.encode()).digest()[:32]
            
            # Get current timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Format log entry
            log_entry = f"[{timestamp}] {message}"
            
            # Encrypt the log entry
            cipher = AES.new(key, AES.MODE_GCM)
            ciphertext, tag = cipher.encrypt_and_digest(log_entry.encode())
            
            # Write to file
            with open(self.log_file, "ab") as f:
                # Format: [nonce_length(1)][tag_length(1)][nonce][tag][ciphertext]
                f.write(bytes([len(cipher.nonce)]))
                f.write(bytes([len(tag)]))
                f.write(cipher.nonce)
                f.write(tag)
                f.write(ciphertext)
                
            self.logger.debug(f"Message logged securely")
            return True
        except Exception as e:
            self.logger.error(f"Error logging message: {e}")
            return False
    
    def read_logs(self, password=None):
        """Read and decrypt logs (if password provided)"""
        if not os.path.exists(self.log_file):
            return []
            
        logs = []
        
        try:
            with open(self.log_file, "rb") as f:
                data = f.read()
                
            # Create key from username
            key = SHA256.new(self.username.encode()).digest()[:32]
            
            # Parse and decrypt log entries
            pos = 0
            while pos < len(data):
                # Read header
                nonce_len = data[pos]
                tag_len = data[pos+1]
                pos += 2
                
                # Read components
                nonce = data[pos:pos+nonce_len]
                pos += nonce_len
                tag = data[pos:pos+tag_len]
                pos += tag_len
                
                # Find end of this entry (next header or EOF)
                next_header = data.find(bytes([nonce_len]), pos)
                if next_header == -1:
                    ciphertext = data[pos:]
                else:
                    ciphertext = data[pos:next_header]
                pos += len(ciphertext)
                
                # Decrypt entry
                cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
                try:
                    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
                    logs.append(plaintext.decode())
                except Exception as e:
                    self.logger.error(f"Failed to decrypt log entry: {e}")
                    
            return logs
        except Exception as e:
            self.logger.error(f"Error reading logs: {e}")
            return []
