import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.recurrence import RecurrenceRuleCreate, RecurrenceRuleRead


class LeaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    asset_description: str | None = Field(default=None, max_length=255)
    lessor: str = Field(min_length=1, max_length=128)
    monthly_payment_minor: int = Field(gt=0)
    currency_code: str = Field(min_length=3, max_length=3)
    start_date: date
    end_date: date | None = None
    linked_account_id: uuid.UUID
    recurrence: RecurrenceRuleCreate


class LeaseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    asset_description: str | None = Field(default=None, max_length=255)
    lessor: str | None = Field(default=None, min_length=1, max_length=128)
    end_date: date | None = None


class LeaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    asset_description: str | None
    lessor: str
    monthly_payment_minor: int
    currency_code: str
    start_date: date
    end_date: date | None
    payment_recurrence_rule_id: uuid.UUID
    linked_account_id: uuid.UUID
    recurrence: RecurrenceRuleRead | None = None
