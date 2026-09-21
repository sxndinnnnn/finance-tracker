"""Shared FastAPI dependencies: current-user resolution, DB session, etc."""
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db  # re-exported for convenience
from app.core.security import decode_token
from app.models.user import User

__all__ = ["get_db", "get_current_user"]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if token is None:
        raise _credentials_exception

    subject = decode_token(token, expected_type="access")
    if subject is None:
        raise _credentials_exception

    try:
        user_id = uuid.UUID(subject)
    except ValueError:
        raise _credentials_exception

    user = await db.get(User, user_id)
    if user is None:
        raise _credentials_exception

    return user
