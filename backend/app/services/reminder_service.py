"""
Business logic for "which subscriptions need a reminder today" and "which
subscriptions' billing dates need to roll forward". Kept separate from the
job scheduler (app/jobs/) so it's independently testable.
"""
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription
from app.models.user import User
from app.models.recurrence import RecurrenceRule
from app.models.reminder_log import ReminderLog, ReminderStatus
from app.services.email_service import get_email_sender
from app.services.recurrence_service import next_occurrences


async def find_subscriptions_due_for_reminder(db: AsyncSession, today: date) -> list[Subscription]:
    result = await db.execute(select(Subscription).where(Subscription.is_active.is_(True)))
    subscriptions = result.scalars().all()

    due = []
    for sub in subscriptions:
        user = await db.get(User, sub.user_id)
        lead_days = sub.reminder_days_before or user.default_reminder_days_before
        if sub.next_billing_date - timedelta(days=lead_days) != today:
            continue

        # A restart or a slow job re-running the same day must never
        # double-send — reminder_logs is the source of truth for that.
        already_sent = await db.scalar(
            select(ReminderLog).where(
                ReminderLog.subscription_id == sub.id,
                ReminderLog.sent_at >= datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc),
            )
        )
        if already_sent is None:
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


async def advance_due_billing_dates(db: AsyncSession, today: date) -> int:
    """Rolls next_billing_date forward for every subscription whose date has
    passed, using its own recurrence rule. Returns how many were advanced."""
    result = await db.execute(
        select(Subscription).where(
            Subscription.is_active.is_(True), Subscription.next_billing_date < today
        )
    )
    subscriptions = result.scalars().all()

    advanced = 0
    for sub in subscriptions:
        rule = await db.get(RecurrenceRule, sub.billing_recurrence_rule_id)
        if rule is None:
            continue
        upcoming = next_occurrences(rule, after=today, count=1)
        if upcoming:
            sub.next_billing_date = upcoming[0]
            advanced += 1

    if advanced:
        await db.commit()
    return advanced
