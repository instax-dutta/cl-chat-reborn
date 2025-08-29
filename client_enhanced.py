#!/usr/bin/env python3
"""
Enhanced Multi-Client CLI Chat Client - MVP
Features: Terminal UI, Encryption, and Modern Interface
"""

import socket
import threading
import json
import sys
import time
from typing import Optional
from encryption import EncryptionManager
from terminal_ui import create_ui

class EnhancedChatClient:
    def __init__(self, host: str = 'localhost', port: int = 5000, username: str = None, 
                 enable_encryption: bool = True, use_ui: bool = True):
        self.host = host
        self.port = port
        self.username = username
        self.socket = None
        self.connected = False
        self.running = False
        self.encryption_manager = EncryptionManager(enable_encryption)
        self.ui = None
        self.use_ui = use_ui
        
    def connect(self) -> bool:
        """Connect to the chat server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            
            # Send username to server
            if self.username:
                self.socket.send(self.username.encode('utf-8'))
                
                # Wait for server response
                response = self.socket.recv(1024).decode('utf-8')
                if response:
                    try:
                        data = json.loads(response)
                        if data.get("type") == "error":
                            print(f"❌ {data['message']}")
                            self.socket.close()
                            return False
                        elif data.get("type") == "system":
                            print(f"✅ {data['message']}")
                            # Handle encryption setup
                            if data.get("encryption"):
                                self._setup_encryption(data["encryption"])
                    except json.JSONDecodeError:
                        print(f"✅ {response}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to server: {e}")
            return False
    
    def start(self):
        """Start the enhanced chat client."""
        if not self.connect():
            return
            
        self.running = True
        
        if self.use_ui:
            # Use enhanced terminal UI
            self.ui = create_ui(self.username, self.host, self.port)
            self.ui.set_input_callback(self._send_message)
            
            # Start listening thread for incoming messages
            listen_thread = threading.Thread(target=self._listen_for_messages)
            listen_thread.daemon = True
            listen_thread.start()
            
            # Start UI
            self.ui.start()
        else:
            # Use basic console interface
            print(f"🎉 Connected to chat server at {self.host}:{self.port}")
            print(f"👤 Username: {self.username}")
            print("💬 Start typing your messages (press Ctrl+C to quit):")
            print("-" * 50)
            
            # Start listening thread for incoming messages
            listen_thread = threading.Thread(target=self._listen_for_messages)
            listen_thread.daemon = True
            listen_thread.start()
            
            # Start sending thread for user input
            send_thread = threading.Thread(target=self._send_messages)
            send_thread.daemon = True
            send_thread.start()
            
            try:
                # Keep main thread alive
                while self.running and self.connected:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                print("\n🛑 Disconnecting...")
            finally:
                self.stop()
    
    def _setup_encryption(self, encryption_info: dict):
        """Setup encryption with server."""
        if encryption_info.get("encrypted") and self.encryption_manager.enable_encryption:
            salt = encryption_info.get("salt")
            if salt:
                self.encryption_manager.set_shared_key(salt)
                print("🔒 Encryption enabled")
    
    def _send_message(self, message: str):
        """Send message via UI callback."""
        if message and self.connected:
            try:
                # Encrypt message if encryption is enabled
                encrypted_message = self.encryption_manager.encrypt(message)
                self.socket.send(encrypted_message.encode('utf-8'))
            except socket.error:
                print("❌ Failed to send message")
                self.connected = False
    
    def _listen_for_messages(self):
        """Listen for incoming messages from the server."""
        while self.running and self.connected:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if not data:
                    break
                    
                try:
                    message_data = json.loads(data)
                    message_type = message_data.get("type", "chat")
                    message = message_data.get("message", "")
                    
                    # Decrypt message if needed
                    decrypted_message = self.encryption_manager.decrypt(message)
                    
                    if self.ui:
                        # Use UI for message display
                        if message_type == "system":
                            self.ui.add_system_message(decrypted_message)
                        elif message_type == "chat":
                            sender = message_data.get("sender", "Unknown")
                            self.ui.add_chat_message(sender, decrypted_message)
                    else:
                        # Use basic console output
                        if message_type == "system":
                            print(f"\n🔔 {decrypted_message}")
                        elif message_type == "chat":
                            print(f"\n{decrypted_message}")
                        
                        # Prompt for next input
                        print(f"\n[{self.username}]: ", end="", flush=True)
                        
                except json.JSONDecodeError:
                    # Handle plain text messages (fallback)
                    print(f"\n{data}")
                    print(f"\n[{self.username}]: ", end="", flush=True)
                    
            except socket.error:
                if self.running:
                    print("\n❌ Lost connection to server")
                break
            except Exception as e:
                if self.running:
                    print(f"\n❌ Error receiving message: {e}")
                break
        
        self.connected = False
    
    def _send_messages(self):
        """Handle sending messages from user input (basic mode)."""
        while self.running and self.connected:
            try:
                # Get user input
                message = input(f"[{self.username}]: ").strip()
                
                if not self.connected:
                    break
                    
                if message.lower() in ['/quit', '/exit', '/q']:
                    print("👋 Goodbye!")
                    break
                    
                if message:
                    try:
                        # Encrypt message if encryption is enabled
                        encrypted_message = self.encryption_manager.encrypt(message)
                        self.socket.send(encrypted_message.encode('utf-8'))
                    except socket.error:
                        print("❌ Failed to send message")
                        break
                        
            except EOFError:
                break
            except KeyboardInterrupt:
                break
            except Exception as e:
                if self.running:
                    print(f"❌ Error sending message: {e}")
                break
        
        self.connected = False
    
    def stop(self):
        """Stop the client and close connection."""
        self.running = False
        self.connected = False
        
        if self.ui:
            self.ui.stop()
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        print("🛑 Enhanced client stopped")

def get_username() -> str:
    """Get username from user input."""
    while True:
        username = input("Enter your username: ").strip()
        if username:
            return username
        print("❌ Username cannot be empty. Please try again.")

def main():
    """Main function to run the enhanced chat client."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Multi-Client CLI Chat Client")
    parser.add_argument("--host", default="localhost", help="Server host (default: localhost)")
    parser.add_argument("--port", type=int, default=5000, help="Server port (default: 5000)")
    parser.add_argument("--username", help="Your username")
    parser.add_argument("--no-encryption", action="store_true", help="Disable encryption")
    parser.add_argument("--no-ui", action="store_true", help="Use basic console interface")
    
    args = parser.parse_args()
    
    # Get username if not provided
    username = args.username
    if not username:
        username = get_username()
    
    client = EnhancedChatClient(
        args.host, 
        args.port, 
        username,
        enable_encryption=not args.no_encryption,
        use_ui=not args.no_ui
    )
    
    try:
        client.start()
    except KeyboardInterrupt:
        print("\n🛑 Client interrupted")
    except Exception as e:
        print(f"❌ Client error: {e}")

if __name__ == "__main__":
    main()
