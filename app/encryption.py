"""Encryption and blind-index token utilities.

We use AES-GCM for patient payload encryption and HMAC-SHA256 for deterministic
search tokens generated from trigrams.
"""

import base64
import hashlib
import hmac
import secrets
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app import logger
from app.settings import get_settings


class EncryptionService:
    """Encapsulates encryption/decryption and token generation logic."""

    def __init__(self) -> None:
        settings = get_settings()
        # Derive fixed-size keys from env values.
        self.aes_key = hashlib.sha256(settings.aes_key.encode("utf-8")).digest()
        self.hmac_key = hashlib.sha256(settings.hmac_key.encode("utf-8")).digest()
        self.aesgcm = AESGCM(self.aes_key)

    def encrypt_data(self, plaintext: str) -> tuple[str, str, str]:
        """Encrypt plaintext and return base64 ciphertext, iv, and tag."""
        iv = secrets.token_bytes(12)
        encrypted = self.aesgcm.encrypt(iv, plaintext.encode("utf-8"), None)
        ciphertext = encrypted[:-16]
        tag = encrypted[-16:]
        return (
            base64.urlsafe_b64encode(ciphertext).decode("utf-8"),
            base64.urlsafe_b64encode(iv).decode("utf-8"),
            base64.urlsafe_b64encode(tag).decode("utf-8"),
        )

    def decrypt_data(self, ciphertext: str, iv: str, tag: str) -> Optional[str]:
        """Decrypt previously encrypted payload; return None when invalid."""
        try:
            ct = base64.urlsafe_b64decode(ciphertext.encode("utf-8"))
            iv_bytes = base64.urlsafe_b64decode(iv.encode("utf-8"))
            tag_bytes = base64.urlsafe_b64decode(tag.encode("utf-8"))
            decrypted = self.aesgcm.decrypt(iv_bytes, ct + tag_bytes, None)
            return decrypted.decode("utf-8")
        except Exception:
            logger.warning("Decryption failed")
            return None

    def generate_hmac_token(self, value: str) -> str:
        """Generate deterministic token for searchable indexing."""
        return hmac.new(self.hmac_key, value.encode("utf-8"), hashlib.sha256).hexdigest()
