import uuid
import enum
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ReminderChannel(str, enum.Enum):
    email = "email"  # room to add sms/push later without touching the schema shape


class ReminderStatus(str, enum.Enum):
    sent = "sent"
    failed = "failed"


class ReminderLog(Base):
    __tablename__ = "reminder_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subscriptions.id"))
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    channel: Mapped[ReminderChannel] = mapped_column(Enum(ReminderChannel), default=ReminderChannel.email)
    status: Mapped[ReminderStatus] = mapped_column(Enum(ReminderStatus))
