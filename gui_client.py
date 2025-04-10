#!/usr/bin/env python3
"""
SecureChatroom GUI Client
A secure, anonymous GUI chatroom client using end-to-end encryption.
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime

from src.network.client import SecureClient
from src.ui.gui import ChatroomGUI
from src.utils.config import Config
from src.utils.anonymity import AnonymityUtils
from src.ui.commands import CommandHandler
from src.utils.logging import SecureLogger
from src.crypto.key_management import KeyManager

# Global variables
gui = None
online_users = []
logger = logging.getLogger("gui_client")

def message_callback(message):
    """Callback for handling received messages"""
    global gui, online_users
    
    msg_type = message.get("type")
    
    if msg_type == "message":
        # Regular chat message
        content = message.get("content", "")
        sender = message.get("sender", "Unknown")
        
        # Check if content already has sender prefix (e.g., "Client1: Hello")
        if ": " in content and not content.startswith("["):
            # Content already has sender format, use it directly
            gui.add_message(content, "other")
        else:
            # Add sender prefix if not present
            gui.add_message(f"{sender}: {content}", "other")
        
    elif msg_type == "system":
        # System message
        gui.add_message(message.get("content", ""), "system")
        
    elif msg_type == "online_users":
        # Update online users list
        users_data = message.get("users", [])
        
        # Handle both string usernames and dictionary user objects
        if users_data and isinstance(users_data[0], dict):
            # Extract usernames from dictionary objects
            online_users = [user.get("username", "Unknown") for user in users_data]
        else:
            # Already a list of usernames
            online_users = users_data
            
        # Only show a compact notification in the chat
        if online_users:
            user_count = len(online_users)
            if user_count == 1:
                gui.add_message(f"[SYSTEM] You are the only user online", "system")
            else:
                gui.add_message(f"[SYSTEM] {user_count} users online: {', '.join(online_users)}", "system")

def handle_command(command):
    """Handle commands from the GUI"""
    global gui, client, secure_logger
    
    if command == "/help":
        gui.show_help()
    elif command == "/quit":
        gui.on_close()
    elif command == "/clear":
        gui.message_history = []
        gui.update_chat_display()
        gui.add_message("[SYSTEM] Chat cleared", "system")
    elif command == "/whoami":
        gui.add_message(f"[SYSTEM] You are connected as: {client.username}", "system")
    elif command == "/users":
        if online_users:
            gui.add_message(f"[SYSTEM] Online users: {', '.join(online_users)}", "system")
        else:
            gui.add_message("[SYSTEM] No other users online", "system")
    elif command.startswith("/log"):
        parts = command.split()
        if len(parts) > 1:
            if parts[1] == "on":
                secure_logger.enabled = True
                gui.add_message("[SYSTEM] Secure logging enabled", "system")
            elif parts[1] == "off":
                secure_logger.enabled = False
                gui.add_message("[SYSTEM] Secure logging disabled", "system")
            else:
                gui.add_message("[SYSTEM] Invalid log command. Use /log on or /log off", "system")
        else:
            gui.add_message(f"[SYSTEM] Logging is currently {'enabled' if secure_logger.enabled else 'disabled'}", "system")
    elif command == "/history":
        if secure_logger.enabled:
            history = secure_logger.read_log()
            if history:
                gui.add_message("[SYSTEM] Message History:", "system")
                for entry in history.split('\n'):
                    if entry.strip():
                        gui.add_message(entry, "other")
            else:
                gui.add_message("[SYSTEM] No message history found", "system")
        else:
            gui.add_message("[SYSTEM] Logging is disabled. Enable with /log on", "system")
    else:
        gui.add_message(f"[SYSTEM] Unknown command: {command}", "system")

def send_message(message):
    """Send a message via the client"""
    global client, gui, secure_logger
    
    try:
        success, error_msg = client.send_message(message)
        
        if success:
            # Show message in your own GUI with "You:" prefix
            # Don't add "You:" if it's already there
            if message.startswith("You: "):
                display_text = message
            else:
                display_text = f"You: {message}"
            
            gui.add_message(display_text, "self")
            
            # Log message if enabled
            if secure_logger.enabled:
                secure_logger.log_message(display_text)
                
            return True, None
        else:
            return False, error_msg
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return False, str(e)

def quit_application():
    """Clean up and quit the application"""
    global client
    if client:
        client.disconnect()
    sys.exit(0)

def main():
    global gui, client, secure_logger, online_users
    online_users = []
    
    # Load configuration
    config = Config()
    config.parse_args()
    logger = config.setup_logging()
    
    # Check for RSA keys
    if not KeyManager.check_keys_exist():
        logger.error("RSA keys not found. Run generate_keys.py first.")
        print("Error: RSA keys not found. Run generate_keys.py first.")
        return 1
    
    # Generate username if not provided
    username = config.custom_username
    if not username:
        username = AnonymityUtils.generate_username()
    
    # Initialize secure logger
    secure_logger = SecureLogger(username)
    
    # Check Tor if enabled
    if config.use_tor:
        print("[*] Checking TOR connection...")
        if not AnonymityUtils.check_tor_connection():
            print("[!] TOR is not running. Attempting to start it...")
            if not AnonymityUtils.start_tor():
                print("[x] Failed to start TOR. Continuing without it.")
                config.use_tor = False
    
    # Connect to server
    print(f"[*] Connecting to {config.host}:{config.port}...")
    client = SecureClient(config.host, config.port, username, config.use_tor)
    
    if not client.connect():
        print("[x] Failed to connect to server")
        return 1
    
    # Register message callback
    client.register_callback(message_callback)
    
    # Store online users in client for command access
    client.online_users = online_users
    
    # Initialize GUI
    gui = ChatroomGUI(username, send_message, handle_command, quit_application)
    
    # Update status
    gui.update_status(f"Connected to {config.host}:{config.port}")
    
    # Start GUI main loop
    gui.start()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
