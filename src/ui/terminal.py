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
            if len(self.message_history) > 0:
                for msg in self.message_history[-display_count:]:
                    if msg["expired"]:
                        self.print_colored(f"  {Colors.GRAY}[Message Expired] {msg['text'][:20]}...{Colors.RESET}", Colors.GRAY)
                    else:
                        prefix = f"[{msg['time']}] "
                        
                        if msg["type"] == "system":
                            # System messages with special formatting
                            self.print_colored(f"  {Colors.YELLOW}╭─ SYSTEM ───────────────────╮{Colors.RESET}", Colors.YELLOW)
                            self.print_colored(f"  {Colors.YELLOW}│ {msg['text']}{Colors.RESET}", Colors.YELLOW)
                            self.print_colored(f"  {Colors.YELLOW}╰───────────────────────────╯{Colors.RESET}", Colors.YELLOW)
                            
                        elif msg["type"] == "self":
                            # Your own messages in a right-aligned bubble
                            text = msg['text']
                            max_len = min(self.terminal_width - 25, 50)
                            
                            if len(text) > max_len:
                                # Split long messages
                                chunks = [text[i:i+max_len] for i in range(0, len(text), max_len)]
                                
                                # First line with timestamp
                                padding = self.terminal_width - len(chunks[0]) - len(prefix) - 10
                                self.print_colored(" " * max(0, padding) + f"{Colors.GREEN}╭─ You ─{Colors.RESET}", Colors.GREEN)
                                self.print_colored(" " * max(0, padding) + f"{Colors.GREEN}│{Colors.RESET} {prefix}{chunks[0]}", Colors.GREEN)
                                
                                # Middle lines
                                for chunk in chunks[1:-1]:
                                    padding = self.terminal_width - len(chunk) - 10
                                    self.print_colored(" " * max(0, padding) + f"{Colors.GREEN}│{Colors.RESET} {chunk}", Colors.GREEN)
                                
                                # Last line
                                padding = self.terminal_width - len(chunks[-1]) - 10
                                self.print_colored(" " * max(0, padding) + f"{Colors.GREEN}│{Colors.RESET} {chunks[-1]}", Colors.GREEN)
                                self.print_colored(" " * max(0, padding) + f"{Colors.GREEN}╰───────{Colors.RESET}", Colors.GREEN)
                            else:
                                # Short message
                                padding = self.terminal_width - len(text) - len(prefix) - 10
                                self.print_colored(" " * max(0, padding) + f"{Colors.GREEN}╭─ You ─{Colors.RESET}", Colors.GREEN)
                                self.print_colored(" " * max(0, padding) + f"{Colors.GREEN}│{Colors.RESET} {prefix}{text}", Colors.GREEN)
                                self.print_colored(" " * max(0, padding) + f"{Colors.GREEN}╰───────{Colors.RESET}", Colors.GREEN)
                                
                        elif msg["type"] == "other":
                            # Messages from others in a left-aligned bubble
                            text = msg['text']
                            sender = text.split(':', 1)[0] if ': ' in text else "Other"
                            content = text.split(':', 1)[1].strip() if ': ' in text else text
                            max_len = min(self.terminal_width - 25, 50)
                            
                            if len(content) > max_len:
                                # Split long messages
                                chunks = [content[i:i+max_len] for i in range(0, len(content), max_len)]
                                
                                # First line with timestamp and sender
                                self.print_colored(f"  {Colors.CYAN}╭─ {sender} ─{Colors.RESET}", Colors.CYAN)
                                self.print_colored(f"  {Colors.CYAN}│{Colors.RESET} {prefix}{chunks[0]}", Colors.CYAN)
                                
                                # Middle lines
                                for chunk in chunks[1:-1]:
                                    self.print_colored(f"  {Colors.CYAN}│{Colors.RESET} {chunk}", Colors.CYAN)
                                
                                # Last line
                                self.print_colored(f"  {Colors.CYAN}│{Colors.RESET} {chunks[-1]}", Colors.CYAN)
                                self.print_colored(f"  {Colors.CYAN}╰───────{Colors.RESET}", Colors.CYAN)
                            else:
                                # Short message
                                self.print_colored(f"  {Colors.CYAN}╭─ {sender} ─{Colors.RESET}", Colors.CYAN)
                                self.print_colored(f"  {Colors.CYAN}│{Colors.RESET} {prefix}{content}", Colors.CYAN)
                                self.print_colored(f"  {Colors.CYAN}╰───────{Colors.RESET}", Colors.CYAN)
                        else:
                            # Fallback for any other message type
                            self.print_colored(f"  {prefix}{msg['text']}", Colors.RESET)
            else:
                # No messages yet
                self.print_colored("\n  No messages yet. Start chatting!", Colors.GRAY)
                
            # Draw input area with a box
            input_box_width = self.terminal_width - 4
            self.print_colored("\n" + "─" * self.terminal_width, Colors.GRAY)
            self.print_colored(f"{Colors.GREEN}╭─ Your Message " + "─" * (input_box_width - 15) + "╮", Colors.GREEN)
            self.print_colored(f"{Colors.GREEN}│{Colors.RESET} {current_input}" + " " * (input_box_width - len(current_input) - 1) + f"{Colors.GREEN}│", Colors.GREEN)
            self.print_colored(f"{Colors.GREEN}╰" + "─" * (input_box_width) + "╯", Colors.GREEN)
            
            # Position cursor in the input box
            sys.stdout.write(f"\033[2A\033[3C{current_input}")
            sys.stdout.flush()
    
    def show_help(self):
        """Display help information"""
        width = self.terminal_width
        
        # Header
        self.print_colored("\n" + "─" * width, Colors.GRAY)
        self.print_colored(f"{Colors.YELLOW}╭─ HELP ─" + "─" * (width - 9) + "╮{Colors.RESET}", Colors.YELLOW)
        
        # Commands section
        commands = [
            ("/help", "Show this help message"),
            ("/quit", "Disconnect and exit"),
            ("/clear", "Clear the screen"),
            ("/whoami", "Show your current username"),
            ("/log on", "Enable secure message logging"),
            ("/log off", "Disable secure message logging"),
            ("/history", "View message history (if logging enabled)"),
            ("/users", "Show online users")
        ]
        
        # Display commands in a nice format
        self.print_colored(f"{Colors.YELLOW}│{Colors.RESET} {Colors.BOLD}Available Commands:{Colors.RESET}", Colors.YELLOW)
        self.print_colored(f"{Colors.YELLOW}│{Colors.RESET}", Colors.YELLOW)
        
        for cmd, desc in commands:
            padding = width - len(cmd) - len(desc) - 10
            self.print_colored(f"{Colors.YELLOW}│{Colors.RESET}   {Colors.CYAN}{cmd}{Colors.RESET} {Colors.GRAY}·{Colors.RESET}" + " " * padding + f"{Colors.RESET}{desc}", Colors.YELLOW)
        
        # Security features section
        self.print_colored(f"{Colors.YELLOW}│{Colors.RESET}", Colors.YELLOW)
        self.print_colored(f"{Colors.YELLOW}│{Colors.RESET} {Colors.BOLD}Security Features:{Colors.RESET}", Colors.YELLOW)
        self.print_colored(f"{Colors.YELLOW}│{Colors.RESET}", Colors.YELLOW)
        
        features = [
            ("End-to-End Encryption", "All messages are encrypted with AES-GCM"),
            ("Anonymous Usernames", "Your identity is protected"),
            ("Self-Destructing Messages", "Messages expire after 10 seconds"),
            ("Secure Logging", "Optional encrypted message logging"),
            ("TOR Integration", "Optional routing through TOR network")
        ]
        
        for feature, desc in features:
            padding = width - len(feature) - len(desc) - 10
            self.print_colored(f"{Colors.YELLOW}│{Colors.RESET}   {Colors.GREEN}{feature}{Colors.RESET} {Colors.GRAY}·{Colors.RESET}" + " " * max(1, padding) + f"{Colors.RESET}{desc}", Colors.YELLOW)
        
        # Footer
        self.print_colored(f"{Colors.YELLOW}╰" + "─" * (width - 2) + "╯{Colors.RESET}", Colors.YELLOW)
        self.print_colored("─" * width, Colors.GRAY)
    
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
