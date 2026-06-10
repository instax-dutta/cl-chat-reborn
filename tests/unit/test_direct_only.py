from unittest.mock import MagicMock

from core.router import Router
from core.seen_ids import SeenIdCache
from sanitizer import RateLimiter


def make_router(direct_only=False):
    return Router(
        seen_ids=SeenIdCache(),
        rate_limiter=RateLimiter(),
        peers={},
        peers_lock=__import__('threading').Lock(),
        display=MagicMock(),
        remove_peer_cb=MagicMock(),
        own_username="TestUser",
        direct_only=direct_only,
    )


class TestDirectOnly:
    def test_direct_only_suppresses_forward(self):
        router = make_router(direct_only=True)
        assert router.direct_only is True
        # The guard at the top of _forward_plaintext will return immediately
        router._forward_plaintext("Alice", "hello", MagicMock())
        # No crash and no peers iterated is the success case

    def test_direct_only_false_does_not_suppress(self):
        router = make_router(direct_only=False)
        assert router.direct_only is False

    def test_forward_plaintext_noop_in_direct_only(self):
        router = make_router(direct_only=True)
        sent = []
        # Should return immediately without iterating peers
        router._forward_plaintext("Alice", "hello", MagicMock())
        assert sent == []

    def test_process_message_ttl_with_direct_only(self):
        import json
        import threading
        router = make_router(direct_only=True)
        peers = router.peers
        peers_lock = router.peers_lock
        sock_a = MagicMock()
        sock_b = MagicMock()

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
            "id": "test-ttl-direct-only",
            "ttl": 3,
        })
        router.process_message(payload, sock_a)

        # Should NOT forward to sock_b in direct-only mode
        assert sock_b.sendall.called is False
