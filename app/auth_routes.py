"""Authentication API routes.

Routes in this file implement basic account and session flows:
- register
- login
- logout
- who-am-I (`/auth/me`)
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    generate_session_token,
    get_active_session,
    hash_password,
    hash_session_token,
    normalize_email,
    session_expiry,
    validate_email,
    verify_password,
)
from app.database import Session, User, get_session
from app.settings import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])

SESSION_COOKIE_NAME = "session_token"


class Credentials(BaseModel):
    """Input payload for register and login."""

    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    """Minimal user identity returned to the frontend."""

    id: int
    email: str


def _read_token(request: Request) -> str | None:
    """Read session token from cookie first, then optional bearer header."""
    cookie_token = request.cookies.get(SESSION_COOKIE_NAME)
    if cookie_token:
        return cookie_token
    auth_header = request.headers.get("Authorization", "")
    prefix = "Bearer "
    if auth_header.startswith(prefix):
        return auth_header[len(prefix) :].strip()
    return None


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> User:
    """Resolve authenticated user from session token."""
    token = _read_token(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    active_session, user = await get_active_session(db, token)
    if not active_session or not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    return user


async def get_current_session_token_hash(
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> str:
    """Resolve active session and return its hashed token ID."""
    token = _read_token(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    active_session, _ = await get_active_session(db, token)
    if not active_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    return active_session.session_token_hash


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(credentials: Credentials, db: AsyncSession = Depends(get_session)) -> UserResponse:
    """Create a new user account."""
    email = normalize_email(credentials.email)
    if not validate_email(email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email")

    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    user = User(email=email, password_hash=hash_password(credentials.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserResponse(id=user.id, email=user.email)


@router.post("/login", response_model=UserResponse)
async def login_user(
    credentials: Credentials,
    response: Response,
    db: AsyncSession = Depends(get_session),
) -> UserResponse:
    """Validate credentials, create DB session, and set cookie token."""
    email = normalize_email(credentials.email)
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = generate_session_token()
    token_hash = hash_session_token(token)
    new_session = Session(
        user_id=user.id,
        session_token_hash=token_hash,
        expires_at=session_expiry(),
    )
    db.add(new_session)
    await db.commit()

    settings = get_settings()
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.session_ttl_hours * 3600,
        httponly=True,
        secure=False,
        samesite="lax",
    )
    return UserResponse(id=user.id, email=user.email)


@router.post("/logout")
async def logout_user(
    response: Response,
    token_hash: str = Depends(get_current_session_token_hash),
    db: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Revoke active session and clear auth cookie."""
    result = await db.execute(select(Session).where(Session.session_token_hash == token_hash))
    session = result.scalar_one_or_none()
    if session:
        session.revoked_at = datetime.now(UTC)
    await db.commit()
    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"status": "logged_out"}


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)) -> UserResponse:
    """Return current logged-in user details."""
    return UserResponse(id=user.id, email=user.email)
