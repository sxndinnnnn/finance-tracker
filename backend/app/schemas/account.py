import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.account import AccountType


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    type: AccountType
    currency_code: str = Field(min_length=3, max_length=3)
    opening_balance_minor: int = 0


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    opening_balance_minor: int | None = None


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    type: AccountType
    currency_code: str
    opening_balance_minor: int
    current_balance_minor: int
    created_at: datetime
