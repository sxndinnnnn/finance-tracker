import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.account import AccountRead
from app.schemas.subscription import SubscriptionRead


class CreditCardCreate(BaseModel):
    card_name: str = Field(min_length=1, max_length=128)
    network: str | None = Field(default=None, max_length=64)
    currency_code: str = Field(min_length=3, max_length=3)
    credit_limit_minor: int = Field(ge=0)
    statement_day: int = Field(ge=1, le=31)
    due_day: int = Field(ge=1, le=31)


class CreditCardUpdate(BaseModel):
    card_name: str | None = Field(default=None, min_length=1, max_length=128)
    network: str | None = Field(default=None, max_length=64)
    credit_limit_minor: int | None = Field(default=None, ge=0)
    statement_day: int | None = Field(default=None, ge=1, le=31)
    due_day: int | None = Field(default=None, ge=1, le=31)


class CreditCardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    account_id: uuid.UUID
    card_name: str
    network: str | None
    credit_limit_minor: int
    statement_day: int
    due_day: int
    current_balance_minor: int
    account: AccountRead
    # "which card is this subscription on" at a glance, and every
    # subscription that needs a new card if this one gets cancelled.
    linked_subscriptions: list[SubscriptionRead] = []
