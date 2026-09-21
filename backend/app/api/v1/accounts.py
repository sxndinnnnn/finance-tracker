import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.account import Account, AccountType
from app.models.currency import Currency
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.schemas.account import AccountCreate, AccountRead, AccountUpdate

router = APIRouter()


async def _current_balance_minor(db: AsyncSession, account: Account) -> int:
    """Opening balance plus posted transactions in the account's own currency.

    Transactions booked in a different currency than the account (allowed,
    per CONCEPT.md 3.1) aren't summed here since minor units aren't
    comparable across currencies without a conversion.
    """
    result = await db.execute(
        select(Transaction.type, Transaction.amount_minor).where(
            Transaction.account_id == account.id,
            Transaction.currency_code == account.currency_code,
        )
    )
    balance = account.opening_balance_minor
    for tx_type, amount_minor in result.all():
        balance += amount_minor if tx_type == TransactionType.income else -amount_minor
    return balance


async def _to_read(db: AsyncSession, account: Account) -> AccountRead:
    return AccountRead(
        **{c.name: getattr(account, c.name) for c in Account.__table__.columns},
        current_balance_minor=await _current_balance_minor(db, account),
    )


@router.get("", response_model=list[AccountRead])
async def list_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Account).where(Account.user_id == current_user.id).order_by(Account.created_at)
    )
    return [await _to_read(db, a) for a in result.scalars().all()]


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
async def create_account(
    payload: AccountCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.type == AccountType.credit_card:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Create credit card accounts via POST /credit-cards, not /accounts",
        )

    currency_code = payload.currency_code.upper()
    if await db.get(Currency, currency_code) is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown currency_code")

    account = Account(
        user_id=current_user.id,
        name=payload.name,
        type=payload.type,
        currency_code=currency_code,
        opening_balance_minor=payload.opening_balance_minor,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return await _to_read(db, account)


async def _get_own_account(account_id: uuid.UUID, current_user: User, db: AsyncSession) -> Account:
    account = await db.get(Account, account_id)
    if account is None or account.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Account not found")
    return account


@router.get("/{account_id}", response_model=AccountRead)
async def get_account(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = await _get_own_account(account_id, current_user, db)
    return await _to_read(db, account)


@router.patch("/{account_id}", response_model=AccountRead)
async def update_account(
    account_id: uuid.UUID,
    payload: AccountUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = await _get_own_account(account_id, current_user, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(account, field, value)
    await db.commit()
    await db.refresh(account)
    return await _to_read(db, account)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = await _get_own_account(account_id, current_user, db)
    await db.delete(account)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Account has transactions, loans, or leases linked to it and can't be deleted",
        )
