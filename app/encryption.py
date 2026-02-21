import os
import base64
import secrets
from typing import Tuple, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import hmac
from app import logger

class EncryptionService:
    def __init__(self):
        self.aes_key = self._load_aes_key()
        self.hmac_key = self._load_hmac_key()
        self.aesgcm = AESGCM(self.aes_key)

    def _load_aes_key(self) -> bytes:
        """Load and derive AES-256 key from env var."""
        raw_key = os.getenv("AES_KEY").encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"secure_bloom_sse",
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(raw_key))

    def _load_hmac_key(self) -> bytes:
        """Load HMAC key from env var."""
        raw_key = os.getenv("HMAC_KEY").encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"hmac_blind_index",
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(raw_key))

    def encrypt_data(self, plaintext: str) -> Tuple[str, str, str]:
        """
        Encrypt plaintext using AES-256-GCM.
        
        Returns: (ciphertext_b64, iv_b64, tag_b64)
        """
        iv = secrets.token_bytes(12)
        ciphertext = self.aesgcm.encrypt(iv, plaintext.encode(), None)
        return (
            base64.urlsafe_b64encode(ciphertext).decode(),
            base64.urlsafe_b64encode(iv).decode(),
            base64.urlsafe_b64encode(ciphertext[-16:]).decode()
        )

    def decrypt_data(self, ciphertext: str, iv: str, tag: str) -> Optional[str]:
        """
        Decrypt ciphertext using AES-256-GCM.
        
        Returns None if decryption fails.
        """
        try:
            ct = base64.urlsafe_b64decode(ciphertext)
            iv_bytes = base64.urlsafe_b64decode(iv)
            tag_bytes = base64.urlsafe_b64decode(tag)
            return self.aesgcm.decrypt(iv_bytes, ct, tag_bytes).decode()
        except Exception:
            logger.warning("Decryption failed")
            return None

    def generate_hmac_token(self, value: str) -> str:
        """
        Generate deterministic HMAC-SHA256 token for blind indexing.
        """
        h = hmac.new(self.hmac_key, value.encode(), hashes.SHA256())
        return h.digest().hex()
