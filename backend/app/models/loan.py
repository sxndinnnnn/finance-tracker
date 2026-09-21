import uuid
import enum
from datetime import date

from sqlalchemy import String, Integer, Numeric, Enum, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class InterestType(str, enum.Enum):
    fixed = "fixed"
    variable = "variable"


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(128))
    lender: Mapped[str] = mapped_column(String(128))

    principal_minor: Mapped[int] = mapped_column(Integer)
    currency_code: Mapped[str] = mapped_column(ForeignKey("currencies.code"))
    interest_rate: Mapped[float] = mapped_column(Numeric(6, 3))  # percent
    interest_type: Mapped[InterestType] = mapped_column(Enum(InterestType))
    term_months: Mapped[int] = mapped_column(Integer)
    start_date: Mapped[date] = mapped_column(Date)

    payment_amount_minor: Mapped[int] = mapped_column(Integer)
    payment_recurrence_rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recurrence_rules.id")
    )
    linked_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))

    # Recompute this from posted payments in the service layer rather than
    # letting the frontend edit it directly, so it never drifts.
    remaining_balance_minor: Mapped[int] = mapped_column(Integer)
