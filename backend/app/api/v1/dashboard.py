"""
Dashboard summary: totals, fixed/variable split, and upcoming bills, all
converted to the signed-in user's base currency via each transaction's
exchange_rate_to_base captured at entry time — never a live/guessed rate.
"""
from collections import defaultdict
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.category import Category
from app.models.currency import Currency
from app.models.lease import Lease
from app.models.loan import Loan
from app.models.recurrence import RecurrenceRule
from app.models.subscription import Subscription
from app.models.transaction import Classification, Transaction, TransactionType
from app.models.user import User
from app.schemas.dashboard import CategorySpending, DashboardSummary, MonthlyTrendPoint, UpcomingBill
from app.services.currency_service import convert_minor
from app.services.recurrence_service import next_occurrences

router = APIRouter()

UPCOMING_WINDOW_DAYS = 30
TREND_MONTHS = 6


async def _currency_map(db: AsyncSession) -> dict[str, Currency]:
    result = await db.execute(select(Currency))
    return {c.code: c for c in result.scalars().all()}


def _to_base(tx: Transaction, currencies: dict[str, Currency], base_code: str) -> int | None:
    tx_currency = currencies.get(tx.currency_code)
    base_currency = currencies.get(base_code)
    if tx_currency is None or base_currency is None:
        return None
    return convert_minor(
        tx.amount_minor,
        tx.currency_code,
        tx_currency.decimal_places,
        base_code,
        base_currency.decimal_places,
        tx.exchange_rate_to_base,
    )


def _month_bounds(months_ago: int, today: date) -> tuple[date, date]:
    year, month = today.year, today.month - months_ago
    while month <= 0:
        month += 12
        year -= 1
    start = date(year, month, 1)
    end = date(year + 1, 1, 1) - timedelta(days=1) if month == 12 else date(year, month + 1, 1) - timedelta(days=1)
    return start, end


async def _month_totals(
    db: AsyncSession, user_id, start: date, end: date, currencies: dict[str, Currency], base_code: str
) -> tuple[int, int]:
    result = await db.execute(
        select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= start,
            Transaction.transaction_date <= end,
        )
    )
    income = expense = 0
    for tx in result.scalars().all():
        converted = _to_base(tx, currencies, base_code)
        if converted is None:
            continue
        if tx.type == TransactionType.income:
            income += converted
        else:
            expense += converted
    return income, expense


@router.get("/summary", response_model=DashboardSummary)
async def get_summary(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    today = date.today()
    base_code = current_user.base_currency_code
    currencies = await _currency_map(db)

    month_start, month_end = _month_bounds(0, today)
    tx_result = await db.execute(
        select(Transaction).where(
            Transaction.user_id == current_user.id,
            Transaction.transaction_date >= month_start,
            Transaction.transaction_date <= today,
        )
    )
    month_txs = tx_result.scalars().all()

    category_result = await db.execute(select(Category))
    category_names = {c.id: c.name for c in category_result.scalars().all()}

    month_income = month_expense = fixed_expense = variable_expense = 0
    category_totals: dict[str, int] = defaultdict(int)

    for tx in month_txs:
        converted = _to_base(tx, currencies, base_code)
        if converted is None:
            continue
        if tx.type == TransactionType.income:
            month_income += converted
            continue
        month_expense += converted
        if tx.classification == Classification.fixed:
            fixed_expense += converted
        else:
            variable_expense += converted
        category_totals[category_names.get(tx.category_id, "Uncategorized")] += converted

    spending_by_category = [
        CategorySpending(category_name=name, amount_minor=amount)
        for name, amount in sorted(category_totals.items(), key=lambda kv: -kv[1])
    ]

    trend: list[MonthlyTrendPoint] = []
    for months_ago in range(TREND_MONTHS - 1, -1, -1):
        start, end = _month_bounds(months_ago, today)
        income, expense = await _month_totals(db, current_user.id, start, end, currencies, base_code)
        trend.append(MonthlyTrendPoint(month=start.strftime("%Y-%m"), income_minor=income, expense_minor=expense))

    window_end = today + timedelta(days=UPCOMING_WINDOW_DAYS)
    upcoming: list[UpcomingBill] = []

    loans_result = await db.execute(select(Loan).where(Loan.user_id == current_user.id))
    for loan in loans_result.scalars().all():
        rule = await db.get(RecurrenceRule, loan.payment_recurrence_rule_id)
        if rule is None:
            continue
        occurrences = next_occurrences(rule, after=today, count=1)
        if occurrences and occurrences[0] <= window_end:
            upcoming.append(
                UpcomingBill(
                    name=loan.name,
                    kind="loan",
                    amount_minor=loan.payment_amount_minor,
                    currency_code=loan.currency_code,
                    due_date=occurrences[0],
                )
            )

    leases_result = await db.execute(select(Lease).where(Lease.user_id == current_user.id))
    for lease in leases_result.scalars().all():
        rule = await db.get(RecurrenceRule, lease.payment_recurrence_rule_id)
        if rule is None:
            continue
        occurrences = next_occurrences(rule, after=today, count=1)
        if occurrences and occurrences[0] <= window_end:
            upcoming.append(
                UpcomingBill(
                    name=lease.name,
                    kind="lease",
                    amount_minor=lease.monthly_payment_minor,
                    currency_code=lease.currency_code,
                    due_date=occurrences[0],
                )
            )

    subs_result = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user.id, Subscription.is_active.is_(True))
    )
    for sub in subs_result.scalars().all():
        if sub.next_billing_date <= window_end:
            upcoming.append(
                UpcomingBill(
                    name=sub.name,
                    kind="subscription",
                    amount_minor=sub.amount_minor,
                    currency_code=sub.currency_code,
                    due_date=sub.next_billing_date,
                )
            )

    upcoming.sort(key=lambda bill: bill.due_date)

    return DashboardSummary(
        base_currency_code=base_code,
        month_income_minor=month_income,
        month_expense_minor=month_expense,
        fixed_expense_minor=fixed_expense,
        variable_expense_minor=variable_expense,
        upcoming_bills=upcoming,
        income_expense_trend=trend,
        spending_by_category=spending_by_category,
    )
