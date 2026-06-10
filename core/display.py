import time
import threading
from collections import deque
from typing import Optional


class Display:
    def __init__(self, ui, username: str, peers: dict, peers_lock: threading.Lock):
        self.ui = ui
        self.username = username
        self._peers = peers
        self._peers_lock = peers_lock
        self.history: deque = deque(maxlen=500)

    def display_chat(self, sender: str, message: str):
        self.history.append(("chat", sender, message))
        if self.ui:
            self.ui.add_chat_message(sender, message)
        else:
            ts = time.strftime("%H:%M:%S")
            print(f"\r[{ts}] [{sender}]: {message}")
            print(f"[{self.username}]: ", end="", flush=True)

    def display_direct(self, sender: str, message: str):
        self.history.append(("direct", sender, message))
        tag = "DM from" if not sender.startswith("you") else "DM"
        text = f"[{tag} {sender}]: {message}"
        if self.ui:
            self.ui.add_system_message(text)
        else:
            print(f"\r{text}")
            print(f"[{self.username}]: ", end="", flush=True)

    def display_system(self, message: str):
        self.history.append(("system", "", message))
        if self.ui:
            self.ui.add_system_message(message)
        else:
            print(f"\r[SYSTEM]: {message}")
            print(f"[{self.username}]: ", end="", flush=True)

    def list_peers(self):
        with self._peers_lock:
            if not self._peers:
                self.display_system("No connected peers")
                return
            lines = [f"Connected peers ({len(self._peers)}):"]
            for conn in self._peers.values():
                lines.append(f"  {conn.username} @ {conn.address[0]}:{conn.address[1]}")
            self.display_system('\n'.join(lines))

    def show_help(self):
        self.display_system(
            "Commands:\n"
            "  /connect <host> <port>  - Connect to another peer\n"
            "  /peers                  - List connected peers\n"
            "  /msg <user> <msg>       - Send direct message\n"
            "  /nick <name>            - Change your nickname\n"
            "  /status                 - Show session info\n"
            "  /reconnect on|off       - Enable/disable auto-reconnect\n"
            "  /history [N]            - Show last N messages\n"
            "  /clear                  - Clear screen\n"
            "  /help                   - Show this help\n"
            "  /quit                   - Disconnect and exit\n"
            "\n"
            "Any other text broadcasts to all connected peers"
        )

    def show_history(self, n: int = 10):
        lines = []
        for kind, sender, msg in list(self.history)[-n:]:
            if kind == "chat":
                lines.append(f"[{sender}]: {msg}")
            elif kind == "direct":
                lines.append(f"[DM {sender}]: {msg}")
            else:
                lines.append(f"[SYSTEM]: {msg}")
        self.display_system('\n'.join(lines) if lines else "No history")
