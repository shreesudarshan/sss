"""Patient API routes.

This file handles encrypted patient create/search/read operations and ensures
all operations are scoped to the authenticated user.
"""

import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import distinct, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth_routes import get_current_user
from app.database import Patient, SearchToken, User, get_session
from app.encryption import EncryptionService
from app.utils import generate_trigrams

router = APIRouter(prefix="/patients", tags=["patients"])

encryption_service = EncryptionService()


class PatientCreate(BaseModel):
    """Payload for creating a patient record."""

    name: str = Field(min_length=1, max_length=255)
    dob: str = Field(min_length=4, max_length=20)
    diagnosis: str = Field(min_length=1, max_length=255)


class PatientResponse(BaseModel):
    """Decrypted patient data sent back to client."""

    id: int
    name: str
    dob: str
    diagnosis: str


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient_data: PatientCreate,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> dict[str, int]:
    """Encrypt and persist one patient record with searchable tokens."""
    plaintext = json.dumps(patient_data.model_dump())
    ciphertext, iv, tag = encryption_service.encrypt_data(plaintext)

    patient = Patient(
        owner_user_id=user.id,
        ciphertext=ciphertext,
        iv=iv,
        tag=tag,
    )
    db.add(patient)
    await db.flush()

    searchable_text = f"{patient_data.name} {patient_data.diagnosis}"
    trigrams = generate_trigrams(searchable_text)
    hmac_tokens = [encryption_service.generate_hmac_token(trigram) for trigram in trigrams]

    db.add_all([SearchToken(patient_id=patient.id, token=token) for token in hmac_tokens])
    await db.commit()
    return {"patient_id": patient.id}


@router.get("/search", response_model=list[PatientResponse])
async def search_patient_records(
    query: str = Query(..., min_length=1, max_length=255),
    db: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> list[PatientResponse]:
    """Search current user's patients by blind-index token matches."""
    trigrams = generate_trigrams(query)
    if not trigrams:
        return []

    hmac_tokens = [encryption_service.generate_hmac_token(trigram) for trigram in trigrams]
    result = await db.execute(
        select(distinct(Patient.id))
        .join(SearchToken, SearchToken.patient_id == Patient.id)
        .where(Patient.owner_user_id == user.id)
        .where(SearchToken.token.in_(hmac_tokens))
    )
    patient_ids = [row[0] for row in result.fetchall()]
    if not patient_ids:
        return []

    records = await db.execute(
        select(Patient)
        .where(Patient.owner_user_id == user.id)
        .where(Patient.id.in_(patient_ids))
        .order_by(Patient.id.desc())
    )
    patients = records.scalars().all()

    response: list[PatientResponse] = []
    for patient in patients:
        decrypted = encryption_service.decrypt_data(patient.ciphertext, patient.iv, patient.tag)
        if not decrypted:
            continue
        data = json.loads(decrypted)
        response.append(PatientResponse(id=patient.id, **data))
    return response


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient_record(
    patient_id: int,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> PatientResponse:
    """Fetch one patient by ID for the current user and decrypt it."""
    result = await db.execute(
        select(Patient)
        .where(Patient.id == patient_id)
        .where(Patient.owner_user_id == user.id)
    )
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    decrypted = encryption_service.decrypt_data(patient.ciphertext, patient.iv, patient.tag)
    if not decrypted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decrypt patient data",
        )
    data = json.loads(decrypted)
    return PatientResponse(id=patient.id, **data)
