import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.account import Account
from app.models.category import Category
from app.models.credit_card import CreditCard
from app.models.currency import Currency
from app.models.recurrence import RecurrenceRule
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.recurrence import RecurrenceRuleRead
from app.schemas.subscription import SubscriptionCreate, SubscriptionRead, SubscriptionUpdate

router = APIRouter()


async def _validate_links(db: AsyncSession, user: User, payload) -> None:
    if payload.linked_credit_card_id is not None:
        card = await db.get(CreditCard, payload.linked_credit_card_id)
        if card is None or card.user_id != user.id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown linked_credit_card_id")
    if payload.linked_account_id is not None:
        account = await db.get(Account, payload.linked_account_id)
        if account is None or account.user_id != user.id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown linked_account_id")
    if payload.category_id is not None:
        category = await db.get(Category, payload.category_id)
        if category is None or (category.user_id is not None and category.user_id != user.id):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown category_id")


async def _to_read(db: AsyncSession, sub: Subscription) -> SubscriptionRead:
    rule = await db.get(RecurrenceRule, sub.billing_recurrence_rule_id)
    return SubscriptionRead(
        **{c.name: getattr(sub, c.name) for c in Subscription.__table__.columns},
        recurrence=RecurrenceRuleRead.model_validate(rule) if rule else None,
    )


@router.get("", response_model=list[SubscriptionRead])
async def list_subscriptions(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user.id).order_by(Subscription.next_billing_date)
    )
    return [await _to_read(db, sub) for sub in result.scalars().all()]


@router.post("", response_model=SubscriptionRead, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    payload: SubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _validate_links(db, current_user, payload)
    currency_code = payload.currency_code.upper()
    if await db.get(Currency, currency_code) is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown currency_code")

    rule_data = payload.recurrence.model_dump()
    rule_data["start_date"] = payload.next_billing_date
    rule = RecurrenceRule(**rule_data)
    db.add(rule)
    await db.flush()

    sub = Subscription(
        user_id=current_user.id,
        name=payload.name,
        amount_minor=payload.amount_minor,
        currency_code=currency_code,
        billing_recurrence_rule_id=rule.id,
        next_billing_date=payload.next_billing_date,
        linked_credit_card_id=payload.linked_credit_card_id,
        linked_account_id=payload.linked_account_id,
        category_id=payload.category_id,
        reminder_days_before=payload.reminder_days_before,
        is_active=payload.is_active,
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return await _to_read(db, sub)


async def _get_own_subscription(db: AsyncSession, sub_id: uuid.UUID, user: User) -> Subscription:
    sub = await db.get(Subscription, sub_id)
    if sub is None or sub.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Subscription not found")
    return sub


@router.get("/{subscription_id}", response_model=SubscriptionRead)
async def get_subscription(
    subscription_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_own_subscription(db, subscription_id, current_user)
    return await _to_read(db, sub)


@router.patch("/{subscription_id}", response_model=SubscriptionRead)
async def update_subscription(
    subscription_id: uuid.UUID,
    payload: SubscriptionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_own_subscription(db, subscription_id, current_user)
    await _validate_links(db, current_user, payload)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(sub, field, value)
    await db.commit()
    await db.refresh(sub)
    return await _to_read(db, sub)


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(
    subscription_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_own_subscription(db, subscription_id, current_user)
    await db.delete(sub)
    await db.commit()
