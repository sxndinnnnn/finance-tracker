import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.account import Account
from app.models.currency import Currency
from app.models.lease import Lease
from app.models.recurrence import RecurrenceRule
from app.models.user import User
from app.schemas.lease import LeaseCreate, LeaseRead, LeaseUpdate
from app.schemas.recurrence import RecurrenceRuleRead

router = APIRouter()


async def _get_owned_account(db: AsyncSession, account_id: uuid.UUID, user: User) -> Account:
    account = await db.get(Account, account_id)
    if account is None or account.user_id != user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown linked_account_id")
    return account


async def _to_read(db: AsyncSession, lease: Lease) -> LeaseRead:
    rule = await db.get(RecurrenceRule, lease.payment_recurrence_rule_id)
    return LeaseRead(
        **{c.name: getattr(lease, c.name) for c in Lease.__table__.columns},
        recurrence=RecurrenceRuleRead.model_validate(rule) if rule else None,
    )


@router.get("", response_model=list[LeaseRead])
async def list_leases(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Lease).where(Lease.user_id == current_user.id).order_by(Lease.start_date.desc())
    )
    return [await _to_read(db, lease) for lease in result.scalars().all()]


@router.post("", response_model=LeaseRead, status_code=status.HTTP_201_CREATED)
async def create_lease(
    payload: LeaseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_account(db, payload.linked_account_id, current_user)
    currency_code = payload.currency_code.upper()
    if await db.get(Currency, currency_code) is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown currency_code")

    rule = RecurrenceRule(**payload.recurrence.model_dump())
    db.add(rule)
    await db.flush()

    lease = Lease(
        user_id=current_user.id,
        name=payload.name,
        asset_description=payload.asset_description,
        lessor=payload.lessor,
        monthly_payment_minor=payload.monthly_payment_minor,
        currency_code=currency_code,
        start_date=payload.start_date,
        end_date=payload.end_date,
        payment_recurrence_rule_id=rule.id,
        linked_account_id=payload.linked_account_id,
    )
    db.add(lease)
    await db.commit()
    await db.refresh(lease)
    return await _to_read(db, lease)


async def _get_own_lease(db: AsyncSession, lease_id: uuid.UUID, user: User) -> Lease:
    lease = await db.get(Lease, lease_id)
    if lease is None or lease.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lease not found")
    return lease


@router.get("/{lease_id}", response_model=LeaseRead)
async def get_lease(
    lease_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    lease = await _get_own_lease(db, lease_id, current_user)
    return await _to_read(db, lease)


@router.patch("/{lease_id}", response_model=LeaseRead)
async def update_lease(
    lease_id: uuid.UUID,
    payload: LeaseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lease = await _get_own_lease(db, lease_id, current_user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(lease, field, value)
    await db.commit()
    await db.refresh(lease)
    return await _to_read(db, lease)


@router.delete("/{lease_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lease(
    lease_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    lease = await _get_own_lease(db, lease_id, current_user)
    await db.delete(lease)
    await db.commit()
