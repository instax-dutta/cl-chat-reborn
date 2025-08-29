# Multi-Client CLI Chat - MVP 🚀

A **minimal viable product** for a multi-client command-line chat service built with Python sockets. Multiple users can connect and exchange real-time text messages through a simple CLI interface.

## 🎯 Features (MVP Scope)

✅ **Real-time messaging** - Instant message delivery between clients  
✅ **Multiple concurrent clients** - Support for unlimited simultaneous connections  
✅ **Username identification** - Each client has a unique username  
✅ **Broadcast messaging** - Messages sent to all connected clients  
✅ **System notifications** - Join/leave notifications and server messages  
✅ **Graceful disconnection** - Clean handling of client disconnections  
✅ **Cross-platform** - Works on Windows, macOS, and Linux  
✅ **End-to-end encryption** - Secure message transmission using AES encryption  
✅ **Modern terminal UI** - Colored interface with timestamps and formatting  
✅ **Enhanced commands** - Built-in help, clear, and user management commands  

## 🚫 Not Included (Future Iterations)

- Authentication/login system
- Persistent message history
- Private chats or direct messaging
- File transfer capabilities
- GUI or fancy terminal formatting
- Message encryption

## 🛠 Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client A  │    │   Client B  │    │   Client C  │
│  (Alice)    │    │   (Bob)     │    │   (Charlie) │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │
                   ┌──────▼──────┐
                   │   Server    │
                   │ (localhost: │
                   │    5000)    │
                   └─────────────┘
```

## 📋 Requirements

- **Python 3.6+** (for type hints support)
- **cryptography>=3.4.8** - For encryption features
- **colorama>=0.4.6** - For colored terminal output (optional)
- **Network access** - For client-server communication

## 🚀 Quick Start

### 1. Start the Server

Open a terminal and run:

```bash
python server.py
```

You should see:
```
🚀 Chat server started on localhost:5000
📡 Waiting for client connections...
```

### 2. Connect Clients

Open **multiple terminal windows** and run:

**Terminal 1 (Enhanced UI):**
```bash
python3 client_enhanced.py --username Alice
```

**Terminal 2 (Enhanced UI):**
```bash
python3 client_enhanced.py --username Bob
```

**Terminal 3 (Basic UI):**
```bash
python3 client.py --username Charlie
```

### 3. Start Chatting!

Once connected, you'll see the enhanced terminal UI:
```
==================================================
🚀 Multi-Client CLI Chat - MVP
==================================================
👤 Username: Alice
🌐 Server: localhost:5000
🔒 Status: Connected
==================================================
💬 Type your messages below (press Ctrl+C to quit)
📋 Commands: /help, /clear, /users, /quit
==================================================

[Alice]: 
```

Type your messages and press Enter to send them!

## 📖 Usage Examples

### Server Options

```bash
# Start server on default port (5000)
python server.py

# Start server on custom host and port
python server.py --host 0.0.0.0 --port 8080

# Start server on specific IP
python server.py --host 192.168.1.100 --port 5000
```

### Client Options

```bash
# Enhanced client with UI and encryption (recommended)
python3 client_enhanced.py --username Alice

# Basic client with encryption
python3 client.py --username Bob

# Enhanced client without encryption
python3 client_enhanced.py --username Charlie --no-encryption

# Enhanced client with basic console interface
python3 client_enhanced.py --username David --no-ui

# Connect to custom server
python3 client_enhanced.py --host 192.168.1.100 --port 8080 --username Eve
```

### Client Commands

- **Type any message** - Sends to all connected clients
- **`/help`** - Show available commands
- **`/clear`** - Clear chat history (UI mode only)
- **`/users`** - Show connected users (coming soon)
- **`/quit`** or **`/exit`** or **`/q`** - Disconnect from server
- **`Ctrl+C`** - Force disconnect

## 🔧 Advanced Configuration

### Custom Server Settings

Edit `server.py` to change default settings:

```python
class ChatServer:
    def __init__(self, host: str = '0.0.0.0', port: int = 8080):  # Changed defaults
```

### Network Configuration

For **local network** access:
```bash
# Server (on machine A)
python server.py --host 0.0.0.0 --port 5000

# Client (on machine B)
python client.py --host 192.168.1.100 --port 5000 --username Bob
```

For **internet access**, you'll need to:
1. Configure your router's port forwarding
2. Use your public IP address
3. Consider security implications

## 🧪 Testing the MVP

### Test Scenario 1: Basic Messaging

1. Start server: `python server.py`
2. Connect Alice: `python client.py --username Alice`
3. Connect Bob: `python client.py --username Bob`
4. Alice types: `Hello everyone!`
5. Bob should see: `[Alice]: Hello everyone!`

### Test Scenario 2: Multiple Clients

1. Start server
2. Connect 3+ clients with different usernames
3. Send messages from each client
4. Verify all clients receive all messages

### Test Scenario 3: Disconnection Handling

1. Start server and connect multiple clients
2. Force-close one client (Ctrl+C)
3. Verify other clients see disconnect notification
4. Verify server cleans up properly

## 🐛 Troubleshooting

### Common Issues

**"Address already in use"**
```bash
# Kill existing process on port 5000
lsof -ti:5000 | xargs kill -9
# Or use different port
python server.py --port 5001
```

**"Connection refused"**
- Ensure server is running
- Check host/port settings
- Verify firewall settings

**"Username already taken"**
- Choose a different username
- Wait for previous client to disconnect

### Debug Mode

Add debug prints to see detailed communication:

```python
# In server.py, add:
print(f"DEBUG: Received from {username}: {message}")

# In client.py, add:
print(f"DEBUG: Sending: {message}")
```

## 🔮 Future Enhancements

### Phase 2 Features
- [ ] Private messaging (`/msg username message`)
- [ ] User list command (`/users`)
- [ ] Message timestamps
- [ ] Typing indicators

### Phase 3 Features
- [ ] Message persistence (SQLite/JSON)
- [ ] User authentication
- [ ] Chat rooms/channels
- [ ] File sharing

### Phase 4 Features
- [ ] Web interface
- [ ] Mobile app
- [ ] End-to-end encryption
- [ ] Voice/video calls

## 📝 Code Structure

```
cl-chat-reborn/
├── server.py              # Main server implementation
├── client.py              # Basic client implementation
├── client_enhanced.py     # Enhanced client with UI and encryption
├── encryption.py          # Encryption module
├── terminal_ui.py         # Terminal UI module
├── test_chat.py           # Testing utility
├── requirements.txt       # Dependencies
└── README.md             # This file
```

### Key Classes

- **`ChatServer`** - Handles multiple client connections
- **`ChatClient`** - Basic client implementation
- **`EnhancedChatClient`** - Enhanced client with UI and encryption
- **`ChatEncryption`** - Handles message encryption/decryption
- **`TerminalUI`** - Modern terminal interface

### Key Methods

- **Server**: `start()`, `handle_client()`, `broadcast_message()`
- **Client**: `connect()`, `listen_for_messages()`, `send_messages()`
- **Enhanced Client**: `start()`, `_send_message()`, `_listen_for_messages()`
- **Encryption**: `encrypt_message()`, `decrypt_message()`, `set_shared_key()`
- **UI**: `start()`, `add_message()`, `_handle_command()`

## 🤝 Contributing

This is an MVP - feel free to:
1. Report bugs
2. Suggest features
3. Submit pull requests
4. Fork and extend

## 📄 License

MIT License - feel free to use for learning, personal projects, or commercial use.

---

**Happy Chatting! 🎉**

*Built with ❤️ using Python sockets*
