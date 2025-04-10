import os
import sys
import time
import threading
from datetime import datetime
import logging

logger = logging.getLogger("terminal_ui")

class Colors:
    """ANSI color codes for terminal output"""
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

class TerminalUI:
    def __init__(self, username, history_size=100):
        self.username = username
        self.message_history = []
        self.max_history = history_size
        self.input_buffer = ""
        self.cursor_position = 0
        self.input_lock = threading.Lock()
        self.supports_ansi = self._check_ansi_support()
        self.terminal_width = self._get_terminal_width()
        self.unread_count = 0
    
    def _check_ansi_support(self):
        """Check if terminal supports ANSI escape codes"""
        if os.name == 'nt':
            # Enable ANSI colors on Windows 10+
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                return True
            except:
                return False
        else:
            return True
    
    def _get_terminal_width(self):
        """Get terminal width or default to 80"""
        try:
            return os.get_terminal_size().columns
        except:
            return 80
    
    def clear_screen(self):
        """Clear the terminal screen"""
        if os.name == 'nt':  # Windows
            os.system('cls')
        else:  # Unix/Linux/Mac
            os.system('clear')
    
    def print_colored(self, text, color=Colors.RESET, end="\n"):
        """Print text with color if supported"""
        if self.supports_ansi:
            print(f"{color}{text}{Colors.RESET}", end=end)
        else:
            print(text, end=end)
        sys.stdout.flush()
    
    def show_banner(self, host, port, use_tor):
        """Display welcome banner"""
        self.clear_screen()
        
        # Get terminal width for centered banner
        width = self.terminal_width
        
        # Create fancy banner with box drawing characters
        banner_text = "SECURE CHATROOM"
        padding = max(2, (width - len(banner_text) - 4) // 2)
        
        # Top border with rounded corners
        self.print_colored("╭" + "─" * (padding * 2 + len(banner_text)) + "╮", Colors.CYAN)
        
        # Title with padding
        self.print_colored("│" + " " * padding + f"{Colors.BOLD}{Colors.CYAN}{banner_text}{Colors.RESET}" + " " * padding + "│", Colors.CYAN)
        
        # Bottom border with rounded corners
        self.print_colored("╰" + "─" * (padding * 2 + len(banner_text)) + "╯", Colors.CYAN)
        
        # Connection info
        self.print_colored(f"● Connected as: {Colors.GREEN}{self.username}{Colors.RESET}", Colors.RESET)
        self.print_colored(f"● Server: {Colors.YELLOW}{host}:{port}{Colors.RESET}", Colors.RESET)
        self.print_colored(f"● TOR Enabled: {Colors.PURPLE if use_tor else Colors.GRAY}{use_tor}{Colors.RESET}", Colors.RESET)
        self.print_colored(f"● Type {Colors.YELLOW}/help{Colors.RESET} for available commands", Colors.RESET)
        
        # Separator
        self.print_colored("─" * width, Colors.GRAY)
    
    def add_message(self, text, msg_type="other"):
        """Add message to history"""
        # Create message object
        msg = {
            "id": int(time.time() * 1000),
            "text": text,
            "type": msg_type,
            "time": datetime.now().strftime("%H:%M:%S"),
            "expired": False
        }
        
        # Add to history
        self.message_history.append(msg)
        
        # Trim history if needed
        if len(self.message_history) > self.max_history:
            self.message_history = self.message_history[-self.max_history:]
        
        # Start expiration thread for non-self messages
        if msg_type != "self" and msg_type != "system":
            threading.Thread(target=self._expire_message, args=(msg["id"],), daemon=True).start()
        
        # Update display
        self.redraw_messages()
        
        return msg["id"]
    
    def _expire_message(self, msg_id):
        """Mark message as expired after timeout"""
        time.sleep(10)  # 10-second expiration
        
        # Find message and mark as expired
        for i, msg in enumerate(self.message_history):
            if msg.get("id") == msg_id:
                self.message_history[i]["expired"] = True
                break
        
        # Update display
        self.redraw_messages()
    
    def redraw_messages(self):
        """Redraw all messages in the terminal"""
        # Only in interactive mode
        if not sys.stdout.isatty():
            return
        
        with self.input_lock:
            # Save cursor position and input
            current_input = self.input_buffer
            
            # Clear screen and show messages
            self.clear_screen()
            
            # Get terminal width for centered banner
            width = self.terminal_width
            
            # Create fancy banner with box drawing characters
            banner_text = "SECURE CHATROOM"
            padding = max(2, (width - len(banner_text) - 4) // 2)
            
            # Top border with rounded corners
            self.print_colored("╭" + "─" * (padding * 2 + len(banner_text)) + "╮", Colors.CYAN)
            
            # Title with padding
            self.print_colored("│" + " " * padding + f"{Colors.BOLD}{Colors.CYAN}{banner_text}{Colors.RESET}" + " " * padding + "│", Colors.CYAN)
            
            # Bottom border with rounded corners
            self.print_colored("╰" + "─" * (padding * 2 + len(banner_text)) + "╯", Colors.CYAN)
            
            # Connection info
            self.print_colored(f"● Connected as: {Colors.GREEN}{self.username}{Colors.RESET}", Colors.RESET)
            self.print_colored("─" * width, Colors.GRAY)
            
            # Show last messages
            display_count = min(15, len(self.message_history))
            for msg in self.message_history[-display_count:]:
                if msg["expired"]:
                    self.print_colored(f"[Message Expired] {msg['text'][:20]}...", Colors.GRAY)
                else:
                    prefix = f"[{msg['time']}] "
                    if msg["type"] == "system":
                        self.print_colored(f"{prefix}{msg['text']}", Colors.YELLOW)
                    elif msg["type"] == "self":
                        # Your own messages are already formatted with "You: " in client.py
                        self.print_colored(f"{prefix}{msg['text']}", Colors.GREEN)
                    elif msg["type"] == "other":
                        # Messages from others should be in cyan
                        self.print_colored(f"{prefix}{msg['text']}", Colors.CYAN)
                    else:
                        # Fallback for any other message type
                        self.print_colored(f"{prefix}{msg['text']}", Colors.RESET)
            
            # Restore input prompt
            self.print_colored("\nYou: ", Colors.GREEN, end="")
            self.print_colored(current_input, end="")
    
    def show_help(self):
        """Display help information"""
        commands = [
            ("/help", "Show this help message"),
            ("/quit", "Disconnect and exit"),
            ("/clear", "Clear the screen"),
            ("/whoami", "Show your current username"),
            ("/log on", "Enable local encrypted logging"),
            ("/log off", "Disable local encrypted logging"),
            ("/history", "Show message history"),
            ("/users", "Show online users")
        ]
        
        self.print_colored("\n─── Available Commands ───", Colors.CYAN)
        for cmd, desc in commands:
            self.print_colored(f"{Colors.YELLOW}{cmd:<12}{Colors.RESET} - {desc}")
        self.print_colored("─" * 30, Colors.GRAY)
    
    def show_online_users(self, users):
        """Display list of online users"""
        self.print_colored("\n─── Online Users ───", Colors.CYAN)
        
        if not users:
            self.print_colored("No users currently online.", Colors.GRAY)
        else:
            self.print_colored(f"Total users online: {len(users)}", Colors.YELLOW)
            
            for i, user in enumerate(users, 1):
                username = user.get("username", "Unknown")
                join_time = user.get("join_time", 0)
                
                # Format join time
                if isinstance(join_time, (int, float)):
                    join_time_str = datetime.fromtimestamp(join_time).strftime("%H:%M:%S")
                    
                    # Calculate time online
                    time_online = time.time() - join_time
                    if time_online < 60:
                        time_str = f"{int(time_online)} seconds"
                    elif time_online < 3600:
                        time_str = f"{int(time_online / 60)} minutes"
                    else:
                        time_str = f"{int(time_online / 3600)} hours, {int((time_online % 3600) / 60)} minutes"
                else:
                    join_time_str = "Unknown"
                    time_str = "Unknown"
                
                self.print_colored(f"{i}. {Colors.GREEN}{username}{Colors.RESET}")
                self.print_colored(f"   Joined at: {join_time_str}")
                self.print_colored(f"   Online for: {time_str}")
        
        self.print_colored("─" * 30, Colors.GRAY)
    
    def get_input(self, prompt="You: "):
        """Get user input with prompt"""
        with self.input_lock:
            self.print_colored(prompt, Colors.GREEN, end="")
            user_input = input()
            return user_input
