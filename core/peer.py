import socket
import time
import threading
import json
from typing import Optional

from core.seen_ids import SeenIdCache
from core.connection import (
    PeerConnection,
    ReconnectState,
    handle_incoming_handshake,
    initiate_outgoing_handshake,
    send_line,
)
from core.router import Router
from core.commands import Commander
from core.display import Display
from core.tofu import TofuStore
from sanitizer import check_username, validate_peer_count, RateLimiter
from terminal_ui import create_ui


def _on_peer_discovered(display, peers_lock, peers, host, port, username):
    """Callback when mDNS discovers a peer on LAN."""
    with peers_lock:
        already = any(p.username == username for p in peers.values())
    if not already:
        display.display_system(
            f"Peer {username} found on LAN ({host}:{port})"
            f" \u2014 /connect {host} {port} to connect"
        )


__version__ = "0.2.0"


class P2PPeer:
    def __init__(self, host: str = '0.0.0.0', port: int = 9000, username: str = None,
                 enable_encryption: bool = True, use_ui: bool = True, auto_clear: bool = True,
                 mesh_ttl: int = 3, enable_discovery: bool = False,
                 direct_only: bool = False):
        self.host = host
        self.port = port
        self.username = username
        self.encryption_enabled = enable_encryption
        self.mesh_ttl = mesh_ttl
        self.enable_discovery = enable_discovery
        self.direct_only = direct_only
        self._discovery = None
        self.running = False
        self.ui = None
        self.use_ui = use_ui
        self.auto_clear = auto_clear

        self.peers: dict = {}
        self.listener_socket: Optional[socket.socket] = None
        self.peers_lock = threading.Lock()
        self.seen_ids = SeenIdCache()
        self.rate_limiter = RateLimiter()
        self.reconnect_enabled = True
        self._reconnect_timers: dict = {}
        self.display = Display(None, username, self.peers, self.peers_lock)
        self.tofu = TofuStore(enable_encryption, self.display.display_system)
        self.router = Router(
            self.seen_ids, self.rate_limiter, self.peers, self.peers_lock,
            self.display, self._remove_peer, username, self.mesh_ttl,
            direct_only=direct_only,
        )
        self.cmdr = Commander(
            username, self.peers, self.peers_lock,
            self.display, self.router,
            self.connect_to_peer, self._remove_peer,
            self.stop,
            host=host, port=port,
            encryption_enabled=enable_encryption,
            start_time=None,
            reconnect_cb=self._set_reconnect_enabled,
        )

    def start(self):
        self.running = True
        self.cmdr._start_time = time.time()

        if not self.encryption_enabled:
            import threading
            import time
            def _warn():
                while self.running:
                    self.display.display_system(
                        "\u26a0  ENCRYPTION DISABLED \u2014 all messages are plaintext on the wire"
                    )
                    time.sleep(60)
            threading.Thread(target=_warn, daemon=True).start()

        if not self._start_listener():
            self.running = False
            return

        if self.direct_only:
            self.display.display_system(
                "⚡ Direct-only mode — mesh forwarding disabled. "
                "Messages reach only peers you are directly connected to."
            )

        if self.enable_discovery:
            from core.discovery import LocalDiscovery
            self._discovery = LocalDiscovery(
                self.username, self.port,
                lambda name, ip, port: _on_peer_discovered(
                    self.display, self.peers_lock, self.peers, ip, port, name
                ),
            )

        if self.use_ui:
            self.ui = create_ui(self.username, self.host, self.port)
            self.ui.set_input_callback(self.cmdr.handle_input)
            self.display.ui = self.ui
            self.display.display_system(f"Listening on {self.host}:{self.port}")
            self.display.display_system("Use /connect <host> <port> to link with other peers")
            self.ui.start()
        else:
            self._basic_input_loop()

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

    def _handle_incoming(self, sock: socket.socket, addr):
        if not validate_peer_count(len(self.peers)):
            send_line(sock, json.dumps({"e": "peer_limit"}))
            sock.close()
            return

        conn, error = handle_incoming_handshake(sock, addr, self.username, self.encryption_enabled)
        if error:
            sock.close()
            self.display.display_system(error)
            return

        if conn.crypto.ready and self.encryption_enabled:
            fingerprint = conn.crypto.get_fingerprint()
            self.tofu.save_fingerprint(addr[0], addr[1], fingerprint)
            self.display.display_system(f"Peer {conn.username} fingerprint: {fingerprint}")

        with self.peers_lock:
            self.peers[sock] = conn

        self.display.display_system(f"{conn.username} connected ({addr[0]}:{addr[1]})")
        self._listen_peer(sock)

    def _set_reconnect_enabled(self, enabled: bool):
        self.reconnect_enabled = enabled
        if not enabled:
            for timer in self._reconnect_timers.values():
                timer.cancel()
            self._reconnect_timers.clear()

    def _schedule_reconnect(self, host: str, port: int):
        key = f"{host}:{port}"
        # Cancel any existing timer for this peer
        old = self._reconnect_timers.pop(key, None)
        if old:
            old.cancel()

        state = ReconnectState(host=host, port=port)
        delay = state.next_delay()

        def _do_reconnect():
            self._reconnect_timers.pop(key, None)
            if not self.running or not self.reconnect_enabled:
                return
            self.display.display_system(f"Reconnecting to {host}:{port} (attempt {state.attempt + 1}/{state.max_attempts})...")
            ok = self.connect_to_peer(host, port)
            if ok:
                return
            state.attempt += 1
            if state.attempt >= state.max_attempts:
                self.display.display_system(f"Gave up reconnecting to {host}:{port} after {state.max_attempts} attempts")
                return

            next_delay = state.next_delay()
            self.display.display_system(f"Next reconnect in {next_delay}s...")
            timer = threading.Timer(next_delay, _do_reconnect)
            timer.daemon = True
            self._reconnect_timers[key] = timer
            timer.start()

        self.display.display_system(f"Scheduling reconnect in {delay}s...")
        timer = threading.Timer(delay, _do_reconnect)
        timer.daemon = True
        self._reconnect_timers[key] = timer
        timer.start()

    def connect_to_peer(self, host: str, port: int) -> bool:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, port))

            if not validate_peer_count(len(self.peers)):
                sock.close()
                self.display.display_system("Maximum peer connections reached")
                return False

            conn, error = initiate_outgoing_handshake(sock, host, port, self.username, self.encryption_enabled)
            if error:
                sock.close()
                self.display.display_system(error)
                return False
            conn.is_outbound = True

            if conn.crypto.ready and self.encryption_enabled:
                fingerprint = conn.crypto.get_fingerprint()
                if not self.tofu.verify_fingerprint(host, port, fingerprint, conn.username):
                    sock.close()
                    self.display.display_system(
                        f"Connection to {conn.username} rejected \u2014 fingerprint not confirmed"
                    )
                    return False

            with self.peers_lock:
                self.peers[sock] = conn

            self.display.display_system(f"Connected to {conn.username} ({host}:{port})")
            threading.Thread(target=self._listen_peer, args=(sock,), daemon=True).start()
            return True

        except socket.timeout:
            self.display.display_system(f"Connection to {host}:{port} timed out")
        except ConnectionRefusedError:
            self.display.display_system(f"Connection refused by {host}:{port}")
        except OSError as e:
            self.display.display_system(f"Failed to connect to {host}:{port} - {e}")
        except Exception as e:
            self.display.display_system(f"Failed to connect to {host}:{port} - {e}")

        return False

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
                        self.router.process_message(line, sock)
        except Exception as e:
            if self.running:
                self.display.display_system(f"Receive error: {e}")
        self._remove_peer(sock)

    def _remove_peer(self, sock: socket.socket):
        with self.peers_lock:
            conn = self.peers.pop(sock, None)
        if conn:
            peer_key = f"{conn.address[0]}:{conn.address[1]}"
            self.rate_limiter.reset(peer_key)
            self.display.display_system(f"{conn.username} disconnected")
            try:
                sock.close()
            except Exception:
                pass
            if conn.is_outbound and self.reconnect_enabled:
                self._schedule_reconnect(conn.address[0], conn.address[1])

    def _basic_input_loop(self):
        print(f"\nCL Chat P2P \u2014 Listening on {self.host}:{self.port}")
        print(f"Username: {self.username}")
        print("Type /help for commands\n")
        while self.running:
            try:
                text = input(f"[{self.username}]: ").strip()
                if text:
                    self.cmdr.handle_input(text)
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
        for timer in self._reconnect_timers.values():
            timer.cancel()
        self._reconnect_timers.clear()
        if self._discovery:
            self._discovery.close()
            self._discovery = None
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
