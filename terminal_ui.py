#!/usr/bin/env python3
"""
Terminal UI module for Confluxus
Provides a modern, terminal-like chat interface with colors and formatting.
"""

import os
import sys
import time
import threading
from datetime import datetime
from typing import List, Optional, Callable
import queue

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    # Fallback if colorama is not available
    class Fore:
        GREEN = ""
        BLUE = ""
        YELLOW = ""
        RED = ""
        CYAN = ""
        MAGENTA = ""
        WHITE = ""
        RESET = ""
    
    class Back:
        BLACK = ""
        BLUE = ""
        GREEN = ""
        RESET = ""
    
    class Style:
        BRIGHT = ""
        DIM = ""
        RESET_ALL = ""
    
    COLORS_AVAILABLE = False

class ChatMessage:
    """Represents a chat message with metadata."""
    
    def __init__(self, sender: str, content: str, msg_type: str = "chat", timestamp: datetime = None):
        self.sender = sender
        self.content = content
        self.msg_type = msg_type
        self.timestamp = timestamp or datetime.now()
    
    def __str__(self):
        time_str = self.timestamp.strftime("%H:%M:%S")
        if self.msg_type == "system":
            return f"{Fore.CYAN}[{time_str}] {Fore.YELLOW}[SYSTEM] {self.content}{Style.RESET_ALL}"
        elif self.msg_type == "error":
            return f"{Fore.CYAN}[{time_str}] {Fore.RED}[ERROR] {self.content}{Style.RESET_ALL}"
        else:
            return f"{Fore.CYAN}[{time_str}] {Fore.GREEN}[{self.sender}] {Fore.WHITE}{self.content}{Style.RESET_ALL}"

class TerminalUI:
    """Modern terminal-like chat interface."""
    
    def __init__(self, username: str, host: str, port: int):
        self.username = username
        self.host = host
        self.port = port
        self.messages: List[ChatMessage] = []
        self.connected = False
        self.running = False
        self.message_queue = queue.Queue()
        self.input_callback: Optional[Callable] = None
        
        # UI state
        self.terminal_width = self._get_terminal_width()
        self.scroll_offset = 0
        self.max_messages_display = 20
        
        # Colors and styling
        self.colors = COLORS_AVAILABLE
        
    def _get_terminal_width(self) -> int:
        """Get terminal width, fallback to 80 if not available."""
        try:
            return os.get_terminal_size().columns
        except:
            return 80
    
    def start(self):
        """Start the terminal UI."""
        self.running = True
        self.connected = True
        
        # Clear screen and show welcome
        self._clear_screen()
        self._show_welcome()
        
        # Start message display thread
        display_thread = threading.Thread(target=self._message_display_loop)
        display_thread.daemon = True
        display_thread.start()
        
        # Start input handling
        self._input_loop()
    
    def _clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def _show_welcome(self):
        """Display welcome message and connection info."""
        print(f"{Fore.CYAN}{'=' * self.terminal_width}")
        print(f"{Fore.GREEN}🚀 Confluxus")
        print(f"{Fore.CYAN}{'=' * self.terminal_width}")
        print(f"{Fore.WHITE}👤 Username: {Fore.YELLOW}{self.username}")
        print(f"{Fore.WHITE}🌐 Server: {Fore.YELLOW}{self.host}:{self.port}")
        print(f"{Fore.WHITE}🔒 Status: {Fore.GREEN}Connected")
        print(f"{Fore.CYAN}{'=' * self.terminal_width}")
        print(f"{Fore.WHITE}💬 Type your messages below (press Ctrl+C to quit)")
        print(f"{Fore.WHITE}📋 Commands: /help, /clear, /users, /quit")
        print(f"{Fore.CYAN}{'=' * self.terminal_width}")
        print()
    
    def _message_display_loop(self):
        """Background thread for displaying messages."""
        while self.running:
            try:
                # Get message from queue with timeout
                message = self.message_queue.get(timeout=0.1)
                self._display_message(message)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Display error: {e}")
    
    def _display_message(self, message: ChatMessage):
        """Display a single message."""
        # Add to message history
        self.messages.append(message)
        
        # Keep only recent messages
        if len(self.messages) > 100:
            self.messages = self.messages[-100:]
        
        # Clear current line and display message
        sys.stdout.write('\r' + ' ' * self.terminal_width + '\r')
        print(str(message))
        
        # Show input prompt
        self._show_input_prompt()
    
    def _show_input_prompt(self):
        """Show the input prompt."""
        prompt = f"{Fore.GREEN}[{self.username}]: {Fore.WHITE}"
        sys.stdout.write(prompt)
        sys.stdout.flush()
    
    def _input_loop(self):
        """Main input handling loop."""
        while self.running and self.connected:
            try:
                # Show input prompt
                self._show_input_prompt()
                
                # Get user input
                user_input = input().strip()
                
                if not self.connected:
                    break
                
                if user_input:
                    # Handle commands
                    if user_input.startswith('/'):
                        self._handle_command(user_input)
                    else:
                        # Send message via callback
                        if self.input_callback:
                            self.input_callback(user_input)
                            
            except EOFError:
                break
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}🛑 Disconnecting...")
                break
            except Exception as e:
                print(f"\n{Fore.RED}❌ Input error: {e}")
        
        self.stop()
    
    def _handle_command(self, command: str):
        """Handle internal UI commands."""
        cmd_parts = command.split()
        cmd = cmd_parts[0].lower()
        
        if cmd == '/help':
            self._show_help()
        elif cmd == '/clear':
            self._clear_chat()
        elif cmd == '/clear-all':
            self.clear_all_traces()
        elif cmd == '/users':
            self._show_users()
        elif cmd in ['/quit', '/exit', '/q']:
            print(f"{Fore.YELLOW}👋 Goodbye!")
            self.stop()
        else:
            # Unknown command, treat as message
            if self.input_callback:
                self.input_callback(command)
    
    def _show_help(self):
        """Show help information."""
        help_msg = ChatMessage(
            "SYSTEM",
            "Available commands:\n"
            "  /help      - Show this help\n"
            "  /clear     - Clear chat history\n"
            "  /clear-all - Clear all traces completely\n"
            "  /users     - Show connected users\n"
            "  /quit      - Disconnect and exit",
            "system"
        )
        self.add_message(help_msg)
    
    def _clear_chat(self):
        """Clear chat history."""
        self.messages.clear()
        self._clear_screen()
        self._show_welcome()
        print("🧹 Chat history cleared")
    
    def clear_all_traces(self):
        """Clear all traces and history completely."""
        self.messages.clear()
        self._clear_screen()
        self._show_welcome()
        
        # Force garbage collection
        import gc
        gc.collect()
        
        print("🧹 All traces cleared from terminal UI")
    
    def _show_users(self):
        """Show connected users (placeholder)."""
        users_msg = ChatMessage(
            "SYSTEM",
            "User list feature coming soon!",
            "system"
        )
        self.add_message(users_msg)
    
    def add_message(self, message: ChatMessage):
        """Add a message to the display queue."""
        if self.running:
            self.message_queue.put(message)
    
    def add_system_message(self, content: str):
        """Add a system message."""
        msg = ChatMessage("SYSTEM", content, "system")
        self.add_message(msg)
    
    def add_error_message(self, content: str):
        """Add an error message."""
        msg = ChatMessage("SYSTEM", content, "error")
        self.add_message(msg)
    
    def add_chat_message(self, sender: str, content: str):
        """Add a chat message."""
        msg = ChatMessage(sender, content, "chat")
        self.add_message(msg)
    
    def set_input_callback(self, callback: Callable):
        """Set callback for handling user input."""
        self.input_callback = callback
    
    def set_connection_status(self, connected: bool):
        """Update connection status."""
        self.connected = connected
        if not connected:
            self.add_error_message("Lost connection to server")
    
    def stop(self):
        """Stop the terminal UI."""
        self.running = False
        self.connected = False
        print(f"\n{Fore.YELLOW}🛑 Terminal UI stopped")

class SimpleTerminalUI:
    """Simplified terminal UI for systems without colorama."""
    
    def __init__(self, username: str, host: str, port: int):
        self.username = username
        self.host = host
        self.port = port
        self.connected = False
        self.running = False
        self.input_callback: Optional[Callable] = None
    
    def start(self):
        """Start the simple terminal UI."""
        self.running = True
        self.connected = True
        
        print(f"🚀 Confluxus")
        print(f"👤 Username: {self.username}")
        print(f"🌐 Server: {self.host}:{self.port}")
        print(f"🔒 Status: Connected")
        print(f"💬 Type your messages below (press Ctrl+C to quit)")
        print(f"📋 Commands: /help, /clear, /users, /quit")
        print("-" * 50)
        
        self._input_loop()
    
    def _input_loop(self):
        """Main input handling loop."""
        while self.running and self.connected:
            try:
                user_input = input(f"[{self.username}]: ").strip()
                
                if not self.connected:
                    break
                
                if user_input:
                    if user_input.startswith('/'):
                        self._handle_command(user_input)
                    else:
                        if self.input_callback:
                            self.input_callback(user_input)
                            
            except EOFError:
                break
            except KeyboardInterrupt:
                print("\n🛑 Disconnecting...")
                break
            except Exception as e:
                print(f"\n❌ Input error: {e}")
        
        self.stop()
    
    def _handle_command(self, command: str):
        """Handle internal UI commands."""
        cmd_parts = command.split()
        cmd = cmd_parts[0].lower()
        
        if cmd == '/help':
            print("Available commands:")
            print("  /help   - Show this help")
            print("  /clear  - Clear screen")
            print("  /users  - Show connected users")
            print("  /quit   - Disconnect and exit")
        elif cmd == '/clear':
            os.system('cls' if os.name == 'nt' else 'clear')
        elif cmd == '/users':
            print("User list feature coming soon!")
        elif cmd in ['/quit', '/exit', '/q']:
            print("👋 Goodbye!")
            self.stop()
        else:
            if self.input_callback:
                self.input_callback(command)
    
    def add_message(self, sender: str, content: str, msg_type: str = "chat"):
        """Add a message to display."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if msg_type == "system":
            print(f"[{timestamp}] [SYSTEM] {content}")
        elif msg_type == "error":
            print(f"[{timestamp}] [ERROR] {content}")
        else:
            print(f"[{timestamp}] [{sender}] {content}")
    
    def set_input_callback(self, callback: Callable):
        """Set callback for handling user input."""
        self.input_callback = callback
    
    def set_connection_status(self, connected: bool):
        """Update connection status."""
        self.connected = connected
        if not connected:
            print("❌ Lost connection to server")
    
    def stop(self):
        """Stop the simple terminal UI."""
        self.running = False
        self.connected = False
        print("🛑 Terminal UI stopped")

def create_ui(username: str, host: str, port: int, use_colors: bool = True):
    """Create appropriate UI based on available features."""
    if use_colors and COLORS_AVAILABLE:
        return TerminalUI(username, host, port)
    else:
        return SimpleTerminalUI(username, host, port)
