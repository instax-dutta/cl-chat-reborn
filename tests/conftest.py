"""
Shared pytest fixtures for CL Chat test suite.
"""

import pytest
from unittest.mock import MagicMock

from encryption import CryptoContext
from peer import P2PPeer


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
def mock_peer():
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
