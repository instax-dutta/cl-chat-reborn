"""
Tests for core.router — Router.process_message, dedup, forwarding,
nick change, direct messages, and rate limiting with mocked sockets.
"""

import json
import uuid
import pytest
from unittest.mock import MagicMock, patch

from core.connection import PeerConnection
from encryption import CryptoContext


# ── Helpers ──────────────────────────────────────────────────────────────


def make_peer_connection(sock, username='RemoteUser', crypto=None):
    """Create a PeerConnection with a given socket, username, and crypto."""
    conn = PeerConnection(sock, ('127.0.0.1', 9000))
    conn.username = username
    conn.crypto = crypto or CryptoContext(enabled=False)
    return conn


def register_peer(router_obj, sock, username='RemoteUser', crypto=None):
    """Register a mock socket + PeerConnection in the router's peers dict."""
    conn = make_peer_connection(sock, username=username, crypto=crypto)
    with router_obj.peers_lock:
        router_obj.peers[sock] = conn
    return conn


# ── Message Dedup Tests ───────────────────────────────────────────────────


class TestMessageDedup:
    """Tests for Router.process_message deduplication via SeenIdCache."""

    def test_dedup_duplicate_id_dropped(self, router, mock_socket):
        """A second message with the same msg_id is dropped."""
        register_peer(router, mock_socket)

        msg = json.dumps({
            "type": "chat",
            "username": "RemoteUser",
            "message": "Hello!",
            "id": "dup-uuid-123",
        })

        router.process_message(msg, mock_socket)
        router.process_message(msg, mock_socket)
        assert router.display.display_chat.call_count == 1, \
            "Dedup failed: display_chat called more than once"

    def test_no_id_no_dedup(self, router, mock_socket):
        """Messages without an id field are both processed."""
        register_peer(router, mock_socket)

        msg_a = json.dumps({
            "type": "chat",
            "username": "RemoteUser",
            "message": "First",
        })
        msg_b = json.dumps({
            "type": "chat",
            "username": "RemoteUser",
            "message": "Second",
        })

        router.process_message(msg_a, mock_socket)
        router.process_message(msg_b, mock_socket)
        assert router.display.display_chat.call_count == 2, \
            "Both messages should be displayed when no id is present"

    def test_different_ids_both_accepted(self, router, mock_socket):
        """Messages with different IDs are both processed."""
        register_peer(router, mock_socket)

        msg_a = json.dumps({
            "type": "chat",
            "username": "RemoteUser",
            "message": "Alpha",
            "id": str(uuid.uuid4()),
        })
        msg_b = json.dumps({
            "type": "chat",
            "username": "RemoteUser",
            "message": "Beta",
            "id": str(uuid.uuid4()),
        })

        router.process_message(msg_a, mock_socket)
        router.process_message(msg_b, mock_socket)
        assert router.display.display_chat.call_count == 2, \
            "Both messages with different IDs should be displayed"


# ── Nick Change Tests ─────────────────────────────────────────────────────


class TestNickChange:
    """Tests for nick_change message processing."""

    def test_nick_change_updates_username(self, router, mock_socket):
        """A nick_change message updates the peer's username."""
        conn = register_peer(router, mock_socket, username='OldName')

        msg = json.dumps({
            "type": "nick_change",
            "username": "OldName",
            "old": "OldName",
            "new": "NewName",
        })

        router.process_message(msg, mock_socket)

        assert conn.username == "NewName", \
            f"Expected 'NewName', got '{conn.username}'"

    def test_nick_change_displays_change(self, router, mock_socket):
        """A nick_change message triggers a system message."""
        register_peer(router, mock_socket, username='OldName')

        msg = json.dumps({
            "type": "nick_change",
            "username": "OldName",
            "old": "OldName",
            "new": "NewName",
        })

        router.process_message(msg, mock_socket)
        router.display.display_system.assert_called_once()
        call_arg = router.display.display_system.call_args[0][0]
        assert "OldName" in call_arg
        assert "NewName" in call_arg


# ── Chat Forwarding Tests ─────────────────────────────────────────────────


class TestChatForwarding:
    """Tests for chat message forwarding to other peers."""

    def test_chat_forwarded_to_other_peers(self, router):
        """A chat message is forwarded to other connected peers."""
        sock_a = MagicMock()
        sock_a.fileno.return_value = 1
        sock_b = MagicMock()
        sock_b.fileno.return_value = 2

        crypto_a = CryptoContext(enabled=True)
        crypto_b = CryptoContext(enabled=True)
        pub_a = crypto_a.get_public_key()
        pub_b = crypto_b.get_public_key()
        crypto_a.derive_shared(pub_b)
        crypto_b.derive_shared(pub_a)

        register_peer(router, sock_a, username='Alice', crypto=crypto_a)
        register_peer(router, sock_b, username='Bob', crypto=crypto_b)

        msg = json.dumps({
            "type": "chat",
            "username": "Alice",
            "message": crypto_a.encrypt("Hello from Alice"),
            "id": str(uuid.uuid4()),
        })

        with patch.object(router, '_forward_plaintext') as mock_forward:
            router.process_message(msg, sock_a)
            assert mock_forward.called, \
                "_forward_plaintext should be called for chat-type messages"

    def test_chat_from_single_peer(self, router, mock_socket):
        """A chat message from a peer with no other peers still displays."""
        register_peer(router, mock_socket)

        msg = json.dumps({
            "type": "chat",
            "username": "RemoteUser",
            "message": "Hello alone",
            "id": str(uuid.uuid4()),
        })

        router.process_message(msg, mock_socket)
        assert router.display.display_chat.called, \
            "display_chat should be called"


# ── Direct Message Tests ──────────────────────────────────────────────────


# ── Invalid Input Tests ──────────────────────────────────────────────────


class TestInvalidInput:
    """Tests for handling of malformed or invalid messages."""

    def test_invalid_json_no_crash(self, router, mock_socket):
        """Sending garbage JSON should not crash (returns silently)."""
        register_peer(router, mock_socket)

        router.process_message("not valid json at all", mock_socket)
        router.process_message("{broken json", mock_socket)
        router.process_message("", mock_socket)

    def test_empty_message_no_crash(self, router, mock_socket):
        """Empty message after JSON parse should not crash."""
        register_peer(router, mock_socket)

        msg = json.dumps({
            "type": "chat",
            "username": "RemoteUser",
            "message": "",
            "id": str(uuid.uuid4()),
        })

        router.process_message(msg, mock_socket)

    def test_unknown_peer_socket_ignored(self, router, mock_socket):
        """Message from an unregistered socket is ignored."""
        msg = json.dumps({
            "type": "chat",
            "message": "ignored",
            "id": str(uuid.uuid4()),
        })

        router.process_message(msg, mock_socket)
        assert not router.display.display_chat.called, \
            "Unknown peer socket should be ignored"


# ── Rate Limiter Integration Test ─────────────────────────────────────────


class TestRateLimiter:
    """Tests for rate limiting integration in Router.process_message."""

    def test_rate_limiter_blocks_excess(self, router, mock_socket):
        """RateLimiter prevents processing when limit is exceeded."""
        register_peer(router, mock_socket)

        from sanitizer import RateLimiter as RL
        router.rate_limiter = RL(max_events=2, window=60)

        for i in range(2):
            msg = json.dumps({
                "type": "chat",
                "username": "RemoteUser",
                "message": f"Message {i}",
                "id": str(uuid.uuid4()),
            })
            router.process_message(msg, mock_socket)

        msg = json.dumps({
            "type": "chat",
            "username": "RemoteUser",
            "message": "Blocked by rate limiter",
            "id": str(uuid.uuid4()),
        })
        router.process_message(msg, mock_socket)

        assert router.display.display_chat.call_count == 2, \
            f"Expected 2 display_chat calls, got {router.display.display_chat.call_count}"


# ── Registry Lifecycle Tests ──────────────────────────────────────────────


class TestPeerRegistration:
    """Tests for peer registration lookup."""

    def test_unrecognized_type_ignored(self, router, mock_socket):
        """An unknown message type should be ignored without error."""
        register_peer(router, mock_socket)

        msg = json.dumps({
            "type": "unknown_type",
            "username": "RemoteUser",
            "message": "test",
            "id": str(uuid.uuid4()),
        })

        router.process_message(msg, mock_socket)
        assert not router.display.display_chat.called
        assert not router.display.display_direct.called
        assert not router.display.display_system.called
