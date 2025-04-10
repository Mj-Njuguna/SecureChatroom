#!/usr/bin/env python3
"""
SecureChatroom Client
A secure, anonymous, terminal-based chatroom client using end-to-end encryption.
"""

import sys
import os
import logging
import threading
import time
import json

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.config import Config
from src.utils.anonymity import AnonymityUtils
from src.network.client import SecureClient
from src.ui.terminal import TerminalUI, Colors
from src.ui.commands import CommandHandler
from src.utils.logging import SecureLogger
from src.crypto.key_management import KeyManager

def message_callback(message):
    """Callback for handling received messages"""
    global ui, online_users
    
    msg_type = message.get("type")
    
    if msg_type == "message":
        # Regular chat message
        content = message.get("content", "")
        sender = message.get("sender", "Unknown")
        
        # Display the message with timestamp if available
        if "timestamp" in message:
            timestamp = time.strftime("%H:%M:%S", time.localtime(message.get("timestamp")))
            ui.add_message(f"[{timestamp}] {content}")
        else:
            ui.add_message(content)
            
        # Flash the terminal or make a sound for notification
        print("\a", end="", flush=True)  # Terminal bell
        
    elif msg_type == "system":
        # System message
        ui.add_message(message.get("content", ""), "system")
        
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
                ui.add_message(f"[SYSTEM] You are the only user online", "system")
            else:
                ui.add_message(f"[SYSTEM] {user_count} users online: {', '.join(online_users)}", "system")

def main():
    global ui, online_users
    online_users = []
    
    # Load configuration
    config = Config()
    config.parse_args()
    logger = config.setup_logging()
    
    # Check if keys exist
    if not KeyManager.check_keys_exist():
        logger.error("RSA keys not found. Run generate_keys.py first.")
        print("Error: RSA keys not found. Run generate_keys.py first.")
        return 1
    
    # Generate username if not provided
    username = config.custom_username
    if not username:
        username = AnonymityUtils.generate_username()
    
    # Initialize UI
    ui = TerminalUI(username)
    
    # Initialize secure logger
    secure_logger = SecureLogger(username)
    
    # Check Tor if enabled
    if config.use_tor:
        ui.print_colored("[*] Checking TOR connection...", Colors.YELLOW)
        if not AnonymityUtils.check_tor_connection():
            ui.print_colored("[!] TOR is not running. Attempting to start it...", Colors.YELLOW)
            if not AnonymityUtils.start_tor():
                ui.print_colored("[x] Failed to start TOR. Continuing without it.", Colors.RED)
                config.use_tor = False
    
    # Show welcome banner
    ui.show_banner(config.host, config.port, config.use_tor)
    
    # Connect to server
    ui.print_colored(f"[*] Connecting to {config.host}:{config.port}...", Colors.YELLOW)
    client = SecureClient(config.host, config.port, username, config.use_tor)
    
    if not client.connect():
        ui.print_colored("[x] Failed to connect to server", Colors.RED)
        return 1
    
    # Register message callback
    client.register_callback(message_callback)
    
    # Store online users in client for command access
    client.online_users = online_users
    
    # Initialize command handler
    cmd_handler = CommandHandler(client, ui, secure_logger)
    
    ui.print_colored(f"[✓] Connected as: {Colors.GREEN}{username}{Colors.RESET}", Colors.GREEN)
    
    # Main input loop
    while True:
        try:
            user_input = ui.get_input()
            
            # Skip empty messages
            if not user_input.strip():
                continue
            
            # Handle commands
            if user_input.startswith('/'):
                if cmd_handler.handle_command(user_input):
                    continue
            
            # Send regular message
            ui.add_message(user_input, "self")
            client.send_message(user_input)
            
            # Log message if enabled
            if secure_logger.enabled:
                secure_logger.log_message(f"You: {user_input}")
                
        except KeyboardInterrupt:
            ui.print_colored("\n[x] Interrupted by user", Colors.RED)
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            ui.print_colored(f"\n[!] Error: {e}", Colors.RED)
            time.sleep(1)
    
    # Clean up
    if client:
        client.disconnect()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
