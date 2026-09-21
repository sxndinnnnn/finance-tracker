import uuid

from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CreditCard(Base):
    __tablename__ = "credit_cards"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    # 1:1 with an Account row (type=credit_card); this table adds the
    # card-specific fields that a plain account doesn't need.
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), unique=True)

    card_name: Mapped[str] = mapped_column(String(128))
    # Free text, not an enum — card networks/schemes vary by country and
    # issuer far more than a fixed dropdown could cover.
    network: Mapped[str | None] = mapped_column(String(64), nullable=True)

    credit_limit_minor: Mapped[int] = mapped_column(Integer)
    statement_day: Mapped[int] = mapped_column(Integer)  # day-of-month, 1-31
    due_day: Mapped[int] = mapped_column(Integer)
    current_balance_minor: Mapped[int] = mapped_column(Integer, default=0)
