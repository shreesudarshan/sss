"""Authentication helpers.

This module contains reusable logic for:
- email normalization and validation
- password hashing/verification
- session token generation and token hashing
- active session lookup
"""

import hashlib
import hmac
import re
import secrets
from datetime import UTC, datetime, timedelta

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Session, User
from app.settings import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def normalize_email(email: str) -> str:
    """Trim spaces around user-provided email input."""
    return email.strip()


def validate_email(email: str) -> bool:
    """Validate email with a simple practical regex."""
    return bool(EMAIL_PATTERN.match(normalize_email(email)))


def hash_password(password: str) -> str:
    """Hash user password before storing it in database."""
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify plain password against a stored hash."""
    return pwd_context.verify(password, password_hash)


def generate_session_token() -> str:
    """Generate random opaque token sent to client."""
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    """Hash session token for storage so raw token is never persisted."""
    app_secret = get_settings().app_secret.encode("utf-8")
    return hmac.new(app_secret, token.encode("utf-8"), hashlib.sha256).hexdigest()


def session_expiry() -> datetime:
    """Compute session expiration timestamp from configured TTL."""
    ttl = get_settings().session_ttl_hours
    return datetime.now(UTC) + timedelta(hours=ttl)


async def get_active_session(
    db: AsyncSession, token: str
) -> tuple[Session, User] | tuple[None, None]:
    """Return active non-revoked, non-expired session and related user."""
    token_hash = hash_session_token(token)
    now = datetime.now(UTC)

    result = await db.execute(
        select(Session, User)
        .join(User, User.id == Session.user_id)
        .where(Session.session_token_hash == token_hash)
        .where(Session.revoked_at.is_(None))
        .where(Session.expires_at > now)
    )
    row = result.first()
    if not row:
        return None, None
    return row[0], row[1]
