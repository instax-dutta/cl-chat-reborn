#!/usr/bin/env python3
"""
Encryption module for Confluxus
Provides end-to-end encryption for secure messaging.
"""

import os
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Optional, Tuple

class ChatEncryption:
    def __init__(self, password: str = None):
        """
        Initialize encryption with optional password.
        If no password provided, generates a random one.
        """
        if password:
            self.password = password.encode()
        else:
            # Generate a random password if none provided
            self.password = os.urandom(32)
        
        self.salt = os.urandom(16)
        self.key = self._derive_key(self.password, self.salt)
        self.cipher = Fernet(self.key)
        
    def _derive_key(self, password: bytes, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def encrypt_message(self, message: str) -> str:
        """Encrypt a message and return base64 encoded string."""
        try:
            encrypted_data = self.cipher.encrypt(message.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            print(f"❌ Encryption error: {e}")
            return message  # Fallback to plain text
    
    def decrypt_message(self, encrypted_message: str) -> str:
        """Decrypt a base64 encoded encrypted message."""
        try:
            # Check if message is encrypted (base64 format)
            if not self._is_base64(encrypted_message):
                return encrypted_message  # Return as-is if not encrypted
                
            encrypted_data = base64.urlsafe_b64decode(encrypted_message.encode('utf-8'))
            decrypted_data = self.cipher.decrypt(encrypted_data)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            print(f"❌ Decryption error: {e}")
            return encrypted_message  # Return encrypted message if decryption fails
    
    def _is_base64(self, s: str) -> bool:
        """Check if string is valid base64."""
        try:
            base64.urlsafe_b64decode(s.encode('utf-8'))
            return True
        except Exception:
            return False
    
    def get_public_info(self) -> dict:
        """Get public encryption info (salt) for key exchange."""
        return {
            "salt": base64.urlsafe_b64encode(self.salt).decode('utf-8'),
            "encrypted": True
        }
    
    def set_shared_key(self, salt: str):
        """Set shared key using received salt."""
        try:
            self.salt = base64.urlsafe_b64decode(salt.encode('utf-8'))
            self.key = self._derive_key(self.password, self.salt)
            self.cipher = Fernet(self.key)
        except Exception as e:
            print(f"❌ Error setting shared key: {e}")

class EncryptionManager:
    """Manages encryption for the chat application."""
    
    def __init__(self, enable_encryption: bool = True, password: str = None):
        self.enable_encryption = enable_encryption
        self.encryption = None
        
        if enable_encryption:
            self.encryption = ChatEncryption(password)
    
    def encrypt(self, message: str) -> str:
        """Encrypt message if encryption is enabled."""
        if not self.enable_encryption or not self.encryption:
            return message
        return self.encryption.encrypt_message(message)
    
    def decrypt(self, message: str) -> str:
        """Decrypt message if encryption is enabled."""
        if not self.enable_encryption or not self.encryption:
            return message
        return self.encryption.decrypt_message(message)
    
    def get_encryption_info(self) -> dict:
        """Get encryption information for key exchange."""
        if not self.enable_encryption or not self.encryption:
            return {"encrypted": False}
        return self.encryption.get_public_info()
    
    def set_shared_key(self, salt: str):
        """Set shared encryption key."""
        if self.enable_encryption and self.encryption:
            self.encryption.set_shared_key(salt)
