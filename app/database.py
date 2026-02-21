"""Database models and async session management.

This module defines all persistent tables and provides shared helpers:
- `init_db` to create tables at startup
- `get_session` to inject SQLAlchemy async sessions into routes
"""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app import logger
from app.settings import get_settings


class Base(DeclarativeBase):
    """Base declarative model class used by all ORM tables."""

    pass


class User(Base):
    """Registered user account."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    sessions: Mapped[list["Session"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    patients: Mapped[list["Patient"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class Session(Base):
    """Persisted login session for logout/revocation support."""

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_token_hash: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="sessions")


class Patient(Base):
    """Encrypted patient record owned by one user."""

    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    iv: Mapped[str] = mapped_column(String(255), nullable=False)
    tag: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    owner: Mapped[User] = relationship(back_populates="patients")
    tokens: Mapped[list["SearchToken"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )


class SearchToken(Base):
    """Blind-index token row used for patient search."""

    __tablename__ = "search_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    patient: Mapped[Patient] = relationship(back_populates="tokens")


Index("idx_search_tokens_token", SearchToken.token)
Index("idx_sessions_user_expires", Session.user_id, Session.expires_at)

settings = get_settings()
engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

_db_ready = False
_db_error: str | None = None


def _format_db_error(exc: Exception) -> str:
    """Normalize DB connection/setup failures into one actionable message."""
    error_text = str(exc).lower()
    if "password authentication failed" in error_text or "invalidpassworderror" in error_text:
        return (
            "Database authentication failed. Update DATABASE_URL in .env with the correct "
            "PostgreSQL username/password."
        )
    if "connection refused" in error_text or "could not connect" in error_text:
        return (
            "Database connection failed. Ensure PostgreSQL is running and DATABASE_URL points "
            "to the correct host/port."
        )
    return "Database initialization failed. Verify DATABASE_URL and PostgreSQL availability."


def get_database_status() -> tuple[bool, str | None]:
    """Expose database readiness and last known error for health checks."""
    return _db_ready, _db_error


async def init_db() -> None:
    """Create tables and indexes if they do not already exist."""
    global _db_ready, _db_error
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        _db_ready = True
        _db_error = None
        logger.info("Database initialized")
    except Exception as exc:
        _db_ready = False
        _db_error = _format_db_error(exc)
        logger.error(_db_error)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield one async DB session per request."""
    global _db_ready, _db_error
    if not _db_ready and _db_error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=_db_error)

    async with AsyncSessionLocal() as session:
        try:
            # Fail fast with a friendly error if DB becomes unavailable.
            await session.execute(text("SELECT 1"))
        except SQLAlchemyError as exc:
            _db_ready = False
            _db_error = _format_db_error(exc)
            logger.error(_db_error)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=_db_error,
            ) from exc
        yield session
