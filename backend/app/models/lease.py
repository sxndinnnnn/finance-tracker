import uuid
from datetime import date

from sqlalchemy import String, Integer, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Lease(Base):
    __tablename__ = "leases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(128))
    asset_description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lessor: Mapped[str] = mapped_column(String(128))

    monthly_payment_minor: Mapped[int] = mapped_column(Integer)
    currency_code: Mapped[str] = mapped_column(ForeignKey("currencies.code"))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    payment_recurrence_rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recurrence_rules.id")
    )
    linked_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
