import socket
import threading
import time
import logging
import json
import os
import signal
from ..crypto.encryption import SecureMessage
from ..crypto.key_management import KeyManager
from ..network.protocol import Protocol, MessageType

class Client:
    """Class to represent a connected client"""
    def __init__(self, conn, addr, username, aes_key):
        self.conn = conn
        self.addr = addr
        self.username = username
        self.aes_key = aes_key
        self.join_time = time.time()
        self.last_activity = time.time()
        self.client_id = None  # Set during handshake

class SecureServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.clients = []  # List of connected clients
        self.server_socket = None
        self.active = False
        self.logger = logging.getLogger("secure_server")
        
        # Load RSA keys
        self.private_key = KeyManager.load_private_key()
        if not self.private_key:
            self.logger.error("Failed to load private key. Run generate_keys.py first.")
            raise Exception("Private key not found")
    
    def start(self):
        """Start the secure server"""
        try:
            # Create server socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.active = True
            self.logger.info(f"Secure server running on {self.host}:{self.port}")
            
            # Start periodic tasks
            threading.Thread(target=self._periodic_tasks, daemon=True).start()
            
            # Main accept loop
            while self.active:
                try:
                    conn, addr = self.server_socket.accept()
                    threading.Thread(target=self._handle_client, args=(conn, addr), daemon=True).start()
                except Exception as e:
                    if self.active:  # Only log if server is still active
                        self.logger.error(f"Error accepting connection: {e}")
                        time.sleep(1)  # Avoid CPU spike on repeated errors
        
        except Exception as e:
            self.logger.error(f"Server error: {e}")
        finally:
            self.shutdown()
    
    def _handle_client(self, conn, addr):
        """Handle client connection"""
        client = None
        
        try:
            # Set timeout for handshake
            conn.settimeout(10)
            
            # Receive encrypted AES key
            encrypted_key = conn.recv(256)  # RSA-2048 encrypted data
            if not encrypted_key:
                self.logger.warning(f"Empty handshake from {addr}")
                return
            
            # Receive handshake data
            handshake_data = conn.recv(1024)
            if not handshake_data:
                self.logger.warning(f"Empty handshake data from {addr}")
                return
            
            # Decrypt AES key
            from Crypto.Cipher import PKCS1_OAEP
            cipher = PKCS1_OAEP.new(self.private_key)
            aes_key = cipher.decrypt(encrypted_key)
            
            # Parse handshake data
            handshake = json.loads(handshake_data.decode())
            username = handshake.get("username", "Unknown")
            client_id = handshake.get("client_id")
            
            # Create client object
            client = Client(conn, addr, username, aes_key)
            client.client_id = client_id
            
            # Reset timeout for normal operation
            conn.settimeout(None)
            
            # Add client to list
            self.clients.append(client)
            self.logger.info(f"Client connected: {username} from {addr}")
            
            # Notify all clients about new user
            self._broadcast_system_message(f"{username} has joined the chat")
            
            # Send online users list
            self._broadcast_online_users()
            
            # Main message handling loop
            while self.active:
                # Receive message length
                header = conn.recv(4)
                if not header or len(header) < 4:
                    break
                
                # Unpack data length
                data_length = int.from_bytes(header, byteorder='big')
                
                # Receive the actual data
                data = b''
                remaining = data_length
                while remaining > 0:
                    chunk = conn.recv(min(remaining, 4096))
                    if not chunk:
                        raise ConnectionError("Connection closed during data transfer")
                    data += chunk
                    remaining -= len(chunk)
                
                # Unpack the message components
                nonce, tag, ciphertext = Protocol.unpack_message(data)
                
                # Decrypt the message
                decrypted = Protocol.decrypt_message((nonce, tag, ciphertext), client.aes_key)
                
                # Process the message
                content = decrypted.get("content", "")
                self.logger.debug(f"Message from {username}: {content}")
                
                # Update last activity time
                client.last_activity = time.time()
                
                # Broadcast message to other clients
                self._broadcast_message(content, client)
        
        except Exception as e:
            self.logger.error(f"Error handling client {addr}: {e}")
        
        finally:
            # Clean up when client disconnects
            if conn:
                conn.close()
            
            # Remove client from list
            if client:
                self.clients = [c for c in self.clients if c.conn != conn]
                self.logger.info(f"Client disconnected: {client.username}")
                
                # Notify remaining clients
                self._broadcast_system_message(f"{client.username} has left the chat")
                
                # Update online users list
                self._broadcast_online_users()
    
    def _broadcast_message(self, content, sender):
        """Broadcast message to all clients except sender"""
        # Add debug logging
        self.logger.info(f"Broadcasting message from {sender.username}: {content}")
        
        formatted_content = f"{sender.username}: {content}"
        message_id = str(time.time())
        timestamp = time.time()
        
        # Keep track of successful deliveries
        successful_deliveries = 0
        total_recipients = len(self.clients) - 1
        
        for client in self.clients:
            if client.conn != sender.conn:
                try:
                    # Create formatted message for this client
                    client_message = {
                        "type": "message",
                        "content": formatted_content,
                        "id": message_id,
                        "timestamp": timestamp,
                        "sender": sender.username
                    }
                    
                    # Encrypt message
                    nonce, tag, ciphertext = Protocol.encrypt_message(client_message, client.aes_key)
                    
                    # Pack message for transmission
                    packed_message = Protocol.pack_message(nonce, tag, ciphertext)
                    
                    # Send message length first, then the message
                    length = len(packed_message)
                    client.conn.sendall(length.to_bytes(4, byteorder='big'))
                    client.conn.sendall(packed_message)
                    
                    successful_deliveries += 1
                    self.logger.debug(f"Message successfully sent to {client.username}")
                except Exception as e:
                    self.logger.error(f"Error broadcasting to {client.username}: {e}")
        
        # Log delivery statistics
        if total_recipients > 0:
            self.logger.info(f"Message delivery: {successful_deliveries}/{total_recipients} recipients ({successful_deliveries/total_recipients*100:.1f}%)")
        else:
            self.logger.info("No other clients to deliver message to")
    
    def _broadcast_system_message(self, content):
        """Send a system message to all clients"""
        for client in self.clients:
            try:
                # Create system message
                message = Protocol.create_system_message(f"[SYSTEM] {content}")
                
                # Encrypt message
                nonce, tag, ciphertext = Protocol.encrypt_message(message, client.aes_key)
                
                # Pack message for transmission
                packed_message = Protocol.pack_message(nonce, tag, ciphertext)
                
                # Send message length first, then the message
                length = len(packed_message)
                client.conn.sendall(length.to_bytes(4, byteorder='big'))
                client.conn.sendall(packed_message)
            except Exception as e:
                self.logger.error(f"Error sending system message to {client.username}: {e}")
    
    def _broadcast_online_users(self):
        """Send the list of online users to all clients"""
        try:
            # Create a list of online users
            online_users = []
            for client in self.clients:
                online_users.append({
                    "username": client.username,
                    "join_time": client.join_time,
                    "addr": str(client.addr[0])  # Only include IP, not port
                })
            
            # Create online users message
            message = Protocol.create_online_users_message(online_users)
            
            # Send to all clients
            for client in self.clients:
                try:
                    # Encrypt message
                    nonce, tag, ciphertext = Protocol.encrypt_message(message, client.aes_key)
                    
                    # Pack message for transmission
                    packed_message = Protocol.pack_message(nonce, tag, ciphertext)
                    
                    # Send message length first, then the message
                    length = len(packed_message)
                    client.conn.sendall(length.to_bytes(4, byteorder='big'))
                    client.conn.sendall(packed_message)
                except Exception as e:
                    self.logger.error(f"Error sending online users to {client.username}: {e}")
        except Exception as e:
            self.logger.error(f"Error broadcasting online users: {e}")
    
    def _periodic_tasks(self):
        """Perform periodic tasks"""
        while self.active:
            try:
                # Broadcast online users list every 30 seconds
                if self.clients:
                    self._broadcast_online_users()
                
                # Check for inactive clients (optional)
                # self._check_inactive_clients()
                
                # Sleep for 30 seconds
                time.sleep(30)
            except Exception as e:
                self.logger.error(f"Error in periodic tasks: {e}")
    
    def _check_inactive_clients(self, timeout=300):
        """Check for and disconnect inactive clients"""
        current_time = time.time()
        inactive_clients = []
        
        for client in self.clients:
            if current_time - client.last_activity > timeout:
                inactive_clients.append(client)
        
        for client in inactive_clients:
            try:
                self.logger.info(f"Disconnecting inactive client: {client.username}")
                client.conn.close()
            except:
                pass
            
            # Remove from clients list
            self.clients = [c for c in self.clients if c != client]
            
            # Notify remaining clients
            self._broadcast_system_message(f"{client.username} has timed out")
    
    def shutdown(self):
        """Gracefully shut down the server"""
        self.active = False
        self.logger.info("Shutting down server...")
        
        # Notify all clients
        self._broadcast_system_message("Server is shutting down")
        
        # Close all client connections
        for client in self.clients:
            try:
                client.conn.close()
            except:
                pass
        
        # Clear clients list
        self.clients = []
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        self.logger.info("Server shutdown complete")
