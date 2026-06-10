"""
Tests for encryption.py — CryptoContext encrypt/decrypt round-trip,
disabled mode, fingerprint, and derivation error handling.
"""

import pytest

from encryption import CryptoContext


class TestEncryptDecryptRoundTrip:
    """Tests for encrypt/decrypt with valid shared keys."""

    def test_roundtrip(self, shared_crypto_pair):
        """Encrypt with Alice's context, decrypt with Bob's, matches original."""
        alice, bob = shared_crypto_pair
        plaintext = "Hello P2P!"
        ciphertext = alice.encrypt(plaintext)
        result = bob.decrypt(ciphertext)
        assert result == plaintext

    def test_bidirectional(self, shared_crypto_pair):
        """Encrypt with Bob's context, decrypt with Alice's, matches original."""
        alice, bob = shared_crypto_pair
        plaintext = "Message from Bob"
        ciphertext = bob.encrypt(plaintext)
        result = alice.decrypt(ciphertext)
        assert result == plaintext

    def test_multiple_messages(self, shared_crypto_pair):
        """Multiple messages can be exchanged correctly."""
        alice, bob = shared_crypto_pair
        messages = ["msg1", "hello world!", "a" * 1000, ""]
        for msg in messages:
            ct = alice.encrypt(msg)
            pt = bob.decrypt(ct)
            assert pt == msg

    def test_decrypt_wrong_key(self):
        """Decrypt with a different shared key returns None."""
        a1 = CryptoContext(enabled=True)
        b1 = CryptoContext(enabled=True)
        a2 = CryptoContext(enabled=True)
        b2 = CryptoContext(enabled=True)

        # Pair a1 with b1
        a1.derive_shared(b1.get_public_key())
        # Pair b2 with a2 (different pair)
        b2.derive_shared(a2.get_public_key())

        ciphertext = a1.encrypt("secret")
        # b2 has a different shared key — decryption should fail
        result = b2.decrypt(ciphertext)
        assert result is None


class TestDisabledMode:
    """Tests for CryptoContext with enabled=False."""

    def test_encrypt_returns_raw(self, crypto_disabled):
        """Disabled mode encrypt returns the raw plaintext unchanged."""
        result = crypto_disabled.encrypt("hello")
        assert result == "hello"

    def test_decrypt_returns_raw(self, crypto_disabled):
        """Disabled mode decrypt returns the raw payload unchanged."""
        result = crypto_disabled.decrypt("some-payload")
        assert result == "some-payload"

    def test_get_public_key_empty(self, crypto_disabled):
        """Disabled mode get_public_key returns empty string."""
        assert crypto_disabled.get_public_key() == ""

    def test_ready_false(self, crypto_disabled):
        """Disabled mode ready property is False."""
        assert crypto_disabled.ready is False

    def test_get_fingerprint_empty(self, crypto_disabled):
        """Disabled mode get_fingerprint returns empty string."""
        assert crypto_disabled.get_fingerprint() == ""


class TestEnabledMode:
    """Tests for CryptoContext with enabled=True."""

    def test_get_public_key_non_empty(self, crypto_enabled):
        """Enabled mode get_public_key returns a non-empty base64 string."""
        key = crypto_enabled.get_public_key()
        assert isinstance(key, str)
        assert len(key) > 0

    def test_ready_false_before_derivation(self, crypto_enabled):
        """Ready is False before any key derivation."""
        assert crypto_enabled.ready is False

    def test_ready_true_after_derivation(self, crypto_enabled):
        """Ready is True after successful key derivation."""
        peer = CryptoContext(enabled=True)
        crypto_enabled.derive_shared(peer.get_public_key())
        assert crypto_enabled.ready is True

    def test_get_fingerprint_non_empty(self, crypto_enabled):
        """Enabled mode get_fingerprint returns a colon-separated hex string."""
        fp = crypto_enabled.get_fingerprint()
        assert isinstance(fp, str)
        assert len(fp) > 0
        assert ":" in fp


class TestDeriveShared:
    """Tests for derive_shared error handling."""

    def test_invalid_base64(self, crypto_enabled):
        """Invalid base64 input sets shared_key to None (ready=False)."""
        crypto_enabled.derive_shared("!!!not-base64!!!")
        assert crypto_enabled.ready is False

    def test_invalid_key_bytes(self, crypto_enabled):
        """Valid base64 but wrong-length key bytes sets shared_key to None."""
        # "AAAAAA==" is 4 bytes of base64 (decodes to 3 bytes) — not valid X25519
        crypto_enabled.derive_shared("AAAAAA==")
        assert crypto_enabled.ready is False

    def test_empty_string(self, crypto_enabled):
        """Empty string as public key sets shared_key to None."""
        crypto_enabled.derive_shared("")
        assert crypto_enabled.ready is False

    def test_derive_shared_disabled_noop(self, crypto_disabled):
        """derive_shared on disabled context does nothing (ready stays False)."""
        crypto_disabled.derive_shared("some-key")
        assert crypto_disabled.ready is False
