"""
Seeded from ISO 4217 via pycountry — see app/seed/seed_currencies.py.
Never add a row here by hand; if a currency is missing, re-run the seed.
"""
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Currency(Base):
    __tablename__ = "currencies"

    code: Mapped[str] = mapped_column(String(3), primary_key=True)  # ISO 4217, e.g. "USD"
    name: Mapped[str] = mapped_column(String(128))
    symbol: Mapped[str] = mapped_column(String(8))
    decimal_places: Mapped[int] = mapped_column(Integer, default=2)
