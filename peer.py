#!/usr/bin/env python3
"""
CL Chat — Peer-to-Peer Command Line Chat
Decentralized messaging with per-connection ECDH encryption.
"""

import sys
import argparse

from core.peer import P2PPeer, __version__
from core.connection import PeerConnection
from sanitizer import check_username


def get_username() -> str:
    while True:
        name = input("Enter your username: ").strip()
        sanitized = check_username(name)
        if sanitized:
            return sanitized
        print("Invalid username (alphanumeric, 2-20 chars)")


def main():
    parser = argparse.ArgumentParser(description="CL Chat - P2P Command Line Chat")
    parser.add_argument("--host", default="0.0.0.0", help="Interface to listen on (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=9000, help="Port to listen on (default: 9000)")
    parser.add_argument("--username", help="Your display name")
    parser.add_argument("--no-encryption", action="store_true", help="Disable encryption")
    parser.add_argument("--no-ui", action="store_true", help="Use basic console interface")
    parser.add_argument("--mesh-ttl", type=int, default=3, help="Mesh hop limit (default: 3)")
    parser.add_argument("--discover", action="store_true", help="Enable mDNS LAN peer discovery")
    parser.add_argument("--connect", help="Connect to a peer on startup (host:port)")

    args = parser.parse_args()

    username = args.username or get_username()
    sanitized = check_username(username)
    if not sanitized:
        print("Invalid username (alphanumeric, 2-20 chars)")
        sys.exit(1)
    username = sanitized

    peer = P2PPeer(
        host=args.host,
        port=args.port,
        username=username,
        enable_encryption=not args.no_encryption,
        use_ui=not args.no_ui,
        mesh_ttl=args.mesh_ttl,
        enable_discovery=args.discover,
    )

    try:
        if args.connect:
            if ':' in args.connect:
                host, port_str = args.connect.split(':', 1)
                try:
                    port = int(port_str)
                    if 1 <= port <= 65535:
                        peer.running = True
                        peer.connect_to_peer(host, port)
                    else:
                        print("Invalid port (1-65535)")
                        sys.exit(1)
                except ValueError:
                    print("Invalid port format")
                    sys.exit(1)

        peer.start()
    except KeyboardInterrupt:
        pass
    finally:
        peer.stop()


if __name__ == "__main__":
    main()
