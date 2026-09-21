import uuid
from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))

    # Localization — picked by the user at signup, never assumed.
    base_currency_code: Mapped[str] = mapped_column(ForeignKey("currencies.code"))
    locale: Mapped[str] = mapped_column(String(16), default="en-US")  # BCP-47
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")  # IANA tz

    default_reminder_days_before: Mapped[int] = mapped_column(Integer, default=3)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
