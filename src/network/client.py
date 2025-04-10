import socket
import threading
import time
import logging
import queue
from ..crypto.encryption import SecureMessage
from ..crypto.key_management import KeyManager
from ..network.protocol import Protocol, MessageType
import socks

class SecureClient:
    def __init__(self, host, port, username, use_tor=False):
        self.host = host
        self.port = port
        self.username = username
        self.use_tor = use_tor
        self.aes_key = None
        self.socket = None
        self.connected = False
        self.reconnect_attempts = 3
        self.reconnect_delay = 5
        self.receive_thread = None
        self.message_callbacks = []
        self.message_queue = queue.Queue()
        self.logger = logging.getLogger("secure_client")
    
    def connect(self):
        """Connect to server with retry logic"""
        try:
            # Create appropriate socket
            if self.use_tor:
                self.socket = socks.socksocket()
                self.socket.set_proxy(socks.SOCKS5, "127.0.0.1", 9050)
                self.logger.info("Using TOR for connection")
            else:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Set timeout for connection attempt
            self.socket.settimeout(10)
            
            # Connect to server
            self.socket.connect((self.host, self.port))
            
            # Generate AES key and perform handshake
            self.aes_key = SecureMessage.generate_key()
            self._perform_handshake()
            
            # Reset timeout for normal operation
            self.socket.settimeout(None)
            
            # Start receive thread
            self.connected = True
            self.receive_thread = threading.Thread(target=self._receive_loop)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            return True
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False
    
    def _perform_handshake(self):
        """Perform secure handshake with server"""
        try:
            # Load server public key
            public_key = KeyManager.load_public_key()
            if not public_key:
                raise Exception("Failed to load server public key")
            
            # Create handshake data
            handshake = Protocol.create_handshake(self.username, self.aes_key, public_key)
            
            # Send handshake data
            self.socket.sendall(handshake["key"])
            self.socket.sendall(handshake["data"])
            
            # Wait for acknowledgment (optional)
            self.logger.debug("Handshake sent")
            return True
        except Exception as e:
            self.logger.error(f"Handshake failed: {e}")
            raise
    
    def _receive_loop(self):
        """Main receive loop"""
        while self.connected:
            try:
                # Receive data length first (4 bytes)
                header = self.socket.recv(4)
                if not header or len(header) < 4:
                    raise ConnectionError("Connection closed by server")
                
                # Unpack data length
                data_length = int.from_bytes(header, byteorder='big')
                
                # Receive the actual data
                data = b''
                remaining = data_length
                while remaining > 0:
                    chunk = self.socket.recv(min(remaining, 4096))
                    if not chunk:
                        raise ConnectionError("Connection closed during data transfer")
                    data += chunk
                    remaining -= len(chunk)
                
                # Unpack the message components
                nonce, tag, ciphertext = Protocol.unpack_message(data)
                
                # Decrypt the message
                decrypted = Protocol.decrypt_message((nonce, tag, ciphertext), self.aes_key)
                
                # Process the message
                self._process_message(decrypted)
                
            except socket.timeout:
                continue
            except ConnectionError as e:
                self.logger.warning(f"Connection error: {e}")
                if self.connected:
                    self._attempt_reconnect()
                break
            except Exception as e:
                self.logger.error(f"Error in receive loop: {e}")
                if self.connected:
                    self._attempt_reconnect()
                break
    
    def _process_message(self, message):
        """Process received message based on type"""
        try:
            msg_type = message.get("type")
            self.logger.debug(f"Received message of type: {msg_type}")
            
            # Add timestamp for received messages if not present
            if "timestamp" not in message:
                message["timestamp"] = time.time()
                
            # Add message ID if not present
            if "id" not in message:
                message["id"] = str(time.time())
            
            # Put message in queue for processing
            self.message_queue.put(message)
            
            # Notify all registered callbacks
            for callback in self.message_callbacks:
                try:
                    callback(message)
                except Exception as e:
                    self.logger.error(f"Error in message callback: {e}")
                    
            # Log message receipt
            if msg_type == "message":
                sender = message.get("sender", "Unknown")
                self.logger.debug(f"Message received from {sender}")
            elif msg_type == "system":
                self.logger.debug(f"System message received: {message.get('content', '')[:30]}...")
            elif msg_type == "online_users":
                self.logger.debug(f"Online users list updated: {len(message.get('users', []))} users")
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
    
    def _attempt_reconnect(self):
        """Attempt to reconnect to server"""
        self.connected = False
        
        for attempt in range(self.reconnect_attempts):
            self.logger.info(f"Reconnecting (attempt {attempt+1}/{self.reconnect_attempts})...")
            time.sleep(self.reconnect_delay)
            
            if self.connect():
                self.logger.info("Reconnected successfully")
                return True
        
        self.logger.error("Failed to reconnect after multiple attempts")
        return False
    
    def send_message(self, content):
        """Send encrypted message to server"""
        if not self.connected:
            raise ConnectionError("Not connected to server")
            
        # Check if there are other users online
        from ..ui.terminal import Colors
        
        # Get the current online users count from the message queue
        other_users_online = False
        online_users_count = 0
        online_users = []
        
        # Check recent messages for online users updates
        for i in range(min(10, self.message_queue.qsize())):
            try:
                # Get message without removing it
                message = self.message_queue.queue[i]
                if message.get("type") == "online_users":
                    users = message.get("users", [])
                    # If we're the only user, don't allow sending
                    if len(users) > 1:
                        other_users_online = True
                        online_users_count = len(users)
                        online_users = users
                    break
            except:
                pass
                
        if not other_users_online:
            self.logger.warning("No other users online. Message not sent.")
            return False, "No other users are online to receive your message."
            
        try:
            # Create message packet
            message = Protocol.create_message(content)
            
            # Encrypt message
            nonce, tag, ciphertext = Protocol.encrypt_message(message, self.aes_key)
            
            # Pack message for transmission
            packed_message = Protocol.pack_message(nonce, tag, ciphertext)
            
            # Send message length first, then the message
            length = len(packed_message)
            self.socket.sendall(length.to_bytes(4, byteorder='big'))
            self.socket.sendall(packed_message)
            
            return True, None
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return False, str(e)
    
    def register_callback(self, callback):
        """Register callback for received messages"""
        self.message_callbacks.append(callback)
    
    def disconnect(self):
        """Gracefully disconnect from server"""
        self.connected = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            
        self.socket = None
