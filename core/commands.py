import json
import socket
import time
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
        host: str = "0.0.0.0",
        port: int = 9000,
        encryption_enabled: bool = True,
        start_time: Optional[float] = None,
        reconnect_cb: Optional[Callable[[bool], None]] = None,
    ):
        self.username = username
        self.peers = peers
        self.peers_lock = peers_lock
        self.display = display
        self.router = router
        self._connect = connect_cb
        self._remove_peer = remove_peer_cb
        self._stop = stop_cb
        self._host = host
        self._port = port
        self._encryption_enabled = encryption_enabled
        self._start_time = start_time or time.time()
        self._reconnect_cb = reconnect_cb

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

        elif command == '/reconnect' and len(parts) >= 2:
            if parts[1] == 'off':
                if self._reconnect_cb:
                    self._reconnect_cb(False)
                self.display.display_system("Reconnect disabled")
            elif parts[1] == 'on':
                if self._reconnect_cb:
                    self._reconnect_cb(True)
                self.display.display_system("Reconnect enabled")
            else:
                self.display.display_system("Usage: /reconnect on|off")

        elif command == '/clear':
            if self.display.ui and hasattr(self.display.ui, 'clear_chat'):
                self.display.ui.clear_chat()

        elif command == '/status':
            self._show_status()

        elif command == '/history':
            parts = cmd.split()
            n = 10
            if len(parts) >= 2:
                try:
                    n = max(1, int(parts[1]))
                except ValueError:
                    pass
            self.display.show_history(n)

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

    def _show_status(self):
        uptime = time.time() - self._start_time
        hours, rem = divmod(int(uptime), 3600)
        minutes, seconds = divmod(rem, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"

        with self.peers_lock:
            peer_count = len(self.peers)
            peer_list = [f"  {c.username} @ {c.address[0]}:{c.address[1]}" for c in self.peers.values()]

        try:
            local_ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            local_ip = "unknown"

        lines = [
            f"Username:  {self.username}",
            f"Listen:    {self._host}:{self._port}",
            f"Local IP:  {local_ip}",
            f"Encryption: {'ON' if self._encryption_enabled else 'OFF'}",
            f"Uptime:    {uptime_str}",
            f"Peers:     {peer_count}",
        ] + peer_list

        self.display.display_system('\n'.join(lines))

    def update_peer_username(self, sock: socket.socket, new_name: str):
        with self.peers_lock:
            conn = self.peers.get(sock)
            if conn:
                conn.username = new_name
