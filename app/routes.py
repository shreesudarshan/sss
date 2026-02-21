from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
from typing import List
from app.encryption import EncryptionService
from app.utils import normalize_string, generate_trigrams
from app.database import insert_patient, search_patients, get_patient
from app.bloom import BloomFilter
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app import logger

router = APIRouter(
    prefix="/patients",
    tags=["patients"],
    responses={404: {"description": "Patient not found"}}
)

encryption_service = EncryptionService()
bloom_filter = BloomFilter(size=50000, hash_count=7)

class PatientCreate(BaseModel):
    name: str
    dob: str
    diagnosis: str

class PatientResponse(BaseModel):
    id: int
    name: str
    dob: str
    diagnosis: str

@router.post("/", response_model=dict, status_code=201)
async def create_patient(
    patient_data: PatientCreate,
    session: AsyncSession = Depends(get_session)
):
    """Create encrypted patient record with searchable tokens."""
    try:
        # Encrypt full patient data
        plaintext = json.dumps(patient_data.dict())
        ciphertext, iv, tag = encryption_service.encrypt_data(plaintext)
        
        # Generate searchable tokens from name + diagnosis
        searchable_text = f"{patient_data.name} {patient_data.diagnosis}"
        trigrams = generate_trigrams(searchable_text)
        hmac_tokens = [encryption_service.generate_hmac_token(trigram) for trigram in trigrams]
        
        # Store in database
        patient_id = await insert_patient(session, ciphertext, iv, tag, hmac_tokens)
        
        # Add to Bloom filter (optional)
        for token in hmac_tokens:
            bloom_filter.add(token)
        
        logger.info(f"Patient {patient_id} created with {len(hmac_tokens)} tokens")
        return {"patient_id": patient_id}
    
    except Exception as e:
        logger.error(f"Error creating patient: {e}")
        raise HTTPException(status_code=400, detail="Failed to create patient")

@router.get("/search")
async def search_patients(
    query: str = Query(..., min_length=1),
    session: AsyncSession = Depends(get_session)
):
    """Search patients by query using HMAC blind indexing."""
    try:
        # Tokenize and generate HMAC tokens
        trigrams = generate_trigrams(query)
        hmac_tokens = [encryption_service.generate_hmac_token(trigram) for trigram in trigrams]
        
        # Find matching patient IDs
        patient_ids = await search_patients(session, hmac_tokens)
        
        # Fetch and decrypt records
        results = []
        for pid in patient_ids:
            patient = await get_patient(session, pid)
            if patient:
                decrypted = encryption_service.decrypt_data(patient.ciphertext, patient.iv, patient.tag)
                if decrypted:
                    results.append(json.loads(decrypted))
        
        logger.info(f"Search '{query}' returned {len(results)} results")
        return results
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=400, detail="Search failed")

@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient_record(
    patient_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Fetch and decrypt specific patient record."""
    try:
        patient = await get_patient(session, patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        decrypted = encryption_service.decrypt_data(patient.ciphertext, patient.iv, patient.tag)
        if not decrypted:
            raise HTTPException(status_code=400, detail="Failed to decrypt record")
        
        data = json.loads(decrypted)
        return PatientResponse(**data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching patient {patient_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch patient")
