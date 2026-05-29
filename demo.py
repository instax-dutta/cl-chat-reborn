#!/usr/bin/env python3
"""
Demo script for CL Chat — Peer-to-Peer CLI Chat
"""

import socket
import time
import sys
import os


def print_banner():
    print("=" * 60)
    print("CL Chat - Peer-to-Peer Command Line Chat")
    print("=" * 60)
    print("Features:")
    print("  • Peer-to-peer architecture (no central server)")
    print("  • End-to-end encryption (AES-256)")
    print("  • Modern terminal UI with colors")
    print("  • Broadcast & direct messaging")
    print("  • Multiple concurrent peer connections")
    print("  • Commands: /connect, /msg, /peers, /nick")
    print("=" * 60)


def check_dependencies():
    print("Checking dependencies...")

    try:
        import cryptography
        print("  cryptography - Available")
    except ImportError:
        print("  cryptography - Not installed")
        return False

    try:
        import colorama
        print("  colorama - Available")
    except ImportError:
        print("  colorama - Not installed (UI will use basic output)")

    return True


def show_usage():
    print("\nUsage:")
    print("  Terminal 1 (Alice):")
    print("    python3 peer.py --username Alice --port 9000")
    print()
    print("  Terminal 2 (Bob):")
    print("    python3 peer.py --username Bob --port 9001")
    print("    # Then in Bob's terminal: /connect 127.0.0.1 9000")
    print()
    print("  Commands:")
    print("    /connect <host> <port>  - Connect to a peer")
    print("    /peers                  - List connected peers")
    print("    /msg <user> <msg>       - Send direct message")
    print("    /nick <name>            - Change nickname")
    print("    /clear                  - Clear screen")
    print("    /help                   - Show help")
    print("    /quit                   - Exit")
    print()


def check_port(port=9000):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('localhost', port))
        sock.close()
        return True
    except socket.error:
        return False


def main():
    print_banner()

    if not check_dependencies():
        print("Install missing deps: pip install cryptography colorama")
        return

    show_usage()

    port_free = check_port(9000)
    if port_free:
        print("Port 9000 is available for listening")
    else:
        print("Port 9000 is in use — use --port to specify a different one")

    print()
    print("=" * 60)
    print("Start chatting! Run peer.py in multiple terminals.")
    print("=" * 60)


if __name__ == "__main__":
    main()
