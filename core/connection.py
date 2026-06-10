import socket
import json
from typing import Optional, Tuple

from encryption import CryptoContext
from sanitizer import check_username


class PeerConnection:
    def __init__(self, sock: socket.socket, address: Tuple):
        self.socket = sock
        self.username = ""
        self.address = address
        self.crypto = CryptoContext(enabled=False)

    def __repr__(self):
        return f"<Peer {self.username} @ {self.address[0]}:{self.address[1]}>"


def recv_line(sock: socket.socket, timeout: float = 5.0) -> Optional[str]:
    """Read one \\n-terminated line from socket using 4096-byte buffered reads."""
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


def send_line(sock: socket.socket, line: str):
    sock.sendall((line + '\n').encode('utf-8'))


def handle_incoming_handshake(
    sock: socket.socket,
    addr: Tuple[str, int],
    own_username: str,
    enable_encryption: bool,
) -> Tuple[Optional[PeerConnection], Optional[str]]:
    """Server-side: accept incoming connection and perform handshake.
    Returns (PeerConnection, None) on success or (None, error_message) on failure.
    The socket is NOT closed by this function on failure.
    """
    conn = PeerConnection(sock, addr)
    conn.crypto = CryptoContext(enable_encryption)

    try:
        hs = json.dumps({"u": own_username, "k": conn.crypto.get_public_key()})
        send_line(sock, hs)

        line = recv_line(sock)
        if not line:
            return None, "Empty handshake response"

        data = json.loads(line)
        peer_name = check_username(data.get("u", ""))
        peer_pubkey = data.get("k", "")

        if not peer_name:
            return None, "Invalid username from peer"

        if peer_name == own_username:
            return None, "Cannot connect to yourself"

        conn.username = peer_name
        if peer_pubkey:
            conn.crypto.derive_shared(peer_pubkey)

        return conn, None

    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, "Invalid handshake data"
    except Exception as e:
        return None, str(e)


def initiate_outgoing_handshake(
    sock: socket.socket,
    host: str,
    port: int,
    own_username: str,
    enable_encryption: bool,
) -> Tuple[Optional[PeerConnection], Optional[str]]:
    """Client-side: connect to remote peer and perform handshake.
    Returns (PeerConnection, None) on success or (None, error_message) on failure.
    The socket is NOT closed by this function on failure.
    """
    conn = PeerConnection(sock, (host, port))
    conn.crypto = CryptoContext(enable_encryption)

    try:
        line = recv_line(sock)
        if not line:
            return None, "Empty handshake from peer"

        data = json.loads(line)
        peer_name = check_username(data.get("u", ""))
        peer_pubkey = data.get("k", "")

        if not peer_name:
            return None, "Invalid username from peer"

        if peer_name == own_username:
            return None, "Cannot connect to yourself"

        conn.username = peer_name
        if peer_pubkey:
            conn.crypto.derive_shared(peer_pubkey)

        hs = json.dumps({"u": own_username, "k": conn.crypto.get_public_key()})
        send_line(sock, hs)

        return conn, None

    except socket.timeout:
        return None, f"Connection to {host}:{port} timed out"
    except ConnectionRefusedError:
        return None, f"Connection refused by {host}:{port}"
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, f"Invalid protocol from {host}:{port}"
    except OSError as e:
        return None, f"Failed to connect to {host}:{port} - {e}"
    except Exception as e:
        return None, str(e)
