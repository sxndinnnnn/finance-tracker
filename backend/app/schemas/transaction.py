import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.transaction import Classification, TransactionType
from app.schemas.recurrence import RecurrenceRuleCreate, RecurrenceRuleRead


class TransactionCreate(BaseModel):
    account_id: uuid.UUID
    category_id: uuid.UUID
    type: TransactionType
    classification: Classification
    amount_minor: int = Field(gt=0)
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    exchange_rate_to_base: float | None = None
    description: str | None = Field(default=None, max_length=255)
    transaction_date: date
    # Required when classification=fixed; generates a recurrence_rules row
    # plus the next batch of future instances.
    recurrence: RecurrenceRuleCreate | None = None

    @model_validator(mode="after")
    def _fixed_requires_recurrence(self):
        if self.classification == Classification.fixed and self.recurrence is None:
            raise ValueError("recurrence is required when classification is 'fixed'")
        return self


class TransactionUpdate(BaseModel):
    category_id: uuid.UUID | None = None
    amount_minor: int | None = Field(default=None, gt=0)
    description: str | None = Field(default=None, max_length=255)
    transaction_date: date | None = None


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    account_id: uuid.UUID
    category_id: uuid.UUID
    type: TransactionType
    classification: Classification
    amount_minor: int
    currency_code: str
    exchange_rate_to_base: float | None
    description: str | None
    transaction_date: date
    recurrence_rule_id: uuid.UUID | None
    parent_transaction_id: uuid.UUID | None
    recurrence: RecurrenceRuleRead | None = None
