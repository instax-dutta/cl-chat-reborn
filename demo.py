#!/usr/bin/env python3
"""
Demo script for Multi-Client CLI Chat - MVP
Showcases the enhanced features including encryption and terminal UI.
"""

import subprocess
import time
import sys
import os

def print_banner():
    """Print the demo banner."""
    print("=" * 60)
    print("🚀 Multi-Client CLI Chat - Enhanced Features Demo")
    print("=" * 60)
    print("✨ Features:")
    print("   • End-to-end encryption using AES")
    print("   • Modern terminal UI with colors")
    print("   • Real-time messaging")
    print("   • Multiple concurrent clients")
    print("   • Enhanced commands (/help, /clear, etc.)")
    print("=" * 60)

def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    try:
        import cryptography
        print("✅ cryptography - Available")
    except ImportError:
        print("❌ cryptography - Not installed")
        return False
    
    try:
        import colorama
        print("✅ colorama - Available")
    except ImportError:
        print("⚠️  colorama - Not installed (UI will use basic colors)")
    
    return True

def show_usage_instructions():
    """Show usage instructions."""
    print("\n📖 Usage Instructions:")
    print("1. Start the server:")
    print("   python3 server.py")
    print()
    print("2. Connect multiple clients:")
    print("   # Terminal 1 - Enhanced UI")
    print("   python3 client_enhanced.py --username Alice")
    print()
    print("   # Terminal 2 - Enhanced UI")
    print("   python3 client_enhanced.py --username Bob")
    print()
    print("   # Terminal 3 - Basic UI")
    print("   python3 client.py --username Charlie")
    print()
    print("3. Try these commands in the chat:")
    print("   /help    - Show available commands")
    print("   /clear   - Clear chat history")
    print("   /users   - Show connected users")
    print("   /quit    - Disconnect")
    print()

def show_encryption_info():
    """Show encryption information."""
    print("🔒 Encryption Details:")
    print("   • Algorithm: AES-256 (Fernet)")
    print("   • Key derivation: PBKDF2 with SHA256")
    print("   • Salt: Random 16-byte salt")
    print("   • Iterations: 100,000")
    print("   • End-to-end: Messages encrypted client-side")
    print()

def show_ui_features():
    """Show UI features."""
    print("🎨 UI Features:")
    print("   • Colored timestamps and usernames")
    print("   • System message highlighting")
    print("   • Error message formatting")
    print("   • Real-time message display")
    print("   • Command history")
    print("   • Responsive terminal interface")
    print()

def run_quick_test():
    """Run a quick test to verify the system works."""
    print("🧪 Running quick test...")
    
    try:
        # Test server connection
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', 5000))
        sock.close()
        
        if result == 0:
            print("✅ Server is running on localhost:5000")
            return True
        else:
            print("❌ Server is not running")
            print("   Start it with: python3 server.py")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main demo function."""
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Please install missing dependencies:")
        print("   pip install cryptography colorama")
        return
    
    print()
    
    # Show features
    show_encryption_info()
    show_ui_features()
    
    # Run quick test
    if run_quick_test():
        print("🎉 System is ready for demo!")
        show_usage_instructions()
    else:
        print("⚠️  Please start the server first")
        print("   python3 server.py")
    
    print("=" * 60)
    print("Happy Chatting! 🎉")

if __name__ == "__main__":
    main()
