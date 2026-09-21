import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.recurrence import RecurrenceRuleCreate, RecurrenceRuleRead


class SubscriptionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    amount_minor: int = Field(gt=0)
    currency_code: str = Field(min_length=3, max_length=3)
    next_billing_date: date
    # frequency/interval/etc. — start_date is overridden to next_billing_date
    # server-side so the schedule and the "next bill" field never drift apart.
    recurrence: RecurrenceRuleCreate
    linked_credit_card_id: uuid.UUID | None = None
    linked_account_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    reminder_days_before: int | None = Field(default=None, ge=0, le=365)
    is_active: bool = True


class SubscriptionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    amount_minor: int | None = Field(default=None, gt=0)
    next_billing_date: date | None = None
    linked_credit_card_id: uuid.UUID | None = None
    linked_account_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    reminder_days_before: int | None = Field(default=None, ge=0, le=365)
    is_active: bool | None = None


class SubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    amount_minor: int
    currency_code: str
    billing_recurrence_rule_id: uuid.UUID
    next_billing_date: date
    linked_credit_card_id: uuid.UUID | None
    linked_account_id: uuid.UUID | None
    category_id: uuid.UUID | None
    reminder_days_before: int | None
    is_active: bool
    recurrence: RecurrenceRuleRead | None = None
