import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.api.v1.accounts import _current_balance_minor, _to_read as _account_to_read
from app.models.account import Account, AccountType
from app.models.credit_card import CreditCard
from app.models.currency import Currency
from app.models.user import User
from app.schemas.credit_card import CreditCardCreate, CreditCardRead, CreditCardUpdate

router = APIRouter()


async def _to_read(db: AsyncSession, card: CreditCard) -> CreditCardRead:
    account = await db.get(Account, card.account_id)
    balance = await _current_balance_minor(db, account)
    return CreditCardRead(
        id=card.id,
        user_id=card.user_id,
        account_id=card.account_id,
        card_name=card.card_name,
        network=card.network,
        credit_limit_minor=card.credit_limit_minor,
        statement_day=card.statement_day,
        due_day=card.due_day,
        current_balance_minor=balance,
        account=await _account_to_read(db, account),
    )


@router.get("", response_model=list[CreditCardRead])
async def list_credit_cards(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(CreditCard).where(CreditCard.user_id == current_user.id))
    return [await _to_read(db, card) for card in result.scalars().all()]


@router.post("", response_model=CreditCardRead, status_code=status.HTTP_201_CREATED)
async def create_credit_card(
    payload: CreditCardCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    currency_code = payload.currency_code.upper()
    if await db.get(Currency, currency_code) is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown currency_code")

    account = Account(
        user_id=current_user.id,
        name=payload.card_name,
        type=AccountType.credit_card,
        currency_code=currency_code,
        opening_balance_minor=0,
    )
    db.add(account)
    await db.flush()

    card = CreditCard(
        user_id=current_user.id,
        account_id=account.id,
        card_name=payload.card_name,
        network=payload.network,
        credit_limit_minor=payload.credit_limit_minor,
        statement_day=payload.statement_day,
        due_day=payload.due_day,
        current_balance_minor=0,
    )
    db.add(card)
    await db.commit()
    await db.refresh(card)
    return await _to_read(db, card)


async def _get_own_card(db: AsyncSession, card_id: uuid.UUID, user: User) -> CreditCard:
    card = await db.get(CreditCard, card_id)
    if card is None or card.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Credit card not found")
    return card


@router.get("/{card_id}", response_model=CreditCardRead)
async def get_credit_card(
    card_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    card = await _get_own_card(db, card_id, current_user)
    return await _to_read(db, card)


@router.patch("/{card_id}", response_model=CreditCardRead)
async def update_credit_card(
    card_id: uuid.UUID,
    payload: CreditCardUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    card = await _get_own_card(db, card_id, current_user)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(card, field, value)
    if "card_name" in data:
        account = await db.get(Account, card.account_id)
        account.name = data["card_name"]
    await db.commit()
    await db.refresh(card)
    return await _to_read(db, card)


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credit_card(
    card_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    card = await _get_own_card(db, card_id, current_user)
    account = await db.get(Account, card.account_id)
    await db.delete(card)
    await db.flush()
    if account is not None:
        await db.delete(account)
    await db.commit()
