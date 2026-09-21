"""Read-only listing of the currencies table — seeded from ISO 4217, never hardcoded here."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.currency import Currency
from app.schemas.currency import CurrencyRead

router = APIRouter()


@router.get("", response_model=list[CurrencyRead])
async def list_currencies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Currency).order_by(Currency.code))
    return result.scalars().all()
