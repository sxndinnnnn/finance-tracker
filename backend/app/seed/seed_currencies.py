"""
Run with: python -m app.seed.seed_currencies
Populates the currencies table from ISO 4217 (via pycountry/Babel) — the
one place currency data ever gets written, so the rest of the app never
needs to know or care what currencies exist.
"""
import asyncio

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.currency import Currency
from app.services.currency_service import list_iso_currencies


async def seed_currencies() -> None:
    async with SessionLocal() as db:
        existing = (await db.execute(select(Currency.code))).scalars().all()
        existing_codes = set(existing)

        for c in list_iso_currencies():
            if c["code"] in existing_codes:
                continue
            db.add(Currency(**c))

        await db.commit()
        print(f"Seeded currencies (skipped {len(existing_codes)} already present).")


if __name__ == "__main__":
    asyncio.run(seed_currencies())
