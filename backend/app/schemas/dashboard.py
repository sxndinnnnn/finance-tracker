from datetime import date

from pydantic import BaseModel


class UpcomingBill(BaseModel):
    name: str
    kind: str  # loan | lease | subscription
    amount_minor: int
    currency_code: str
    due_date: date


class MonthlyTrendPoint(BaseModel):
    month: str  # YYYY-MM
    income_minor: int
    expense_minor: int


class CategorySpending(BaseModel):
    category_name: str
    amount_minor: int


class DashboardSummary(BaseModel):
    base_currency_code: str
    month_income_minor: int
    month_expense_minor: int
    fixed_expense_minor: int
    variable_expense_minor: int
    upcoming_bills: list[UpcomingBill]
    income_expense_trend: list[MonthlyTrendPoint]
    spending_by_category: list[CategorySpending]
