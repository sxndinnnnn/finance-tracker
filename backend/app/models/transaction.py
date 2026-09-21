import uuid
import enum
from datetime import date

from sqlalchemy import String, Integer, Numeric, Enum, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TransactionType(str, enum.Enum):
    income = "income"
    expense = "expense"


class Classification(str, enum.Enum):
    fixed = "fixed"
    variable = "variable"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id"))

    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType))
    classification: Mapped[Classification] = mapped_column(Enum(Classification))

    amount_minor: Mapped[int] = mapped_column(Integer)
    currency_code: Mapped[str] = mapped_column(ForeignKey("currencies.code"))
    # Frozen at entry time so past reports don't shift when rates move later.
    exchange_rate_to_base: Mapped[float | None] = mapped_column(Numeric(18, 8), nullable=True)

    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    transaction_date: Mapped[date] = mapped_column(Date)

    # Set only for fixed/recurring items; the recurrence service generates
    # future instances and stamps parent_transaction_id back to the template.
    recurrence_rule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recurrence_rules.id"), nullable=True
    )
    parent_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=True
    )
