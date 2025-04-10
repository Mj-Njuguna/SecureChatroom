# SecureChatroom

A secure, anonymous, terminal-based chatroom using Python, RSA, and AES encryption.

## Features

- **End-to-end encryption**: RSA for key exchange, AES-GCM for message encryption
- **Anonymous usernames**: Auto-generated codenames (e.g., ShadowPanther42)
- **Self-destructing messages**: Messages expire after 10 seconds
- **Encrypted logging**: Optional secure local message logging
- **Tor integration**: Optional routing through Tor network for enhanced privacy
- **Terminal-based UI**: Clean, color-coded interface with no external dependencies
- **Online users tracking**: See who's currently in the chatroom
- **Command system**: Helpful commands for managing your chat experience

## Requirements

- Python 3.10+
- Dependencies:
  - pycryptodome
  - python-dotenv
  - PySocks (for Tor support)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/Mj-Njuguna/SecureChatroom.git
   cd SecureChatroom
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Generate RSA keys:
   ```
   python generate_keys.py
   ```

4. Configure your environment (optional):
   Create a `.env` file with the following settings:
   ```
   HOST=127.0.0.1
   PORT=9999
   USE_TOR=False
   ```

## Usage

### Starting the Server

```
python server.py [--host HOST] [--port PORT] [--debug]
```

### Connecting as a Client

```
python client.py [--host HOST] [--port PORT] [--username NAME] [--use-tor] [--debug]
```

### Available Commands

- `/help` - Show available commands
- `/quit` - Disconnect and exit
- `/clear` - Clear the screen
- `/whoami` - Show your current username
- `/log on` - Enable local encrypted logging
- `/log off` - Disable local encrypted logging
- `/history` - Show message history
- `/users` - Show online users

## Security Features

- **RSA-2048 encryption** for secure key exchange
- **AES-256 GCM mode** for authenticated encryption of messages
- **Perfect Forward Secrecy** through unique session keys
- **Self-destructing messages** for enhanced privacy
- **Encrypted local logs** using key derivation from username
- **Anonymous usernames** to protect real identities
- **Tor support** for network-level anonymity

## Project Structure

```
SecureChatroom/
├── src/
│   ├── crypto/        # Encryption utilities
│   ├── network/       # Client/server networking
│   ├── utils/         # Configuration and utilities
│   └── ui/            # Terminal UI components
├── client.py          # Client entry point
├── server.py          # Server entry point
├── generate_keys.py   # Key generation script
├── requirements.txt   # Dependencies
└── README.md          # Documentation
```

## Advanced Usage

### Using with Tor

1. Install and start the Tor service on your system
2. Enable Tor in your `.env` file: `USE_TOR=True`
3. Or use the command line flag: `python client.py --use-tor`

### Custom Usernames

By default, random animal-based codenames are generated, but you can specify a custom username:

```
python client.py --username YourSecretCodename
```

## License

[MIT License](LICENSE)