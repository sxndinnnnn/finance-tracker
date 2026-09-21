"""
Run with: python -m app.seed.seed_default_categories
Seeds a small starter set of system-default categories (user_id=None) so new
users aren't dropped into an empty category list. These are ordinary editable
rows, not an enum — a user can rename or delete any of them.
"""
import asyncio

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.category import Category, CategoryKind

DEFAULT_CATEGORIES = [
    ("Salary", CategoryKind.income),
    ("Freelance/Business Income", CategoryKind.income),
    ("Other Income", CategoryKind.income),
    ("Rent/Mortgage", CategoryKind.expense),
    ("Groceries", CategoryKind.expense),
    ("Utilities", CategoryKind.expense),
    ("Transport", CategoryKind.expense),
    ("Dining Out", CategoryKind.expense),
    ("Healthcare", CategoryKind.expense),
    ("Entertainment", CategoryKind.expense),
    ("Other Expense", CategoryKind.expense),
]


async def seed_default_categories() -> None:
    async with SessionLocal() as db:
        existing = (
            await db.execute(select(Category.name).where(Category.user_id.is_(None)))
        ).scalars().all()
        existing_names = set(existing)

        added = 0
        for name, kind in DEFAULT_CATEGORIES:
            if name in existing_names:
                continue
            db.add(Category(user_id=None, name=name, kind=kind))
            added += 1

        await db.commit()
        print(f"Seeded {added} default categories (skipped {len(existing_names)} already present).")


if __name__ == "__main__":
    asyncio.run(seed_default_categories())
