import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.models.loan import InterestType
from app.schemas.recurrence import RecurrenceRuleCreate, RecurrenceRuleRead


class LoanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    lender: str = Field(min_length=1, max_length=128)
    principal_minor: int = Field(gt=0)
    currency_code: str = Field(min_length=3, max_length=3)
    interest_rate: float = Field(ge=0)
    interest_type: InterestType
    term_months: int = Field(gt=0)
    start_date: date
    payment_amount_minor: int = Field(gt=0)
    linked_account_id: uuid.UUID
    recurrence: RecurrenceRuleCreate


class LoanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    lender: str | None = Field(default=None, min_length=1, max_length=128)
    interest_rate: float | None = Field(default=None, ge=0)
    interest_type: InterestType | None = None


class LoanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    lender: str
    principal_minor: int
    currency_code: str
    interest_rate: float
    interest_type: InterestType
    term_months: int
    start_date: date
    payment_amount_minor: int
    payment_recurrence_rule_id: uuid.UUID
    linked_account_id: uuid.UUID
    remaining_balance_minor: int
    recurrence: RecurrenceRuleRead | None = None
