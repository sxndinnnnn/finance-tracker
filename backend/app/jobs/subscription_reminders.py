"""
Daily sweep: find subscriptions due for a reminder today, send email, log it.
Runs inside the API process via APScheduler for simplicity — move to a
separate worker/Celery beat later if the app outgrows a single process.
"""
from datetime import date, datetime, time, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.user import User
from app.services.reminder_service import find_subscriptions_due_for_reminder, send_reminder

settings = get_settings()
_scheduler = AsyncIOScheduler()


async def run_reminder_sweep() -> None:
    async with SessionLocal() as db:
        today = date.today()
        due = await find_subscriptions_due_for_reminder(db, today)
        for subscription in due:
            user = await db.get(User, subscription.user_id)
            await send_reminder(db, subscription, user.email)


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
