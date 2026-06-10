import json
import socket
import threading
from typing import Callable, Optional

from sanitizer import check_username, clean_message


class Commander:
    def __init__(
        self,
        username: str,
        peers: dict,
        peers_lock: threading.Lock,
        display,
        router,
        connect_cb: Callable[[str, int], bool],
        remove_peer_cb: Callable[[socket.socket], None],
        stop_cb: Callable[[], None],
    ):
        self.username = username
        self.peers = peers
        self.peers_lock = peers_lock
        self.display = display
        self.router = router
        self._connect = connect_cb
        self._remove_peer = remove_peer_cb
        self._stop = stop_cb

    def handle_input(self, text: str):
        from core.fingerprint_challenge import challenge_queue, FingerprintChallenge
        import queue as _queue
        try:
            challenge = challenge_queue.get_nowait()
            if text.strip().lower() == 'yes':
                challenge.accepted = True
            challenge.result_event.set()
            return
        except _queue.Empty:
            pass

        if not text or not isinstance(text, str):
            return
        text = clean_message(text)
        if not text:
            return

        if text.startswith('/'):
            self.handle_command(text)
        else:
            self.router.broadcast_plaintext(text)
            self.display.display_chat(self.username, text)

    def handle_command(self, cmd: str):
        parts = cmd.split()
        if not parts:
            return
        command = parts[0].lower()

        if command == '/connect' and len(parts) >= 3:
            host = parts[1]
            try:
                port = int(parts[2])
                if port < 1 or port > 65535:
                    self.display.display_system("Port must be 1-65535")
                    return
                self._connect(host, port)
            except ValueError:
                self.display.display_system("Usage: /connect <host> <port>")

        elif command == '/peers':
            self.display.list_peers()

        elif command == '/msg' and len(parts) >= 3:
            target = parts[1]
            msg = ' '.join(parts[2:])
            msg = clean_message(msg)
            if not msg:
                return
            self.router.send_direct(target, msg)
            self.display.display_direct(f"you -> {target}", msg)

        elif command == '/nick' and len(parts) >= 2:
            new = check_username(parts[1])
            if not new:
                self.display.display_system("Invalid nickname (alphanumeric, 2-20 chars)")
                return
            old = self.username
            self.username = new
            self.router.own_username = new
            if hasattr(self.display.ui, 'set_username'):
                self.display.ui.set_username(self.username)
            self.display.display_system(f"Nickname changed: {old} -> {self.username}")
            self._send_nick_notification(old)

        elif command == '/clear':
            if self.display.ui and hasattr(self.display.ui, 'clear_chat'):
                self.display.ui.clear_chat()

        elif command == '/help':
            self.display.show_help()

        elif command in ('/quit', '/exit', '/q'):
            self._stop()

        else:
            self.display.display_system(f"Unknown: {command}. Type /help")

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

    def update_peer_username(self, sock: socket.socket, new_name: str):
        with self.peers_lock:
            conn = self.peers.get(sock)
            if conn:
                conn.username = new_name
