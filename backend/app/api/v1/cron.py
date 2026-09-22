"""Vercel Cron entrypoint for the subscription reminder sweep. Verifies the
request is really Vercel Cron, then delegates to the same run_reminder_sweep()
used by the in-process APScheduler job for local/non-serverless deployments."""
import secrets

from fastapi import APIRouter, Header, HTTPException, status

from app.core.config import get_settings
from app.jobs.subscription_reminders import run_reminder_sweep

router = APIRouter()
settings = get_settings()


@router.get("/reminder-sweep")
async def reminder_sweep(authorization: str | None = Header(default=None)):
    if not settings.cron_secret:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "CRON_SECRET not configured")
    expected = f"Bearer {settings.cron_secret}"
    if not authorization or not secrets.compare_digest(authorization, expected):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or missing cron credentials")

    await run_reminder_sweep()
    return {"status": "ok"}
