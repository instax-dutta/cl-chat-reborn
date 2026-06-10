#!/usr/bin/env python3
"""
CL Chat — Peer-to-Peer Command Line Chat
Decentralized messaging with per-connection ECDH encryption.
"""

import socket
import threading
import json
import uuid
import sys
import os
import hashlib
import time
from collections import deque
from typing import Dict, Optional, Tuple

from encryption import CryptoContext
from sanitizer import check_username, clean_message, validate_peer_count, RateLimiter
from terminal_ui import create_ui


class P2PPeer:
    def __init__(self, host: str = '0.0.0.0', port: int = 9000, username: str = None,
                 enable_encryption: bool = True, use_ui: bool = True, auto_clear: bool = True):
        self.host = host
        self.port = port
        self.username = username
        self.encryption_enabled = enable_encryption
        self.running = False
        self.ui = None
        self.use_ui = use_ui
        self.auto_clear = auto_clear

        self.peers: Dict[socket.socket, 'PeerConnection'] = {}
        self.listener_socket: Optional[socket.socket] = None
        self.peers_lock = threading.Lock()
        self.seen_ids_deque: deque = deque(maxlen=10000)
        self.seen_ids_set: set = set()
        self.seen_ids_lock = threading.Lock()
        self.rate_limiter = RateLimiter()

    def start(self):
        self.running = True

        if not self._start_listener():
            self.running = False
            return

        if self.use_ui:
            self.ui = create_ui(self.username, self.host, self.port)
            self.ui.set_input_callback(self._handle_input)
            self._display_system(f"Listening on {self.host}:{self.port}")
            self._display_system("Use /connect <host> <port> to link with other peers")
            self.ui.start()
        else:
            self._basic_input_loop()

    def _recv_line(self, sock: socket.socket, timeout: float = 5.0) -> Optional[str]:
        """Read one \n-terminated line from socket using 4096-byte buffered reads."""
        sock.settimeout(timeout)
        buf = b""
        try:
            while b'\n' not in buf:
                chunk = sock.recv(4096)
                if not chunk:
                    return None
                buf += chunk
            line, buf = buf.split(b'\n', 1)
            return line.decode('utf-8', errors='replace')
        except (socket.timeout, socket.error):
            return None
        finally:
            sock.settimeout(None)

    def _send_line(self, sock: socket.socket, line: str):
        sock.sendall((line + '\n').encode('utf-8'))

    def _start_listener(self) -> bool:
        try:
            self.listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.listener_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.listener_socket.bind((self.host, self.port))
            self.listener_socket.listen(5)
            self.listener_socket.settimeout(1.0)

            t = threading.Thread(target=self._accept_loop, daemon=True)
            t.start()
            return True
        except OSError as e:
            print(f"Failed to bind to {self.host}:{self.port} - {e}")
            return False

    def _accept_loop(self):
        while self.running:
            try:
                sock, addr = self.listener_socket.accept()
                threading.Thread(target=self._handle_incoming, args=(sock, addr), daemon=True).start()
            except socket.timeout:
                continue
            except Exception:
                pass

    # ── Handshake ──────────────────────────────────────────────

    def _handle_incoming(self, sock: socket.socket, addr: Tuple[str, int]):
        conn = PeerConnection(sock, addr)
        conn.crypto = CryptoContext(self.encryption_enabled)

        try:
            hs = json.dumps({"u": self.username, "k": conn.crypto.get_public_key()})
            self._send_line(sock, hs)

            line = self._recv_line(sock)
            if not line:
                sock.close()
                return

            data = json.loads(line)
            peer_name = check_username(data.get("u", ""))
            peer_pubkey = data.get("k", "")

            if not peer_name:
                sock.close()
                return
            if peer_name == self.username:
                sock.close()
                return
            if not validate_peer_count(len(self.peers)):
                self._send_line(sock, json.dumps({"e": "peer_limit"}))
                sock.close()
                return

            conn.username = peer_name
            if peer_pubkey:
                conn.crypto.derive_shared(peer_pubkey)

                # Store peer fingerprint for MITM detection (CR-03)
                if peer_pubkey and self.encryption_enabled:
                    fingerprint = conn.crypto.get_fingerprint()
                    self._save_fingerprint(addr[0], addr[1], fingerprint)
                    self._display_system(f"Peer {peer_name} fingerprint: {fingerprint}")

            with self.peers_lock:
                self.peers[sock] = conn

            self._display_system(f"{peer_name} connected ({addr[0]}:{addr[1]})")
            self._listen_peer(sock)

        except (json.JSONDecodeError, UnicodeDecodeError):
            sock.close()
        except Exception as e:
            if self.running:
                self._display_system(f"Connection error from {addr}: {e}")
            sock.close()


    def connect_to_peer(self, host: str, port: int) -> bool:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, port))

            conn = PeerConnection(sock, (host, port))
            conn.crypto = CryptoContext(self.encryption_enabled)

            line = self._recv_line(sock)
            if not line:
                sock.close()
                self._display_system("Empty handshake from peer")
                return False

            data = json.loads(line)
            peer_name = check_username(data.get("u", ""))
            peer_pubkey = data.get("k", "")

            if not peer_name:
                sock.close()
                self._display_system("Invalid username from peer")
                return False
            if peer_name == self.username:
                sock.close()
                self._display_system("Cannot connect to yourself")
                return False
            if not validate_peer_count(len(self.peers)):
                sock.close()
                self._display_system("Maximum peer connections reached")
                return False

            conn.username = peer_name
            if peer_pubkey:
                conn.crypto.derive_shared(peer_pubkey)

                # Fingerprint verification (MITM protection, CR-03)
                if peer_pubkey and self.encryption_enabled:
                    fingerprint = conn.crypto.get_fingerprint()
                    if not self._verify_fingerprint(host, port, fingerprint, peer_name):
                        sock.close()
                        self._display_system(f"Connection to {peer_name} rejected \u2014 fingerprint not confirmed")
                        return False

            hs = json.dumps({"u": self.username, "k": conn.crypto.get_public_key()})
            self._send_line(sock, hs)

            with self.peers_lock:
                self.peers[sock] = conn

            self._display_system(f"Connected to {peer_name} ({host}:{port})")
            threading.Thread(target=self._listen_peer, args=(sock,), daemon=True).start()
            return True

        except socket.timeout:
            self._display_system(f"Connection to {host}:{port} timed out")
        except ConnectionRefusedError:
            self._display_system(f"Connection refused by {host}:{port}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._display_system(f"Invalid protocol from {host}:{port}")
        except Exception as e:
            self._display_system(f"Failed to connect to {host}:{port} - {e}")

        return False

    # ── Message handling ───────────────────────────────────────

    def _listen_peer(self, sock: socket.socket):
        buf = ""
        try:
            while True:
                try:
                    chunk = sock.recv(4096).decode('utf-8')
                    if not chunk:
                        break
                except (socket.timeout, socket.error, ConnectionResetError, BrokenPipeError):
                    break

                buf += chunk
                while '\n' in buf:
                    line, buf = buf.split('\n', 1)
                    line = line.strip()
                    if line:
                        self._process_message(line, sock)
        except Exception as e:
            if self.running:
                self._display_system(f"Receive error: {e}")
        self._remove_peer(sock)

    def _process_message(self, raw: str, source_sock: socket.socket):
        # Rate limit check per source socket
        if not self.rate_limiter.allow(str(id(source_sock))):
            return

        with self.peers_lock:
            conn = self.peers.get(source_sock)
        if not conn:
            return

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return

        msg_type = data.get("type")
        content = data.get("message", "")
        sender = data.get("username", "?")
        msg_id = data.get("id", "")

        with self.seen_ids_lock:
            if msg_id and msg_id in self.seen_ids_set:
                return
            if msg_id:
                if len(self.seen_ids_deque) >= 10000:
                    evicted = self.seen_ids_deque.popleft()
                    self.seen_ids_set.discard(evicted)
                self.seen_ids_deque.append(msg_id)
                self.seen_ids_set.add(msg_id)

        if msg_type in ("chat", "direct"):
            plaintext = conn.crypto.decrypt(content)
            if plaintext is None:
                return
        else:
            plaintext = content

        if msg_type == "chat":
            self._display_chat(sender, plaintext)
            self._forward_plaintext(sender, plaintext, source_sock)

        elif msg_type == "direct":
            self._display_direct(sender, plaintext)

        elif msg_type == "nick_change":
            old_name = data.get("old", "")
            new_name = data.get("new", "")
            self._update_peer_username(source_sock, new_name)
            self._display_system(f"{old_name} changed nickname to {new_name}")

    def _forward_plaintext(self, sender: str, plaintext: str, exclude_sock: socket.socket):
        msg_id = str(uuid.uuid4())
        with self.seen_ids_lock:
            if len(self.seen_ids_deque) >= 10000:
                evicted = self.seen_ids_deque.popleft()
                self.seen_ids_set.discard(evicted)
            self.seen_ids_deque.append(msg_id)
            self.seen_ids_set.add(msg_id)

        with self.peers_lock:
            for sock, peer in list(self.peers.items()):
                if sock == exclude_sock:
                    continue
                encrypted = peer.crypto.encrypt(plaintext)
                payload = json.dumps({
                    "type": "chat",
                    "username": sender,
                    "message": encrypted,
                    "id": msg_id,
                }) + '\n'
                try:
                    sock.sendall(payload.encode('utf-8'))
                except socket.error:
                    self._remove_peer(sock)

    def _broadcast_plaintext(self, plaintext: str):
        msg_id = str(uuid.uuid4())
        with self.seen_ids_lock:
            if len(self.seen_ids_deque) >= 10000:
                evicted = self.seen_ids_deque.popleft()
                self.seen_ids_set.discard(evicted)
            self.seen_ids_deque.append(msg_id)
            self.seen_ids_set.add(msg_id)

        with self.peers_lock:
            for sock, peer in list(self.peers.items()):
                encrypted = peer.crypto.encrypt(plaintext)
                payload = json.dumps({
                    "type": "chat",
                    "username": self.username,
                    "message": encrypted,
                    "id": msg_id,
                }) + '\n'
                try:
                    sock.sendall(payload.encode('utf-8'))
                except socket.error:
                    self._remove_peer(sock)

    def send_direct(self, target_username: str, plaintext: str):
        with self.peers_lock:
            target_sock = None
            target_crypto = None
            for sock, peer in self.peers.items():
                if peer.username == target_username:
                    target_sock = sock
                    target_crypto = peer.crypto
                    break

        if target_sock is None:
            self._display_system(f"No peer '{target_username}' connected")
            return

        encrypted = target_crypto.encrypt(plaintext)
        payload = json.dumps({
            "type": "direct",
            "username": self.username,
            "message": encrypted,
        }) + '\n'
        try:
            target_sock.sendall(payload.encode('utf-8'))
        except socket.error:
            self._remove_peer(target_sock)

    # ── Input / commands ──────────────────────────────────────

    def _handle_input(self, text: str):
        if not text or not isinstance(text, str):
            return
        text = clean_message(text)
        if not text:
            return

        if text.startswith('/'):
            self._handle_command(text)
        else:
            self._broadcast_plaintext(text)
            self._display_chat(self.username, text)

    def _handle_command(self, cmd: str):
        parts = cmd.split()
        if not parts:
            return
        command = parts[0].lower()

        if command == '/connect' and len(parts) >= 3:
            host = parts[1]
            try:
                port = int(parts[2])
                if port < 1 or port > 65535:
                    self._display_system("Port must be 1-65535")
                    return
                self.connect_to_peer(host, port)
            except ValueError:
                self._display_system("Usage: /connect <host> <port>")

        elif command == '/peers':
            self._list_peers()

        elif command == '/msg' and len(parts) >= 3:
            target = parts[1]
            msg = ' '.join(parts[2:])
            msg = clean_message(msg)
            if not msg:
                return
            self.send_direct(target, msg)
            self._display_direct(f"you -> {target}", msg)

        elif command == '/nick' and len(parts) >= 2:
            new = check_username(parts[1])
            if not new:
                self._display_system("Invalid nickname (alphanumeric, 2-20 chars)")
                return
            old = self.username
            self.username = new
            if self.ui and hasattr(self.ui, 'set_username'):
                self.ui.set_username(self.username)
            self._display_system(f"Nickname changed: {old} -> {self.username}")
            self._send_nick_notification(old)

        elif command == '/clear':
            if self.ui and hasattr(self.ui, 'clear_chat'):
                self.ui.clear_chat()

        elif command == '/help':
            self._show_help()

        elif command in ('/quit', '/exit', '/q'):
            self.stop()

        else:
            self._display_system(f"Unknown: {command}. Type /help")

    def _send_nick_notification(self, old_name: str):
        payload = json.dumps({
            "type": "nick_change",
            "username": self.username,
            "old": old_name,
            "new": self.username,
        }) + '\n'
        with self.peers_lock:
            for sock in list(self.peers.keys()):
                try:
                    sock.sendall(payload.encode('utf-8'))
                except socket.error:
                    self._remove_peer(sock)

    def _update_peer_username(self, sock: socket.socket, new_name: str):
        with self.peers_lock:
            conn = self.peers.get(sock)
            if conn:
                conn.username = new_name

    # ── Display helpers ───────────────────────────────────────

    def _list_peers(self):
        with self.peers_lock:
            if not self.peers:
                self._display_system("No connected peers")
                return
            lines = [f"Connected peers ({len(self.peers)}):"]
            for conn in self.peers.values():
                lines.append(f"  {conn.username} @ {conn.address[0]}:{conn.address[1]}")
            self._display_system('\n'.join(lines))

    def _show_help(self):
        self._display_system(
            "Commands:\n"
            "  /connect <host> <port>  - Connect to another peer\n"
            "  /peers                  - List connected peers\n"
            "  /msg <user> <msg>       - Send direct message\n"
            "  /nick <name>            - Change your nickname\n"
            "  /clear                  - Clear screen\n"
            "  /help                   - Show this help\n"
            "  /quit                   - Disconnect and exit\n"
            "\n"
            "Any other text broadcasts to all connected peers"
        )

    def _display_chat(self, sender: str, message: str):
        if self.ui:
            self.ui.add_chat_message(sender, message)
        else:
            ts = time.strftime("%H:%M:%S")
            print(f"\r[{ts}] [{sender}]: {message}")
            print(f"[{self.username}]: ", end="", flush=True)

    def _display_direct(self, sender: str, message: str):
        tag = "DM from" if not sender.startswith("you") else "DM"
        text = f"[{tag} {sender}]: {message}"
        if self.ui:
            self.ui.add_system_message(text)
        else:
            print(f"\r{text}")
            print(f"[{self.username}]: ", end="", flush=True)

    def _display_system(self, message: str):
        if self.ui:
            self.ui.add_system_message(message)
        else:
            print(f"\r[SYSTEM]: {message}")
            print(f"[{self.username}]: ", end="", flush=True)

    # ── Connection management ─────────────────────────────────

    def _remove_peer(self, sock: socket.socket):
        with self.peers_lock:
            conn = self.peers.pop(sock, None)
        if conn:
            self.rate_limiter.reset(str(id(sock)))
            self._display_system(f"{conn.username} disconnected")
            try:
                sock.close()
            except Exception:
                pass

    def _basic_input_loop(self):
        print(f"\nCL Chat P2P — Listening on {self.host}:{self.port}")
        print(f"Username: {self.username}")
        print("Type /help for commands\n")
        while self.running:
            try:
                text = input(f"[{self.username}]: ").strip()
                if text:
                    self._handle_input(text)
            except (EOFError, KeyboardInterrupt):
                print()
                break
        self.stop()

    def stop(self):
        self.running = False
        with self.peers_lock:
            for sock in list(self.peers.keys()):
                try:
                    sock.close()
                except Exception:
                    pass
            self.peers.clear()
        if self.listener_socket:
            try:
                self.listener_socket.close()
            except Exception:
                pass
        if self.ui:
            self.ui.stop()
        if self.auto_clear:
            import gc
            gc.collect()

    # ── TOFU fingerprint helpers (CR-03) ──────────────────────

    @staticmethod
    def _known_hosts_path() -> str:
        """Return path to TOFU known_hosts file."""
        return os.path.join(os.path.expanduser('~'), '.clchat', 'known_hosts.json')

    @staticmethod
    def _load_known_hosts() -> dict:
        """Load TOFU known_hosts JSON. Returns empty dict if file missing or corrupt."""
        path = P2PPeer._known_hosts_path()
        try:
            with open(path) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _save_fingerprint(host: str, port: int, fingerprint: str):
        """Save a peer fingerprint to the TOFU known_hosts file."""
        path = P2PPeer._known_hosts_path()
        hosts = P2PPeer._load_known_hosts()
        hosts[f"{host}:{port}"] = fingerprint
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # Use a tmpfile + rename to prevent partial writes
        tmp = path + '.tmp'
        with open(tmp, 'w') as f:
            json.dump(hosts, f, indent=2)
        os.replace(tmp, path)

    def _verify_fingerprint(self, host: str, port: int, fingerprint: str, display_name: str) -> bool:
        """TOFU verification: check known_hosts, prompt user if unknown or changed.

        Args:
            host: Remote host address
            port: Remote port
            fingerprint: Peer's SHA-256 fingerprint string
            display_name: Peer's username for display
        Returns:
            True if fingerprint is accepted, False to abort connection
        """
        if not fingerprint:
            return True  # encryption disabled — skip verification

        hosts = self._load_known_hosts()
        key = f"{host}:{port}"

        if key in hosts:
            stored = hosts[key]
            if stored == fingerprint:
                return True  # Fingerprint matches — continue

            # Mismatch — warn user
            self._display_system(
                f"\u26a0\ufe0f  SECURITY WARNING: {display_name} ({host}:{port}) fingerprint mismatch!\n"
                f"    Previous: {stored[:20]}...\n"
                f"    Current:  {fingerprint[:20]}...\n"
                f"    Full: {fingerprint}\n"
                f"    Possible MITM attack or peer re-installed with new key."
            )
            self._display_system("Type 'yes' to accept the new fingerprint: ")
        else:
            # First connection — prompt for verification
            self._display_system(
                f"First connection to {display_name} ({host}:{port})\n"
                f"  Fingerprint: {fingerprint}\n"
                f"  Verify this fingerprint with the peer out-of-band (e.g., in person, via another channel)."
            )
            self._display_system("Type 'yes' to trust and continue: ")

        # Get user confirmation
        try:
            response = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            return False

        if response == 'yes':
            self._save_fingerprint(host, port, fingerprint)
            return True
        return False


class PeerConnection:
    def __init__(self, sock: socket.socket, address: Tuple):
        self.socket = sock
        self.username = ""
        self.address = address
        self.crypto = CryptoContext(enabled=False)

    def __repr__(self):
        return f"<Peer {self.username} @ {self.address[0]}:{self.address[1]}>"


def get_username() -> str:
    while True:
        name = input("Enter your username: ").strip()
        sanitized = check_username(name)
        if sanitized:
            return sanitized
        print("Invalid username (alphanumeric, 2-20 chars)")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="CL Chat - P2P Command Line Chat")
    parser.add_argument("--host", default="0.0.0.0", help="Interface to listen on (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=9000, help="Port to listen on (default: 9000)")
    parser.add_argument("--username", help="Your display name")
    parser.add_argument("--no-encryption", action="store_true", help="Disable encryption")
    parser.add_argument("--no-ui", action="store_true", help="Use basic console interface")
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
