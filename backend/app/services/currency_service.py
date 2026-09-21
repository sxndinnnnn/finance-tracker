"""
Source of truth for currency data. Nothing here is hand-typed — it's a thin
wrapper over pycountry/Babel so the currencies table (and therefore every
dropdown in the UI) reflects ISO 4217, not a list someone wrote once and
forgot to update.
"""
import pycountry
from babel import numbers as babel_numbers


def list_iso_currencies() -> list[dict]:
    """Returns every ISO 4217 currency as {code, name, symbol, decimal_places}."""
    results = []
    for currency in pycountry.currencies:
        code = currency.alpha_3
        try:
            symbol = babel_numbers.get_currency_symbol(code, locale="en")
        except Exception:
            symbol = code
        try:
            decimal_places = babel_numbers.get_currency_precision(code)
        except Exception:
            decimal_places = 2
        results.append(
            {
                "code": code,
                "name": currency.name,
                "symbol": symbol,
                "decimal_places": decimal_places,
            }
        )
    return results


def format_amount(amount_minor: int, currency_code: str, locale: str = "en") -> str:
    """Render minor units (cents) as a locale- and currency-correct string."""
    decimal_places = babel_numbers.get_currency_precision(currency_code)
    major_amount = amount_minor / (10**decimal_places)
    return babel_numbers.format_currency(major_amount, currency_code, locale=locale)


def convert_minor(
    amount_minor: int,
    from_code: str,
    from_decimal_places: int,
    to_code: str,
    to_decimal_places: int,
    rate_to_base: float | None,
) -> int | None:
    """Converts minor units from one currency to another using a rate
    captured at entry time. Returns None when a conversion can't be made
    (different currencies with no rate on record) rather than guessing —
    callers should exclude those amounts from base-currency totals instead
    of silently treating them as 1:1.
    """
    if from_code == to_code:
        return amount_minor
    if rate_to_base is None:
        return None
    major = amount_minor / (10**from_decimal_places)
    return round(major * rate_to_base * (10**to_decimal_places))
