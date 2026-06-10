import json
import threading
from unittest.mock import MagicMock

from core.router import Router
from core.seen_ids import SeenIdCache
from sanitizer import RateLimiter


class TestMeshTtl:
    def test_ttl_decremented_on_forward(self):
        seen_ids = SeenIdCache()
        rate_limiter = RateLimiter()
        peers = {}
        peers_lock = threading.Lock()
        display = MagicMock()
        remove_peer = MagicMock()
        router = Router(seen_ids, rate_limiter, peers, peers_lock, display, remove_peer, "TestUser", mesh_ttl=3)

        sock_a = MagicMock()
        sock_a.fileno.return_value = 1
        sock_b = MagicMock()
        sock_b.fileno.return_value = 2

        from core.connection import PeerConnection
        from encryption import CryptoContext
        crypto_a = CryptoContext(enabled=True)
        crypto_b = CryptoContext(enabled=True)
        crypto_a.derive_shared(crypto_b.get_public_key())
        crypto_b.derive_shared(crypto_a.get_public_key())

        conn_a = PeerConnection(sock_a, ("127.0.0.1", 9000))
        conn_a.username = "Alice"
        conn_a.crypto = crypto_a
        conn_b = PeerConnection(sock_b, ("127.0.0.1", 9001))
        conn_b.username = "Bob"
        conn_b.crypto = crypto_b

        with peers_lock:
            peers[sock_a] = conn_a
            peers[sock_b] = conn_b

        # Simulate a forwarded message — it should include a ttl in the payload
        payload = json.dumps({
            "type": "chat",
            "username": "Alice",
            "message": crypto_a.encrypt("hello"),
            "id": "test-uuid",
            "ttl": 2,
        })
        router.process_message(payload, sock_a)

        # The forward should carry ttl=1
        sent = sock_b.sendall.call_args[0][0].decode()
        sent_data = json.loads(sent)
        assert sent_data["ttl"] == 1

    def test_ttl_zero_does_not_forward(self):
        seen_ids = SeenIdCache()
        rate_limiter = RateLimiter()
        peers = {}
        peers_lock = threading.Lock()
        display = MagicMock()
        remove_peer = MagicMock()
        router = Router(seen_ids, rate_limiter, peers, peers_lock, display, remove_peer, "TestUser", mesh_ttl=3)

        sock_a = MagicMock()
        sock_a.fileno.return_value = 1
        sock_b = MagicMock()
        sock_b.fileno.return_value = 2

        from core.connection import PeerConnection
        from encryption import CryptoContext
        crypto = CryptoContext(enabled=False)
        conn_a = PeerConnection(sock_a, ("127.0.0.1", 9000))
        conn_a.username = "Alice"
        conn_a.crypto = crypto
        conn_b = PeerConnection(sock_b, ("127.0.0.1", 9001))
        conn_b.username = "Bob"
        conn_b.crypto = crypto

        with peers_lock:
            peers[sock_a] = conn_a
            peers[sock_b] = conn_b

        payload = json.dumps({
            "type": "chat",
            "username": "Alice",
            "message": "hello",
            "id": "test-uuid-drop",
            "ttl": 1,
        })
        router.process_message(payload, sock_a)

        # TTL was 1, after decrement is 0 — no forward
        assert sock_b.sendall.called is False
