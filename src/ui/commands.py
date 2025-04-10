import logging
import sys
import os
from datetime import datetime
from ..ui.terminal import Colors

logger = logging.getLogger("commands")

class CommandHandler:
    def __init__(self, client, terminal_ui, secure_logger=None):
        self.client = client
        self.ui = terminal_ui
        self.secure_logger = secure_logger
        self.commands = {
            "/help": self.cmd_help,
            "/quit": self.cmd_quit,
            "/clear": self.cmd_clear,
            "/whoami": self.cmd_whoami,
            "/log": self.cmd_log,
            "/history": self.cmd_history,
            "/users": self.cmd_users
        }
    
    def handle_command(self, command):
        """Process a command and return True if it was a command, False otherwise"""
        if not command.startswith('/'):
            return False
            
        # Split command and arguments
        parts = command.split(' ', 1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        # Find and execute command
        if cmd in self.commands:
            self.commands[cmd](args)
            return True
        elif cmd.startswith('/log'):
            # Special case for /log on and /log off
            if command.lower() == "/log on":
                self.cmd_log("on")
                return True
            elif command.lower() == "/log off":
                self.cmd_log("off")
                return True
        
        # Unknown command
        self.ui.print_colored(f"Unknown command: {cmd}. Type /help for available commands.", Colors.RED)
        return True
    
    def cmd_help(self, args):
        """Show help information"""
        self.ui.show_help()
    
    def cmd_quit(self, args):
        """Disconnect and exit"""
        self.ui.print_colored("[x] Disconnecting...", Colors.RED)
        if self.client:
            self.client.disconnect()
        sys.exit(0)
    
    def cmd_clear(self, args):
        """Clear the screen"""
        self.ui.clear_screen()
        self.ui.redraw_messages()
    
    def cmd_whoami(self, args):
        """Show current username"""
        if self.client:
            self.ui.print_colored(f"You're {Colors.GREEN}{self.client.username}{Colors.RESET}", 
                                 Colors.YELLOW)
    
    def cmd_log(self, args):
        """Enable or disable secure logging"""
        if not self.secure_logger:
            self.ui.print_colored("[x] Secure logging not available", Colors.RED)
            return
            
        if args.lower() == "on":
            self.secure_logger.enable()
            self.ui.print_colored("[✓] Logging enabled", Colors.GREEN)
        elif args.lower() == "off":
            self.secure_logger.disable()
            self.ui.print_colored("[x] Logging disabled", Colors.RED)
        else:
            self.ui.print_colored("Usage: /log on|off", Colors.YELLOW)
    
    def cmd_history(self, args):
        """Show message history"""
        self.ui.clear_screen()
        self.ui.print_colored("─── Message History ───", Colors.CYAN)
        
        for i, msg in enumerate(self.ui.message_history):
            prefix = f"[{msg['time']}] "
            if msg["type"] == "system":
                self.ui.print_colored(f"{prefix}{msg['text']}", Colors.YELLOW)
            elif msg["type"] == "self":
                self.ui.print_colored(f"{prefix}You: {msg['text']}", Colors.GREEN)
            else:
                self.ui.print_colored(f"{prefix}{msg['text']}", Colors.RESET)
                
        self.ui.print_colored("─" * 30, Colors.GRAY)
        input("Press Enter to continue...")
        self.ui.redraw_messages()
    
    def cmd_users(self, args):
        """Show online users"""
        # This requires the client to have the latest user list
        if hasattr(self.client, 'online_users'):
            self.ui.show_online_users(self.client.online_users)
        else:
            self.ui.print_colored("[!] Online users information not available", Colors.YELLOW)
