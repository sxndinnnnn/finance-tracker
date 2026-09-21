"""Password hashing + JWT helpers."""
from datetime import datetime, timedelta, timezone
from typing import Literal

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TokenType = Literal["access", "refresh"]


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _create_token(subject: str, token_type: TokenType, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {"sub": subject, "exp": expire, "type": token_type}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    return _create_token(
        subject,
        "access",
        timedelta(minutes=expires_minutes or settings.access_token_expire_minutes),
    )


def create_refresh_token(subject: str, expires_days: int | None = None) -> str:
    return _create_token(
        subject,
        "refresh",
        timedelta(days=expires_days or settings.refresh_token_expire_days),
    )


def decode_token(token: str, expected_type: TokenType) -> str | None:
    """Returns the subject (user id) if the token is valid and of the expected type, else None."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None
    if payload.get("type") != expected_type:
        return None
    subject = payload.get("sub")
    return subject if isinstance(subject, str) else None
