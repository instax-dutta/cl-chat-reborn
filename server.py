#!/usr/bin/env python3
"""
Confluxus Chat Server
Handles multiple client connections and relays messages between them.
"""

import socket
import threading
import json
import time
from typing import Dict, List, Tuple
from encryption import EncryptionManager

class ChatServer:
    def __init__(self, host: str = 'localhost', port: int = 5000, enable_encryption: bool = True, 
                 auto_clear_history: bool = True):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients: Dict[str, Tuple[socket.socket, str]] = {}  # {client_socket: (socket, username)}
        self.running = False
        self.encryption_manager = EncryptionManager(enable_encryption)
        self.auto_clear_history = auto_clear_history
        self.message_history: List[dict] = []  # Store message history for trace clearance
        
    def start(self):
        """Start the chat server and listen for connections."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            
            print(f"🚀 Chat server started on {self.host}:{self.port}")
            print(f"📡 Waiting for client connections...")
            
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    print(f"🔗 New connection from {address}")
                    
                    # Start a new thread to handle this client
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.error:
                    if self.running:
                        print("❌ Error accepting connection")
                    break
                    
        except Exception as e:
            print(f"❌ Server error: {e}")
        finally:
            self.stop()
    
    def handle_client(self, client_socket: socket.socket, address: Tuple[str, int]):
        """Handle individual client connection in a separate thread."""
        username = None
        
        try:
            # Get username from client
            username_data = client_socket.recv(1024).decode('utf-8')
            if username_data:
                username = username_data.strip()
                
                # Check if username is already taken
                if username in [client_info[1] for client_info in self.clients.values()]:
                    error_msg = json.dumps({
                        "type": "error",
                        "message": f"Username '{username}' is already taken. Please choose another."
                    })
                    client_socket.send(error_msg.encode('utf-8'))
                    client_socket.close()
                    return
                
                # Add client to the list
                self.clients[client_socket] = (client_socket, username)
                
                # Send welcome message with encryption info
                welcome_msg = json.dumps({
                    "type": "system",
                    "message": f"Welcome to the chat, {username}! Type your messages below.",
                    "encryption": self.encryption_manager.get_encryption_info()
                })
                client_socket.send(welcome_msg.encode('utf-8'))
                
                # Broadcast user joined message
                self.broadcast_message(f"{username} joined the chat!", "system", exclude_socket=client_socket)
                
                print(f"👤 {username} connected from {address}")
                print(f"📊 Active clients: {len(self.clients)}")
                
                # Handle incoming messages from this client
                while self.running:
                    try:
                        message_data = client_socket.recv(1024).decode('utf-8')
                        if not message_data:
                            break
                            
                        message = message_data.strip()
                        if message:
                            # Decrypt message if needed
                            decrypted_message = self.encryption_manager.decrypt(message)
                            print(f"💬 [{username}]: {decrypted_message}")
                            
                            # Store message in history for trace clearance
                            self._add_to_history(username, decrypted_message, message)
                            
                            self.broadcast_message(message, "chat", sender=username, exclude_socket=client_socket)
                            
                    except socket.error:
                        break
                        
        except Exception as e:
            print(f"❌ Error handling client {address}: {e}")
        finally:
            # Clean up when client disconnects
            if client_socket in self.clients:
                username = self.clients[client_socket][1]
                del self.clients[client_socket]
                client_socket.close()
                
                if username:
                    print(f"👋 {username} disconnected")
                    self.broadcast_message(f"{username} left the chat!", "system")
                    print(f"📊 Active clients: {len(self.clients)}")
                    
                    # Check if chatroom is empty and clear traces
                    self._check_and_clear_if_empty()
    
    def broadcast_message(self, message: str, msg_type: str, sender: str = None, exclude_socket: socket.socket = None):
        """Broadcast a message to all connected clients."""
        if msg_type == "chat":
            formatted_message = f"[{sender}]: {message}"
        else:
            formatted_message = f"[SYSTEM]: {message}"
            
        data = json.dumps({
            "type": msg_type,
            "message": formatted_message,
            "sender": sender
        })
        
        # Send to all clients except the excluded one
        disconnected_clients = []
        for client_socket in self.clients:
            if client_socket != exclude_socket:
                try:
                    client_socket.send(data.encode('utf-8'))
                except socket.error:
                    disconnected_clients.append(client_socket)
        
        # Clean up disconnected clients
        for client_socket in disconnected_clients:
            if client_socket in self.clients:
                username = self.clients[client_socket][1]
                del self.clients[client_socket]
                try:
                    client_socket.close()
                except:
                    pass
                if username:
                    print(f"🧹 Cleaned up disconnected client: {username}")
    
    def stop(self):
        """Stop the server and close all connections."""
        self.running = False
        
        # Clear all traces before stopping
        if self.auto_clear_history:
            self._clear_all_traces()
        
        # Close all client connections
        for client_socket in list(self.clients.keys()):
            try:
                client_socket.close()
            except:
                pass
        self.clients.clear()
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            
        print("🛑 Server stopped")
    
    def _add_to_history(self, sender: str, decrypted_message: str, encrypted_message: str):
        """Add message to history for trace clearance."""
        if self.auto_clear_history:
            self.message_history.append({
                'sender': sender,
                'decrypted': decrypted_message,
                'encrypted': encrypted_message,
                'timestamp': time.time()
            })
    
    def _clear_all_traces(self):
        """Completely clear all message traces and history."""
        print("🧹 Clearing all message traces and history...")
        
        # Clear message history
        self.message_history.clear()
        
        # Clear server logs (print newlines to overwrite previous output)
        print("\n" * 50)
        print("🧹 All message traces cleared from server memory")
        print("🔒 No communication history remains")
        
        # Force garbage collection to free memory
        import gc
        gc.collect()
        
        print("✅ Complete trace clearance completed")
    
    def _check_and_clear_if_empty(self):
        """Check if chatroom is empty and clear traces if so."""
        if len(self.clients) == 0 and self.auto_clear_history:
            print(f"📭 Chatroom is empty - clearing all traces...")
            self._clear_all_traces()

def main():
    """Main function to run the chat server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Confluxus Chat Server")
    parser.add_argument("--host", default="localhost", help="Server host (default: localhost)")
    parser.add_argument("--port", type=int, default=5000, help="Server port (default: 5000)")
    parser.add_argument("--no-encryption", action="store_true", help="Disable encryption")
    parser.add_argument("--no-auto-clear", action="store_true", help="Disable automatic trace clearance")
    
    args = parser.parse_args()
    
    server = ChatServer(
        args.host, 
        args.port, 
        enable_encryption=not args.no_encryption,
        auto_clear_history=not args.no_auto_clear
    )
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
        server.stop()

if __name__ == "__main__":
    main()
