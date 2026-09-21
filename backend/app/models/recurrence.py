"""
One generic recurrence table shared by transactions, loans, leases, and
subscriptions. Expand it with python-dateutil.rrule (or the raw
rrule_string) in app/services — don't re-implement "monthly" logic per model.
"""
import uuid
import enum
from datetime import date

from sqlalchemy import String, Integer, Enum, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Frequency(str, enum.Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"
    custom = "custom"  # use rrule_string


class RecurrenceRule(Base):
    __tablename__ = "recurrence_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    frequency: Mapped[Frequency] = mapped_column(Enum(Frequency))
    interval: Mapped[int] = mapped_column(Integer, default=1)
    by_weekday: Mapped[str | None] = mapped_column(String(32), nullable=True)   # e.g. "MO,WE,FR"
    by_monthday: Mapped[int | None] = mapped_column(Integer, nullable=True)     # e.g. 15
    rrule_string: Mapped[str | None] = mapped_column(String(255), nullable=True)  # raw RFC 5545 escape hatch
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
