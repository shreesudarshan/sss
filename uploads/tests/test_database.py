"""Legacy database workflow tests kept for reference."""

import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import init_db, get_session, insert_patient, search_patients, get_patient, Patient
from app.encryption import EncryptionService
from app.utils import generate_trigrams

@pytest.fixture(scope="session")
async def setup_db():
    await init_db()
    yield
    # Note: SQLite in-memory would be ideal but using file for persistence in tests

@pytest.mark.asyncio
async def test_insert_search_retrieve(setup_db):
    """Test complete insert -> search -> retrieve workflow."""
    async for session in get_session():
        # Create patient
        encryption = EncryptionService()
        plaintext = '{"name": "John Doe", "dob": "1990-01-01", "diagnosis": "flu"}'
        ciphertext, iv, tag = encryption.encrypt_data(plaintext)
        
        searchable_text = "John Doe flu"
        trigrams = generate_trigrams(searchable_text)
        hmac_tokens = [encryption.generate_hmac_token(t) for t in trigrams]
        
        patient_id = await insert_patient(session, ciphertext, iv, tag, hmac_tokens)
        assert patient_id > 0
        
        # Search
        search_tokens = [encryption.generate_hmac_token(t) for t in generate_trigrams("john flu")]
        found_ids = await search_patients(session, search_tokens)
        assert patient_id in found_ids
        
        # Retrieve
        patient = await get_patient(session, patient_id)
        assert patient is not None
        assert patient.id == patient_id

@pytest.mark.asyncio
async def test_search_no_results(setup_db):
    """Test search returns empty when no matches."""
    async for session in get_session():
        empty_tokens = []
        result = await search_patients(session, empty_tokens)
        assert result == []
        
        no_match_tokens = ["nonexistenttoken123"]
        result = await search_patients(session, no_match_tokens)
        assert result == []
