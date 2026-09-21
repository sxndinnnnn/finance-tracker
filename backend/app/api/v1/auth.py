from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.currency import Currency
from app.models.user import User
from app.schemas.user import (
    RefreshRequest,
    Token,
    UserCreate,
    UserLogin,
    UserRead,
    UserUpdate,
)

router = APIRouter()


def _issue_tokens(user_id) -> Token:
    subject = str(user_id)
    return Token(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
    )


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")

    currency_code = payload.base_currency_code.upper()
    currency = await db.get(Currency, currency_code)
    if currency is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown base_currency_code")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        base_currency_code=currency_code,
        locale=payload.locale,
        timezone=payload.timezone,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return _issue_tokens(user.id)


@router.post("/login", response_model=Token)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")

    return _issue_tokens(user.id)


@router.post("/refresh", response_model=Token)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    import uuid as _uuid

    subject = decode_token(payload.refresh_token, expected_type="refresh")
    if subject is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")

    try:
        user_id = _uuid.UUID(subject)
    except ValueError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")

    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")

    return _issue_tokens(user.id)


@router.get("/me", response_model=UserRead)
async def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserRead)
async def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = payload.model_dump(exclude_unset=True)

    if "base_currency_code" in data and data["base_currency_code"] is not None:
        code = data["base_currency_code"].upper()
        currency = await db.get(Currency, code)
        if currency is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown base_currency_code")
        data["base_currency_code"] = code

    for field, value in data.items():
        setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)
    return current_user
