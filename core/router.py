import json
import uuid
import socket
import threading
from typing import Callable

from core.seen_ids import SeenIdCache
from core.dm import encode_dm, decode_dm
from sanitizer import RateLimiter


class Router:
    def __init__(
        self,
        seen_ids: SeenIdCache,
        rate_limiter: RateLimiter,
        peers: dict,
        peers_lock: threading.Lock,
        display,
        remove_peer_cb: Callable[[socket.socket], None],
        own_username: str,
    ):
        self.seen_ids = seen_ids
        self.rate_limiter = rate_limiter
        self.peers = peers
        self.peers_lock = peers_lock
        self.display = display
        self._remove_peer = remove_peer_cb
        self.own_username = own_username

    def process_message(self, raw: str, source_sock: socket.socket):
        with self.peers_lock:
            conn = self.peers.get(source_sock)
        if not conn:
            return

        peer_key = f"{conn.address[0]}:{conn.address[1]}"
        if not self.rate_limiter.allow(peer_key):
            return

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return

        msg_type = data.get("type")
        content = data.get("message", "")
        sender = data.get("username", "?")
        msg_id = data.get("id", "")

        if self.seen_ids.seen(msg_id):
            return

        if msg_type in ("chat", "direct"):
            plaintext = conn.crypto.decrypt(content)
            if plaintext is None:
                return
            if not conn.crypto.ready:
                sender = f"[PLAIN] {sender}"
        else:
            plaintext = content

        if msg_type == "chat":
            is_dm, dm_target, body = decode_dm(plaintext)
            if is_dm:
                if dm_target == self.own_username:
                    self.display.display_direct(sender, body)
                return
            self.display.display_chat(sender, body)
            self._forward_plaintext(sender, body, source_sock)

        elif msg_type == "nick_change":
            old_name = data.get("old", "")
            new_name = data.get("new", "")
            self._update_peer_username(source_sock, new_name)
            self.display.display_system(f"{old_name} changed nickname to {new_name}")

    def _forward_plaintext(self, sender: str, plaintext: str, exclude_sock: socket.socket):
        msg_id = str(uuid.uuid4())
        self.seen_ids.seen(msg_id)

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

    def broadcast_plaintext(self, plaintext: str):
        msg_id = str(uuid.uuid4())
        self.seen_ids.seen(msg_id)

        with self.peers_lock:
            for sock, peer in list(self.peers.items()):
                encrypted = peer.crypto.encrypt(plaintext)
                payload = json.dumps({
                    "type": "chat",
                    "username": self.own_username,
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
            self.display.display_system(f"No peer '{target_username}' connected")
            return

        dm_plaintext = encode_dm(target_username, plaintext)
        encrypted = target_crypto.encrypt(dm_plaintext)
        payload = json.dumps({
            "type": "chat",
            "username": self.own_username,
            "message": encrypted,
        }) + '\n'
        try:
            target_sock.sendall(payload.encode('utf-8'))
        except socket.error:
            self._remove_peer(target_sock)

    def _update_peer_username(self, sock: socket.socket, new_name: str):
        with self.peers_lock:
            conn = self.peers.get(sock)
            if conn:
                conn.username = new_name
