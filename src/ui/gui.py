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

class ChatroomGUI:
    def __init__(self, username, send_callback, command_callback, quit_callback):
        """Initialize the GUI with callbacks for interaction with the client"""
        self.username = username
        self.send_callback = send_callback
        self.command_callback = command_callback
        self.quit_callback = quit_callback
        self.message_history = []
        self.max_history = 100
        self.setup_ui()
        
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
        
        # Set up the main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header with connection info
        self.header_frame = ttk.Frame(self.main_frame)
        self.header_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.title_label = ttk.Label(
            self.header_frame, 
            text="SECURE CHATROOM", 
            font=("Arial", 16, "bold"),
            foreground=Colors.ACCENT
        )
        self.title_label.pack(side=tk.LEFT)
        
        self.username_label = ttk.Label(
            self.header_frame,
            text=f"Connected as: {self.username}",
            font=("Arial", 10),
            foreground=Colors.SELF
        )
        self.username_label.pack(side=tk.RIGHT)
        
        # Chat display area
        self.chat_frame = ttk.Frame(self.main_frame)
        self.chat_frame.pack(fill=tk.BOTH, expand=True)
        
        self.chat_display = scrolledtext.ScrolledText(
            self.chat_frame,
            wrap=tk.WORD,
            bg=Colors.BG_LIGHT,
            fg=Colors.TEXT,
            font=("Consolas", 10),
            padx=10,
            pady=10
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        self.chat_display.config(state=tk.DISABLED)
        
        # Input area
        self.input_frame = ttk.Frame(self.main_frame)
        self.input_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.message_input = tk.Text(
            self.input_frame,
            height=3,
            bg=Colors.BG_LIGHT,
            fg=Colors.TEXT,
            font=("Consolas", 10),
            padx=10,
            pady=10,
            wrap=tk.WORD
        )
        self.message_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.message_input.bind("<Return>", self.on_enter)
        self.message_input.bind("<Shift-Return>", lambda e: None)  # Allow Shift+Enter for newline
        
        self.send_button = ttk.Button(
            self.input_frame,
            text="Send",
            command=self.send_message
        )
        self.send_button.pack(side=tk.RIGHT, padx=(10, 0))
        
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
        
        # Start expiration thread for non-self messages
        if msg_type != "self" and msg_type != "system" and msg_type != "error":
            threading.Thread(target=self._expire_message, args=(msg["id"],), daemon=True).start()
        
        # Update display
        self.update_chat_display()
        
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
        self.update_chat_display()
    
    def update_chat_display(self):
        """Update the chat display with all messages"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("1.0", tk.END)
        
        for msg in self.message_history:
            if msg["expired"]:
                self.chat_display.insert(tk.END, f"[Message Expired] {msg['text'][:20]}...\n", "error")
            else:
                timestamp = f"[{msg['time']}] "
                self.chat_display.insert(tk.END, timestamp, "timestamp")
                
                if msg["type"] == "system":
                    self.chat_display.insert(tk.END, f"{msg['text']}\n", "system")
                elif msg["type"] == "self":
                    self.chat_display.insert(tk.END, f"{msg['text']}\n", "self")
                elif msg["type"] == "error":
                    self.chat_display.insert(tk.END, f"{msg['text']}\n", "error")
                else:
                    self.chat_display.insert(tk.END, f"{msg['text']}\n", "other")
        
        # Scroll to the bottom
        self.chat_display.see(tk.END)
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
• Self-Destructing Messages - Messages expire after 10 seconds
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
        if messagebox.askokcancel("Quit", "Do you want to quit the SecureChatroom?"):
            self.quit_callback()
            self.root.destroy()
    
    def start(self):
        """Start the GUI main loop"""
        self.root.mainloop()
