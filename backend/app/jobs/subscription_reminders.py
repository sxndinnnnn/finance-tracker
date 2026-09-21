"""
Daily sweep: find subscriptions due for a reminder today, send email, log
it, then roll forward the billing date of anything that's come due. Runs
inside the API process via APScheduler for simplicity — move to a separate
worker/Celery beat later if the app outgrows a single process.
"""
from datetime import date, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.user import User
from app.services.reminder_service import (
    advance_due_billing_dates,
    find_subscriptions_due_for_reminder,
    send_reminder,
)

settings = get_settings()
_scheduler = AsyncIOScheduler()


async def run_reminder_sweep() -> None:
    async with SessionLocal() as db:
        today = date.today()

        # Reminders are computed off the current next_billing_date, so this
        # runs before the billing date advances below.
        due = await find_subscriptions_due_for_reminder(db, today)
        for subscription in due:
            user = await db.get(User, subscription.user_id)
            await send_reminder(db, subscription, user.email)

        await advance_due_billing_dates(db, today)


def start_scheduler() -> None:
    _scheduler.add_job(
        run_reminder_sweep,
        "cron",
        hour=settings.reminder_check_hour_utc,
        minute=0,
        timezone=timezone.utc,
        id="subscription_reminder_sweep",
        replace_existing=True,
    )
    _scheduler.start()


def stop_scheduler() -> None:
    _scheduler.shutdown(wait=False)
