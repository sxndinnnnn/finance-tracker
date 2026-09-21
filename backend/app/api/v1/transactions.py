import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.account import Account
from app.models.category import Category
from app.models.currency import Currency
from app.models.recurrence import RecurrenceRule
from app.models.transaction import Classification, Transaction
from app.models.user import User
from app.schemas.recurrence import RecurrenceRuleRead
from app.schemas.transaction import TransactionCreate, TransactionRead, TransactionUpdate
from app.services.recurrence_service import next_occurrences

router = APIRouter()

# How many future instances of a fixed/recurring transaction to materialize
# up front. Keeps the "generate the next N occurrences" requirement bounded
# instead of expanding a rule indefinitely.
GENERATED_OCCURRENCES = 12


async def _to_read(db: AsyncSession, tx: Transaction) -> TransactionRead:
    recurrence = None
    if tx.recurrence_rule_id:
        rule = await db.get(RecurrenceRule, tx.recurrence_rule_id)
        if rule:
            recurrence = RecurrenceRuleRead.model_validate(rule)
    return TransactionRead(
        **{c.name: getattr(tx, c.name) for c in Transaction.__table__.columns},
        recurrence=recurrence,
    )


async def _get_owned_account(db: AsyncSession, account_id: uuid.UUID, user: User) -> Account:
    account = await db.get(Account, account_id)
    if account is None or account.user_id != user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown account_id")
    return account


async def _get_visible_category(db: AsyncSession, category_id: uuid.UUID, user: User) -> Category:
    category = await db.get(Category, category_id)
    if category is None or (category.user_id is not None and category.user_id != user.id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown category_id")
    return category


@router.get("", response_model=list[TransactionRead])
async def list_transactions(
    account_id: uuid.UUID | None = None,
    category_id: uuid.UUID | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Transaction).where(Transaction.user_id == current_user.id)
    if account_id is not None:
        stmt = stmt.where(Transaction.account_id == account_id)
    if category_id is not None:
        stmt = stmt.where(Transaction.category_id == category_id)
    if from_date is not None:
        stmt = stmt.where(Transaction.transaction_date >= from_date)
    if to_date is not None:
        stmt = stmt.where(Transaction.transaction_date <= to_date)
    stmt = stmt.order_by(Transaction.transaction_date.desc())

    result = await db.execute(stmt)
    return [await _to_read(db, tx) for tx in result.scalars().all()]


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    payload: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = await _get_owned_account(db, payload.account_id, current_user)
    category = await _get_visible_category(db, payload.category_id, current_user)
    if category.kind.value != payload.type.value:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Category kind ({category.kind.value}) doesn't match transaction type ({payload.type.value})",
        )

    currency_code = (payload.currency_code or account.currency_code).upper()
    if await db.get(Currency, currency_code) is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown currency_code")

    tx = Transaction(
        user_id=current_user.id,
        account_id=account.id,
        category_id=category.id,
        type=payload.type,
        classification=payload.classification,
        amount_minor=payload.amount_minor,
        currency_code=currency_code,
        exchange_rate_to_base=payload.exchange_rate_to_base,
        description=payload.description,
        transaction_date=payload.transaction_date,
    )
    db.add(tx)
    await db.flush()

    if payload.classification == Classification.fixed:
        rule = RecurrenceRule(**payload.recurrence.model_dump())
        db.add(rule)
        await db.flush()
        tx.recurrence_rule_id = rule.id

        occurrences = next_occurrences(
            rule, after=payload.transaction_date + timedelta(days=1), count=GENERATED_OCCURRENCES
        )
        for occ_date in occurrences:
            db.add(
                Transaction(
                    user_id=current_user.id,
                    account_id=account.id,
                    category_id=category.id,
                    type=payload.type,
                    classification=Classification.fixed,
                    amount_minor=payload.amount_minor,
                    currency_code=currency_code,
                    exchange_rate_to_base=payload.exchange_rate_to_base,
                    description=payload.description,
                    transaction_date=occ_date,
                    recurrence_rule_id=rule.id,
                    parent_transaction_id=tx.id,
                )
            )

    await db.commit()
    await db.refresh(tx)
    return await _to_read(db, tx)


async def _get_own_transaction(db: AsyncSession, tx_id: uuid.UUID, user: User) -> Transaction:
    tx = await db.get(Transaction, tx_id)
    if tx is None or tx.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaction not found")
    return tx


@router.get("/{transaction_id}", response_model=TransactionRead)
async def get_transaction(
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tx = await _get_own_transaction(db, transaction_id, current_user)
    return await _to_read(db, tx)


@router.patch("/{transaction_id}", response_model=TransactionRead)
async def update_transaction(
    transaction_id: uuid.UUID,
    payload: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tx = await _get_own_transaction(db, transaction_id, current_user)
    data = payload.model_dump(exclude_unset=True)

    if "category_id" in data:
        category = await _get_visible_category(db, data["category_id"], current_user)
        if category.kind.value != tx.type.value:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Category kind doesn't match transaction type")

    for field, value in data.items():
        setattr(tx, field, value)

    await db.commit()
    await db.refresh(tx)
    return await _to_read(db, tx)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tx = await _get_own_transaction(db, transaction_id, current_user)

    # Deleting a recurring template also cancels its not-yet-occurred
    # generated instances; past instances stay since they already happened.
    today = date.today()
    result = await db.execute(
        select(Transaction).where(
            Transaction.parent_transaction_id == tx.id,
            Transaction.transaction_date >= today,
        )
    )
    for future_instance in result.scalars().all():
        await db.delete(future_instance)

    await db.delete(tx)
    await db.commit()
