"""
Business logic for "which subscriptions need a reminder today". Kept
separate from the job scheduler (app/jobs/) so it's independently testable.
"""
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription
from app.models.user import User
from app.models.reminder_log import ReminderLog, ReminderStatus
from app.services.email_service import get_email_sender


async def find_subscriptions_due_for_reminder(db: AsyncSession, today: date) -> list[Subscription]:
    result = await db.execute(select(Subscription).where(Subscription.is_active.is_(True)))
    subscriptions = result.scalars().all()

    due = []
    for sub in subscriptions:
        user = await db.get(User, sub.user_id)
        lead_days = sub.reminder_days_before or user.default_reminder_days_before
        if sub.next_billing_date - timedelta(days=lead_days) == today:
            due.append(sub)
    return due


async def send_reminder(db: AsyncSession, subscription: Subscription, user_email: str) -> None:
    sender = get_email_sender()
    try:
        await sender.send(
            to=user_email,
            subject=f"{subscription.name} renews soon",
            body=(
                f"Your subscription '{subscription.name}' renews on "
                f"{subscription.next_billing_date.isoformat()}."
            ),
        )
        status = ReminderStatus.sent
    except Exception:
        status = ReminderStatus.failed

    db.add(ReminderLog(subscription_id=subscription.id, status=status))
    await db.commit()
