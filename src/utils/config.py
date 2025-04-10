import os
from dotenv import load_dotenv
import argparse
import logging

class Config:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Default values
        self.host = "127.0.0.1"
        self.port = 9999
        self.use_tor = False
        self.debug = False
        self.log_level = "INFO"
        self.custom_username = None
        
        # Load from environment
        self._load_from_env()
        
    def _load_from_env(self):
        """Load configuration from environment variables"""
        if os.getenv("HOST"):
            self.host = os.getenv("HOST")
            
        if os.getenv("PORT"):
            try:
                self.port = int(os.getenv("PORT"))
            except ValueError:
                pass
                
        if os.getenv("USE_TOR", "").lower() in ("true", "1", "yes"):
            self.use_tor = True
            
        if os.getenv("DEBUG", "").lower() in ("true", "1", "yes"):
            self.debug = True
            self.log_level = "DEBUG"
    
    def parse_args(self, args=None):
        """Parse command line arguments"""
        parser = argparse.ArgumentParser(description="Secure Chatroom")
        parser.add_argument("--host", type=str, help="Server host address")
        parser.add_argument("--port", type=int, help="Server port")
        parser.add_argument("--username", type=str, help="Custom username")
        parser.add_argument("--use-tor", action="store_true", help="Use TOR for connection")
        parser.add_argument("--debug", action="store_true", help="Enable debug mode")
        
        parsed_args = parser.parse_args(args)
        
        # Override config with command line args
        if parsed_args.host:
            self.host = parsed_args.host
            
        if parsed_args.port:
            self.port = parsed_args.port
            
        if parsed_args.username:
            self.custom_username = parsed_args.username
            
        if parsed_args.use_tor:
            self.use_tor = True
            
        if parsed_args.debug:
            self.debug = True
            self.log_level = "DEBUG"
        
        return self
    
    def setup_logging(self):
        """Configure logging based on settings"""
        log_level = getattr(logging, self.log_level)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("secure_chatroom.log"),
                logging.StreamHandler()
            ]
        )
        
        # Reduce verbosity of some modules
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        
        return logging.getLogger("secure_chatroom")
