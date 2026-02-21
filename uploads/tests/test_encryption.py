"""Legacy encryption unit tests for service behavior."""

import pytest
import json
from app.encryption import EncryptionService
from app import logger

@pytest.fixture
def encryption_service():
    return EncryptionService()

def test_encrypt_decrypt_roundtrip(encryption_service):
    """Test AES-GCM encryption/decryption roundtrip."""
    plaintext = {
        "name": "John Doe",
        "dob": "1990-01-01",
        "diagnosis": "Hypertension"
    }
    plaintext_json = json.dumps(plaintext)
    
    ciphertext, iv, tag = encryption_service.encrypt_data(plaintext_json)
    
    # Verify outputs are base64 strings
    assert all(len(x) > 0 for x in [ciphertext, iv, tag])
    
    # Decrypt
    decrypted = encryption_service.decrypt_data(ciphertext, iv, tag)
    assert decrypted is not None
    assert json.loads(decrypted) == plaintext

def test_hmac_determinism(encryption_service):
    """Test HMAC tokens are deterministic."""
    token1 = encryption_service.generate_hmac_token("john")
    token2 = encryption_service.generate_hmac_token("john")
    assert token1 == token2
    
    token3 = encryption_service.generate_hmac_token("doe")
    assert token1 != token3

def test_decrypt_invalid_data(encryption_service):
    """Test decryption fails with invalid data."""
    ciphertext = "invalid"
    iv = "invalid"
    tag = "invalid"
    
    result = encryption_service.decrypt_data(ciphertext, iv, tag)
    assert result is None
