# SecureChatroom

A secure, anonymous chatroom with end-to-end encryption, featuring both terminal and GUI interfaces.

## Features

- **End-to-end encryption**: RSA for key exchange, AES-GCM for message encryption
- **Anonymous usernames**: Auto-generated codenames (e.g., ShadowPanther42)
- **Inactivity-based message expiration**: Messages expire after 5 minutes of inactivity
- **Modern GUI interface**: Clean, intuitive graphical interface with dark theme
- **Encrypted logging**: Optional secure local message logging
- **Tor integration**: Optional routing through Tor network for enhanced privacy
- **Online users tracking**: See who's currently in the chatroom
- **Command system**: Helpful commands for managing your chat experience
- **Enhanced privacy**: Server details are hidden from the UI

## Requirements

- Python 3.10+
- Dependencies:
  - pycryptodome
  - python-dotenv
  - PySocks (for Tor support)
  - tkinter (for GUI interface, included with Python standard library)

## Detailed Installation Guide

### Step 1: Clone the Repository

```bash
git clone https://github.com/Mj-Njuguna/SecureChatroom.git
cd SecureChatroom
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Generate RSA Keys

This step is crucial for the encryption system to work:

```bash
python generate_keys.py
```

This will create two files:
- `server_private.pem`: The server's private key (keep this secure)
- `server_public.pem`: The server's public key (shared with clients)

### Step 4: Configure Your Environment (Optional)

Create a `.env` file in the root directory with the following settings:

```
HOST=127.0.0.1
PORT=9999
USE_TOR=False
DEBUG=False
```

You can customize these settings:
- `HOST`: The IP address for the server (default: 127.0.0.1)
- `PORT`: The port number for the server (default: 9999)
- `USE_TOR`: Whether to route traffic through Tor (default: False)
- `DEBUG`: Enable debug logging (default: False)

## Usage Guide

### Starting the Server

First, you need to start the server before connecting any clients:

```bash
python server.py [--host HOST] [--port PORT] [--debug]
```

Options:
- `--host HOST`: Specify the server IP address (default: from .env or 127.0.0.1)
- `--port PORT`: Specify the server port (default: from .env or 9999)
- `--debug`: Enable debug logging

### Connecting with the GUI Client (Recommended)

The GUI client provides a modern, user-friendly interface:

```bash
python gui_client.py [--host HOST] [--port PORT] [--username NAME] [--use-tor] [--debug]
```

Options:
- `--host HOST`: Server IP address (default: from .env or 127.0.0.1)
- `--port PORT`: Server port (default: from .env or 9999)
- `--username NAME`: Custom username (default: auto-generated)
- `--use-tor`: Route traffic through Tor network
- `--debug`: Enable debug logging

### Connecting with the Terminal Client (Alternative)

If you prefer a terminal-based interface:

```bash
python client.py [--host HOST] [--port PORT] [--username NAME] [--use-tor] [--debug]
```

The options are the same as for the GUI client.

### Testing with Multiple Clients

To test with multiple clients on the same machine:

1. Start the server in one terminal
2. Open multiple terminals and run the GUI client in each one with different usernames:
   ```bash
   python gui_client.py --username Client1
   python gui_client.py --username Client2
   ```

## Available Commands

Both the GUI and terminal clients support these commands:

- `/help` - Show available commands
- `/quit` - Disconnect and exit
- `/clear` - Clear the chat history
- `/whoami` - Show your current username
- `/users` - Show online users
- `/log on` - Enable local encrypted logging
- `/log off` - Disable local encrypted logging
- `/history` - Show message history (if logging enabled)

## Security Features Explained

### End-to-End Encryption

- **RSA-2048 encryption** for secure key exchange
- **AES-256 GCM mode** for authenticated encryption of messages
- **Perfect Forward Secrecy** through unique session keys

### Privacy Protection

- **Inactivity-based message expiration**: Messages automatically expire after 5 minutes of inactivity
- **Anonymous usernames**: Protect real identities with auto-generated codenames
- **Hidden server details**: Server IP/port are not displayed in the client UI
- **Encrypted local logs**: Using key derivation from username
- **Tor support**: For network-level anonymity

## GUI Features

The graphical interface includes:

- **Modern dark theme**: Easy on the eyes for extended chat sessions
- **Color-coded messages**: Different colors for your messages, others' messages, and system notifications
- **Online users display**: See who's online directly in the header
- **Message formatting**: Clear visual separation between different types of messages
- **Automatic refresh**: Chat display updates automatically

## Project Structure

```
SecureChatroom/
├── src/
│   ├── crypto/        # Encryption utilities
│   ├── network/       # Client/server networking
│   ├── utils/         # Configuration and utilities
│   └── ui/            # UI components (terminal and GUI)
├── client.py          # Terminal client entry point
├── gui_client.py      # GUI client entry point
├── server.py          # Server entry point
├── generate_keys.py   # Key generation script
├── requirements.txt   # Dependencies
└── README.md          # Documentation
```

## Advanced Usage

### Using with Tor

1. Install and start the Tor service on your system
2. Enable Tor in your `.env` file: `USE_TOR=True`
3. Or use the command line flag: `python gui_client.py --use-tor`

### Custom Usernames

By default, random animal-based codenames are generated, but you can specify a custom username:

```bash
python gui_client.py --username YourSecretCodename
```

### Secure Logging

Enable secure logging to keep an encrypted record of your conversations:

1. Type `/log on` in the chat
2. View past messages with `/history`
3. Disable logging with `/log off`

## Troubleshooting

### Connection Issues

- Make sure the server is running before starting any clients
- Check that you're using the correct host and port
- Verify that your firewall isn't blocking the connection
- Try a different port if the default is in use

### RSA Key Issues

- If you get "RSA keys not found" error, run `python generate_keys.py`
- Make sure both private and public key files are in the root directory

### GUI Display Problems

- Ensure you have tkinter installed (included with standard Python installation)
- Try adjusting your system's display scaling if text appears too small or large

## License

[MIT License](LICENSE)