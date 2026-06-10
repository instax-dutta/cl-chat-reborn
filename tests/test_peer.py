"""
Tests for peer.py — P2PPeer message processing, dedup, forwarding,
nick change, direct messages, and rate limiting with mocked sockets.
"""

import json
import uuid
import pytest
from unittest.mock import MagicMock, patch

from peer import P2PPeer, PeerConnection
from encryption import CryptoContext


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture
def peer():
    """P2PPeer with no UI, no listener, and running=True."""
    p = P2PPeer(
        host='127.0.0.1',
        port=0,
        username='TestUser',
        enable_encryption=True,
        use_ui=False,
        auto_clear=False,
    )
    p.running = True
    return p


@pytest.fixture
def mock_sock():
    """Standard mock socket for testing."""
    sock = MagicMock()
    sock.fileno.return_value = 12345
    sock.sendall.return_value = None
    return sock


def make_peer_connection(sock, username='RemoteUser', crypto=None):
    """Create a PeerConnection with a given socket, username, and crypto."""
    conn = PeerConnection(sock, ('127.0.0.1', 9000))
    conn.username = username
    conn.crypto = crypto or CryptoContext(enabled=False)
    return conn


def register_peer(peer_obj, sock, username='RemoteUser', crypto=None):
    """Register a mock socket + PeerConnection in the peer's peers dict."""
    conn = make_peer_connection(sock, username=username, crypto=crypto)
    with peer_obj.peers_lock:
        peer_obj.peers[sock] = conn
    return conn


# ── Message Dedup Tests ───────────────────────────────────────────────────


class TestMessageDedup:
    """Tests for _process_message deduplication via seen_ids."""

    def test_dedup_duplicate_id_dropped(self, peer, mock_sock):
        """A second message with the same msg_id is dropped."""
        register_peer(peer, mock_sock)

        msg = json.dumps({
            "type": "chat",
            "username": "RemoteUser",
            "message": "Hello!",
            "id": "dup-uuid-123",
        })

        with patch.object(peer, '_display_chat') as mock_display:
            peer._process_message(msg, mock_sock)
            peer._process_message(msg, mock_sock)
            assert mock_display.call_count == 1, \
                "Dedup failed: _display_chat called more than once"

    def test_no_id_no_dedup(self, peer, mock_sock):
        """Messages without an id field are both processed."""
        register_peer(peer, mock_sock)

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

        with patch.object(peer, '_display_chat') as mock_display:
            peer._process_message(msg_a, mock_sock)
            peer._process_message(msg_b, mock_sock)
            assert mock_display.call_count == 2, \
                "Both messages should be displayed when no id is present"

    def test_different_ids_both_accepted(self, peer, mock_sock):
        """Messages with different IDs are both processed."""
        register_peer(peer, mock_sock)

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

        with patch.object(peer, '_display_chat') as mock_display:
            peer._process_message(msg_a, mock_sock)
            peer._process_message(msg_b, mock_sock)
            assert mock_display.call_count == 2, \
                "Both messages with different IDs should be displayed"


# ── Nick Change Tests ─────────────────────────────────────────────────────


class TestNickChange:
    """Tests for nick_change message processing."""

    def test_nick_change_updates_username(self, peer, mock_sock):
        """A nick_change message updates the peer's username."""
        conn = register_peer(peer, mock_sock, username='OldName')

        msg = json.dumps({
            "type": "nick_change",
            "username": "OldName",
            "old": "OldName",
            "new": "NewName",
        })

        with patch.object(peer, '_display_system'):
            peer._process_message(msg, mock_sock)

        assert conn.username == "NewName", \
            f"Expected 'NewName', got '{conn.username}'"

    def test_nick_change_displays_change(self, peer, mock_sock):
        """A nick_change message triggers a system message."""
        register_peer(peer, mock_sock, username='OldName')

        msg = json.dumps({
            "type": "nick_change",
            "username": "OldName",
            "old": "OldName",
            "new": "NewName",
        })

        with patch.object(peer, '_display_system') as mock_sys:
            peer._process_message(msg, mock_sock)
            mock_sys.assert_called_once()
            # Verify the message mentions both names
            call_arg = mock_sys.call_args[0][0]
            assert "OldName" in call_arg
            assert "NewName" in call_arg


# ── Chat Forwarding Tests ─────────────────────────────────────────────────


class TestChatForwarding:
    """Tests for chat message forwarding to other peers."""

    def test_chat_forwarded_to_other_peers(self, peer):
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

        register_peer(peer, sock_a, username='Alice', crypto=crypto_a)
        register_peer(peer, sock_b, username='Bob', crypto=crypto_b)

        msg = json.dumps({
            "type": "chat",
            "username": "Alice",
            "message": crypto_a.encrypt("Hello from Alice"),
            "id": str(uuid.uuid4()),
        })

        with patch.object(peer, '_forward_plaintext') as mock_forward:
            peer._process_message(msg, sock_a)
            assert mock_forward.called, \
                "_forward_plaintext should be called for chat-type messages"

    def test_chat_from_single_peer(self, peer, mock_sock):
        """A chat message from a peer with no other peers still displays."""
        register_peer(peer, mock_sock)

        msg = json.dumps({
            "type": "chat",
            "username": "RemoteUser",
            "message": "Hello alone",
            "id": str(uuid.uuid4()),
        })

        with patch.object(peer, '_display_chat') as mock_display:
            with patch.object(peer, '_forward_plaintext') as mock_forward:
                peer._process_message(msg, mock_sock)
                assert mock_display.called, \
                    "_display_chat should be called"
                # Forwarding may still be called (with no other peers to send to)
                # The important thing is no crash


# ── Direct Message Tests ──────────────────────────────────────────────────


class TestDirectMessage:
    """Tests for direct message processing."""

    def test_direct_message_displays(self, peer, mock_sock):
        """A direct message is displayed via _display_direct."""
        register_peer(peer, mock_sock)

        msg = json.dumps({
            "type": "direct",
            "username": "RemoteUser",
            "message": "This is a direct message",
            "id": str(uuid.uuid4()),
        })

        with patch.object(peer, '_display_direct') as mock_direct:
            peer._process_message(msg, mock_sock)
            assert mock_direct.called, \
                "_display_direct should be called for direct-type messages"

    def test_direct_not_forwarded(self, peer, mock_sock):
        """A direct message should not trigger forwarding."""
        register_peer(peer, mock_sock)

        msg = json.dumps({
            "type": "direct",
            "username": "RemoteUser",
            "message": "Private message",
            "id": str(uuid.uuid4()),
        })

        with patch.object(peer, '_forward_plaintext') as mock_forward:
            peer._process_message(msg, mock_sock)
            assert not mock_forward.called, \
                "Direct messages should not be forwarded"


# ── Invalid Input Tests ──────────────────────────────────────────────────


class TestInvalidInput:
    """Tests for handling of malformed or invalid messages."""

    def test_invalid_json_no_crash(self, peer, mock_sock):
        """Sending garbage JSON should not crash (returns silently)."""
        register_peer(peer, mock_sock)

        # Should not raise any exception
        peer._process_message("not valid json at all", mock_sock)
        peer._process_message("{broken json", mock_sock)
        peer._process_message("", mock_sock)

    def test_empty_message_no_crash(self, peer, mock_sock):
        """Empty message after JSON parse should not crash."""
        register_peer(peer, mock_sock)

        msg = json.dumps({
            "type": "chat",
            "username": "RemoteUser",
            "message": "",
            "id": str(uuid.uuid4()),
        })

        # Should not raise — _display_chat and _forward_plaintext handle empties
        with patch.object(peer, '_display_chat'):
            with patch.object(peer, '_forward_plaintext'):
                peer._process_message(msg, mock_sock)

    def test_unknown_peer_socket_ignored(self, peer, mock_sock):
        """Message from an unregistered socket is ignored."""
        msg = json.dumps({
            "type": "chat",
            "message": "ignored",
            "id": str(uuid.uuid4()),
        })

        # mock_sock is NOT registered in peer.peers — should return silently
        with patch.object(peer, '_display_chat') as mock_display:
            peer._process_message(msg, mock_sock)
            assert not mock_display.called, \
                "Unknown peer socket should be ignored"


# ── Rate Limiter Integration Test ─────────────────────────────────────────


class TestRateLimiter:
    """Tests for rate limiting integration in _process_message."""

    def test_rate_limiter_blocks_excess(self, peer, mock_sock):
        """RateLimiter prevents processing when limit is exceeded."""
        register_peer(peer, mock_sock)

        # Override rate_limiter with a small limit for testing
        from sanitizer import RateLimiter
        peer.rate_limiter = RateLimiter(max_events=2, window=60)

        with patch.object(peer, '_display_chat') as mock_display:
            # First two messages should go through
            for i in range(2):
                msg = json.dumps({
                    "type": "chat",
                    "username": "RemoteUser",
                    "message": f"Message {i}",
                    "id": str(uuid.uuid4()),
                })
                peer._process_message(msg, mock_sock)

            # Third message should be rate-limited
            msg = json.dumps({
                "type": "chat",
                "username": "RemoteUser",
                "message": "Blocked by rate limiter",
                "id": str(uuid.uuid4()),
            })
            peer._process_message(msg, mock_sock)

            # Only 2 of 3 messages should have reached _display_chat
            assert mock_display.call_count == 2, \
                f"Expected 2 _display_chat calls, got {mock_display.call_count}"


# ── Registry Lifecycle Tests ──────────────────────────────────────────────


class TestPeerRegistration:
    """Tests for peer registration lookup."""

    def test_unrecognized_type_ignored(self, peer, mock_sock):
        """An unknown message type should be ignored without error."""
        register_peer(peer, mock_sock)

        msg = json.dumps({
            "type": "unknown_type",
            "username": "RemoteUser",
            "message": "test",
            "id": str(uuid.uuid4()),
        })

        # Patches for all display methods to ensure none are called
        with patch.object(peer, '_display_chat') as mock_chat:
            with patch.object(peer, '_display_direct') as mock_direct:
                with patch.object(peer, '_display_system') as mock_sys:
                    peer._process_message(msg, mock_sock)
                    assert not mock_chat.called
                    assert not mock_direct.called
                    assert not mock_sys.called
