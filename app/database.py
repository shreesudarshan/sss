import asyncio
import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import Column, Integer, String, ForeignKey, Index, text
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from typing import List, Optional
from app import logger
import os

Base = declarative_base()

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    ciphertext = Column(String, nullable=False)
    iv = Column(String, nullable=False)
    tag = Column(String, nullable=False)

class SearchToken(Base):
    __tablename__ = "search_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    token = Column(String, nullable=False, index=True)
    
    patient = relationship("Patient", back_populates="tokens")

Patient.tokens = relationship("SearchToken", cascade="all, delete-orphan")

DATABASE_URL = "sqlite+aiosqlite:///secure.db"
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db() -> None:
    """Initialize database and create tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Create indexes for performance
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tokens_token ON search_tokens(token)"))
        logger.info("Database initialized")

async def get_session() -> AsyncSession:
    """Get database session."""
    async with AsyncSessionLocal() as session:
        yield session

async def insert_patient(
    session: AsyncSession,
    ciphertext: str,
    iv: str,
    tag: str,
    tokens: List[str]
) -> int:
    """Insert patient record and search tokens."""
    async with session.begin():
        patient = Patient(ciphertext=ciphertext, iv=iv, tag=tag)
        session.add(patient)
        await session.flush()
        
        for token in tokens:
            search_token = SearchToken(patient_id=patient.id, token=token)
            session.add(search_token)
        
        await session.flush()
        patient_id = patient.id
        await session.commit()
        return patient_id

async def search_patients(
    session: AsyncSession,
    tokens: List[str]
) -> List[int]:
    """Search patients by HMAC tokens."""
    if not tokens:
        return []
    
    token_list = "'" + "', '".join(tokens) + "'"
    result = await session.execute(
        text(f"""
            SELECT DISTINCT patient_id 
            FROM search_tokens 
            WHERE token IN ({token_list})
        """)
    )
    return [row[0] for row in result.fetchall()]

async def get_patient(
    session: AsyncSession,
    patient_id: int
) -> Optional[Patient]:
    """Fetch patient by ID."""
    result = await session.get(Patient, patient_id)
    return result
