"""
Shared pytest fixtures for CL Chat test suite.
"""

import threading
from unittest.mock import MagicMock

import pytest

from encryption import CryptoContext
from core.seen_ids import SeenIdCache
from core.router import Router
from sanitizer import RateLimiter


@pytest.fixture
def crypto_enabled():
    """CryptoContext with encryption enabled."""
    return CryptoContext(enabled=True)


@pytest.fixture
def crypto_disabled():
    """CryptoContext with encryption disabled."""
    return CryptoContext(enabled=False)


@pytest.fixture
def alice_crypto():
    """Alice's CryptoContext for two-party tests."""
    return CryptoContext(enabled=True)


@pytest.fixture
def bob_crypto():
    """Bob's CryptoContext for two-party tests."""
    return CryptoContext(enabled=True)


@pytest.fixture
def shared_crypto_pair(alice_crypto, bob_crypto):
    """Two CryptoContext instances with mutual key derivation.

    Returns (alice_crypto, bob_crypto) where both have derived the
    shared key from the other's public key.
    """
    alice_pub = alice_crypto.get_public_key()
    bob_pub = bob_crypto.get_public_key()
    alice_crypto.derive_shared(bob_pub)
    bob_crypto.derive_shared(alice_pub)
    return alice_crypto, bob_crypto


@pytest.fixture
def mock_socket():
    """A mock socket for testing message processing."""
    sock = MagicMock()
    sock.fileno.return_value = 12345
    sock.sendall.return_value = None
    return sock


@pytest.fixture
def router():
    """Router with mocked display and remove_peer callback."""
    seen_ids = SeenIdCache(maxsize=100)
    rate_limiter = RateLimiter()
    peers = {}
    peers_lock = threading.Lock()
    display = MagicMock()
    remove_peer = MagicMock()
    return Router(seen_ids, rate_limiter, peers, peers_lock, display, remove_peer, 'TestUser')
