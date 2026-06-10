"""
Encryption module for CL Chat
X25519 ECDH key exchange + ChaCha20-Poly1305 AEAD + HKDF-SHA256.

Each peer-to-peer connection gets its own ephemeral X25519 keypair.
A shared symmetric key is derived via HKDF-SHA256 from the ECDH shared secret.
Messages are encrypted with ChaCha20-Poly1305 using random 12-byte nonces,
providing authenticated encryption and forward secrecy.
"""

import base64
import binascii
import hashlib
import logging
import os
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

logger = logging.getLogger(__name__)


class CryptoContext:
    """Per-connection cryptographic context.

    Uses X25519 ECDH for key agreement and ChaCha20-Poly1305
    for authenticated encryption with random nonces.
    """

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._private_key = None
        self._shared_key = None

        if enabled:
            self._private_key = x25519.X25519PrivateKey.generate()

    def get_public_key(self) -> str:
        """Return base64-encoded X25519 public key for handshake."""
        if not self.enabled or not self._private_key:
            return ""
        pub = self._private_key.public_key()
        raw = pub.public_bytes_raw()
        return base64.b64encode(raw).decode()

    def get_fingerprint(self) -> str:
        """Return SHA-256 fingerprint of X25519 public key as colon-separated hex.

        Returns empty string if encryption is disabled or no keypair exists.
        Format matches SSH-style fingerprint for user-friendly comparison.
        """
        if not self.enabled or not self._private_key:
            return ""
        pub = self._private_key.public_key()
        raw = pub.public_bytes_raw()
        digest = hashlib.sha256(raw).hexdigest()
        return ':'.join(digest[i:i+2] for i in range(0, len(digest), 2))

    def derive_shared(self, peer_pubkey_b64: str):
        """Derive shared key from peer's base64-encoded public key via X25519 + HKDF."""
        if not self.enabled or not self._private_key:
            return
        try:
            raw = base64.b64decode(peer_pubkey_b64)
            peer_pub = x25519.X25519PublicKey.from_public_bytes(raw)
            shared = self._private_key.exchange(peer_pub)

            hkdf = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=None,
                info=b'clchat-p2p-v2',
            )
            self._shared_key = hkdf.derive(shared)
        except binascii.Error as e:
            logger.error("Invalid base64 encoding in peer public key: %s", e)
            self._shared_key = None
        except ValueError as e:
            logger.error("Invalid public key bytes from peer: %s", e)
            self._shared_key = None
        except Exception as e:
            logger.error("Key derivation failed: %s", e)
            self._shared_key = None

    @property
    def ready(self) -> bool:
        return self.enabled and self._shared_key is not None

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext with ChaCha20-Poly1305.

        Returns base64(nonce + ciphertext) or raw input if crypto disabled.
        """
        if not self.ready:
            return plaintext
        nonce = os.urandom(12)
        chacha = ChaCha20Poly1305(self._shared_key)
        ct = chacha.encrypt(nonce, plaintext.encode('utf-8'), None)
        return base64.b64encode(nonce + ct).decode()

    def decrypt(self, payload: str):
        """Decrypt base64(nonce + ciphertext) via ChaCha20-Poly1305.

        Returns plaintext string, None on failure, or raw input if crypto disabled.
        """
        if not self.enabled:
            return payload
        if not self._shared_key:
            return payload
        try:
            raw = base64.b64decode(payload)
            nonce, ct = raw[:12], raw[12:]
            chacha = ChaCha20Poly1305(self._shared_key)
            pt = chacha.decrypt(nonce, ct, None)
            return pt.decode('utf-8')
        except Exception:
            return None
