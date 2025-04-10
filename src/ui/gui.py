import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import logging
from datetime import datetime

logger = logging.getLogger("gui")

class Colors:
    """Color scheme for the GUI"""
    BG_DARK = "#1E1E2E"  # Dark background
    BG_LIGHT = "#2A2A3C"  # Lighter background for contrast
    TEXT = "#CDD6F4"      # Main text color
    ACCENT = "#89B4FA"    # Accent color for highlights
    SELF = "#A6E3A1"      # Color for your own messages
    OTHER = "#89DCEB"     # Color for messages from others
    SYSTEM = "#F9E2AF"    # Color for system messages
    ERROR = "#F38BA8"     # Color for errors
    BORDER = "#6C7086"    # Border color

class ChatroomGUI:
    def __init__(self, username, send_callback, command_callback, quit_callback):
        """Initialize the GUI with callbacks for interaction with the client"""
        self.username = username
        self.send_callback = send_callback
        self.command_callback = command_callback
        self.quit_callback = quit_callback
        self.message_history = []
        self.max_history = 100
        self.online_users = []
        self.refresh_timer = None
        self.last_activity_time = time.time()
        self.inactivity_timeout = 300  # 5 minutes in seconds
        self.setup_ui()
        # Start the auto-refresh timer
        self._start_refresh_timer()
        
    def setup_ui(self):
        """Set up the main UI components"""
        self.root = tk.Tk()
        self.root.title(f"SecureChatroom - {self.username}")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        self.root.configure(bg=Colors.BG_DARK)
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure("TFrame", background=Colors.BG_DARK)
        self.style.configure("TLabel", background=Colors.BG_DARK, foreground=Colors.TEXT)
        self.style.configure("TButton", background=Colors.BG_LIGHT, foreground=Colors.TEXT)
        
        # Set up the main frame with a border
        self.main_frame = ttk.Frame(self.root, padding=5)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header with connection info and a decorative border
        self.header_frame = ttk.Frame(self.main_frame)
        self.header_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.connection_label = ttk.Label(
            self.header_frame,
            text="Not connected",
            font=("Arial", 10),
            foreground=Colors.TEXT
        )
        self.connection_label.pack(side=tk.LEFT)
        
        # Add online users display in header
        self.online_users_label = ttk.Label(
            self.header_frame,
            text="No other users online",
            font=("Arial", 10),
            foreground=Colors.ACCENT
        )
        self.online_users_label.pack(side=tk.LEFT, padx=(20, 0))
        
        self.username_label = ttk.Label(
            self.header_frame,
            text=f"You: {self.username}",
            font=("Arial", 10, "bold"),
            foreground=Colors.SELF
        )
        self.username_label.pack(side=tk.RIGHT)
        
        # Add a separator below the header
        header_separator = ttk.Separator(self.main_frame, orient='horizontal')
        header_separator.pack(fill=tk.X, pady=(0, 10))
        
        # Chat display area with improved styling
        self.chat_frame = ttk.Frame(self.main_frame, padding=5)
        self.chat_frame.pack(fill=tk.BOTH, expand=True)
        
        self.chat_display = scrolledtext.ScrolledText(
            self.chat_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg=Colors.BG_DARK,
            fg=Colors.TEXT,
            insertbackground=Colors.TEXT,
            selectbackground=Colors.ACCENT,
            relief=tk.SUNKEN,
            padx=10,
            pady=10,
            borderwidth=1
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        self.chat_display.config(state=tk.DISABLED)  # Read-only
        
        # Add a separator above the input area
        input_separator = ttk.Separator(self.main_frame, orient='horizontal')
        input_separator.pack(fill=tk.X, pady=10)
        
        # Input area with improved styling
        self.input_frame = ttk.Frame(self.main_frame)
        self.input_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.message_input = tk.Text(
            self.input_frame,
            height=3,
            font=("Consolas", 10),
            bg=Colors.BG_LIGHT,
            fg=Colors.TEXT,
            insertbackground=Colors.TEXT,
            relief=tk.SUNKEN,
            padx=10,
            pady=5,
            borderwidth=1,
            wrap=tk.WORD
        )
        self.message_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.message_input.bind("<Return>", self.on_enter)
        self.message_input.bind("<Shift-Return>", lambda e: None)  # Allow Shift+Enter for newline
        
        # Send button with improved styling
        self.send_button = ttk.Button(
            self.input_frame,
            text="Send",
            command=self.send_message,
            style="Send.TButton"
        )
        self.send_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Create a custom style for the send button
        self.style.configure(
            "Send.TButton", 
            background=Colors.ACCENT,
            foreground=Colors.BG_DARK,
            font=("Arial", 10, "bold"),
            padding=5
        )
        
        # Status bar
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = ttk.Label(
            self.status_frame,
            text="Ready",
            font=("Arial", 8),
            foreground=Colors.TEXT
        )
        self.status_label.pack(side=tk.LEFT)
        
        # Set up protocol for window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Configure tags for message formatting
        self.chat_display.tag_configure("self", foreground=Colors.SELF)
        self.chat_display.tag_configure("other", foreground=Colors.OTHER)
        self.chat_display.tag_configure("system", foreground=Colors.SYSTEM)
        self.chat_display.tag_configure("error", foreground=Colors.ERROR)
        self.chat_display.tag_configure("timestamp", foreground=Colors.ACCENT)
        
        # Welcome message
        self.add_message("[SYSTEM] Welcome to SecureChatroom. Type /help for available commands.", "system")
    
    def on_enter(self, event):
        """Handle Enter key press in the input field"""
        if not event.state & 0x1:  # Check if Shift key is not pressed
            self.send_message()
            return "break"  # Prevent default behavior (newline)
        return None  # Allow default behavior for Shift+Enter
    
    def send_message(self):
        """Send the message from the input field"""
        # Update last activity time when sending a message
        self.last_activity_time = time.time()
        
        message = self.message_input.get("1.0", tk.END).strip()
        if not message:
            return
            
        # Clear input field
        self.message_input.delete("1.0", tk.END)
        
        # Handle commands
        if message.startswith('/'):
            self.command_callback(message)
        else:
            success, error = self.send_callback(message)
            if not success and error:
                self.add_message(f"[ERROR] {error}", "error")
    
    def add_message(self, text, msg_type="other"):
        """Add a message to the chat display"""
        # Update last activity time when a message is added
        self.last_activity_time = time.time()
        
        # Handle online users updates differently
        if msg_type == "system" and "users online:" in text:
            # Extract users from the message
            try:
                users_part = text.split("users online:", 1)[1].strip()
                users = [u.strip() for u in users_part.split(",")]
                self.update_online_users(users)
                return None  # Don't add this message to chat
            except:
                pass  # If parsing fails, treat as normal message
                
        # Handle "You are the only user online" message
        if msg_type == "system" and "You are the only user online" in text:
            self.update_online_users([self.username])
            return None  # Don't add this message to chat
            
        # Create message object
        timestamp = datetime.now().strftime("%H:%M:%S")
        msg = {
            "id": int(time.time() * 1000),
            "text": text,
            "type": msg_type,
            "time": timestamp,
            "expired": False
        }
        
        # Add to history
        self.message_history.append(msg)
        
        # Trim history if needed
        if len(self.message_history) > self.max_history:
            self.message_history = self.message_history[-self.max_history:]
        
        # Update display
        self.update_chat_display()
        
        return msg["id"]
        
    def update_online_users(self, users):
        """Update the online users display in the header"""
        self.online_users = users
        
        # Update the online users label
        if len(users) <= 1:
            self.online_users_label.config(text="No other users online", foreground=Colors.ERROR)
        else:
            user_count = len(users)
            # Filter out current user from the display
            other_users = [u for u in users if u != self.username]
            self.online_users_label.config(
                text=f"{user_count} users online: {', '.join(other_users)}",
                foreground=Colors.ACCENT
            )
    
    def _start_refresh_timer(self):
        """Start a timer to periodically refresh the chat display"""
        # Refresh every 5 seconds to check for expired messages
        self.refresh_timer = threading.Timer(5.0, self._refresh_callback)
        self.refresh_timer.daemon = True
        self.refresh_timer.start()
        
    def _refresh_callback(self):
        """Callback for the refresh timer"""
        # Check for inactivity
        current_time = time.time()
        time_since_last_activity = current_time - self.last_activity_time
        
        # If inactive for 5 minutes, expire all messages
        if time_since_last_activity >= self.inactivity_timeout:
            updated = False
            
            for i, msg in enumerate(self.message_history):
                # Only expire non-system messages that aren't already expired
                if not msg.get("expired", False) and msg.get("type") not in ["system", "error"]:
                    self.message_history[i]["expired"] = True
                    updated = True
            
            # Update display if needed
            if updated:
                self.update_chat_display()
                # Reset activity timer after expiring messages
                self.last_activity_time = current_time
        
        # Restart the timer (check every 30 seconds)
        self.refresh_timer = threading.Timer(30.0, self._refresh_callback)
        self.refresh_timer.daemon = True
        self.refresh_timer.start()
    
    def update_chat_display(self):
        """Update the chat display with all messages"""
        # Update last activity time when user views the chat
        self.last_activity_time = time.time()
        
        # Enable editing temporarily
        self.chat_display.config(state=tk.NORMAL)
        
        # Clear current content
        self.chat_display.delete("1.0", tk.END)
        
        # Add all messages
        for msg in self.message_history:
            timestamp = msg.get("time", "")
            text = msg.get("text", "")
            msg_type = msg.get("type", "other")
            expired = msg.get("expired", False)
            
            # Format expired messages
            if expired and msg_type == "other":
                # Only show first 15 characters of expired messages
                text_parts = text.split(": ", 1)
                if len(text_parts) > 1:
                    sender = text_parts[0]
                    content = text_parts[1]
                    # Truncate content if longer than 15 chars
                    if len(content) > 15:
                        content = content[:15] + "..."
                    text = f"{sender}: {content}"
                text = f"[Message Expired] {text}"
            
            # Insert timestamp
            self.chat_display.insert(tk.END, f"[{timestamp}] ", "timestamp")
            
            # Insert message with appropriate tag
            self.chat_display.insert(tk.END, f"{text}\n", msg_type)
        
        # Scroll to bottom
        self.chat_display.see(tk.END)
        
        # Disable editing again
        self.chat_display.config(state=tk.DISABLED)
    
    def update_status(self, text):
        """Update the status bar text"""
        self.status_label.config(text=text)
    
    def show_help(self):
        """Display help information in a dialog"""
        help_text = """Available Commands:
/help - Show this help message
/quit - Disconnect and exit
/clear - Clear the screen
/whoami - Show your current username
/log on - Enable secure message logging
/log off - Disable secure message logging
/history - View message history (if logging enabled)
/users - Show online users

Security Features:
• End-to-End Encryption - All messages are encrypted with AES-GCM
• Anonymous Usernames - Your identity is protected
• Self-Destructing Messages - Messages expire after 30 seconds
• Secure Logging - Optional encrypted message logging
• TOR Integration - Optional routing through TOR network
"""
        messagebox.showinfo("Help", help_text)
    
    def show_error(self, message):
        """Display an error message"""
        messagebox.showerror("Error", message)
    
    def show_info(self, title, message):
        """Display an information message"""
        messagebox.showinfo(title, message)
    
    def on_close(self):
        """Handle window close event"""
        # Cancel the refresh timer
        if self.refresh_timer:
            self.refresh_timer.cancel()
        
        # Call the quit callback
        if self.quit_callback:
            self.quit_callback()
        
        # Close the window
        self.root.destroy()
    
    def start(self):
        """Start the GUI main loop"""
        self.root.mainloop()
