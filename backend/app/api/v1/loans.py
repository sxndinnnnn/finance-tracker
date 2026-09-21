import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.account import Account
from app.models.currency import Currency
from app.models.loan import Loan
from app.models.recurrence import RecurrenceRule
from app.models.user import User
from app.schemas.loan import LoanCreate, LoanRead, LoanUpdate
from app.schemas.recurrence import RecurrenceRuleRead
from app.services.recurrence_service import count_occurrences_on_or_before

router = APIRouter()


async def _get_owned_account(db: AsyncSession, account_id: uuid.UUID, user: User) -> Account:
    account = await db.get(Account, account_id)
    if account is None or account.user_id != user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown linked_account_id")
    return account


def _remaining_balance(loan: Loan, rule: RecurrenceRule) -> int:
    # Derived from the payment schedule itself — how many installments have
    # come due as of today — rather than a manually re-typed figure.
    paid_installments = count_occurrences_on_or_before(rule, date.today(), max_count=loan.term_months)
    remaining = loan.principal_minor - paid_installments * loan.payment_amount_minor
    return max(remaining, 0)


async def _to_read(db: AsyncSession, loan: Loan) -> LoanRead:
    rule = await db.get(RecurrenceRule, loan.payment_recurrence_rule_id)
    return LoanRead(
        **{c.name: getattr(loan, c.name) for c in Loan.__table__.columns if c.name != "remaining_balance_minor"},
        remaining_balance_minor=_remaining_balance(loan, rule) if rule else loan.remaining_balance_minor,
        recurrence=RecurrenceRuleRead.model_validate(rule) if rule else None,
    )


@router.get("", response_model=list[LoanRead])
async def list_loans(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Loan).where(Loan.user_id == current_user.id).order_by(Loan.start_date.desc()))
    return [await _to_read(db, loan) for loan in result.scalars().all()]


@router.post("", response_model=LoanRead, status_code=status.HTTP_201_CREATED)
async def create_loan(
    payload: LoanCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_account(db, payload.linked_account_id, current_user)
    currency_code = payload.currency_code.upper()
    if await db.get(Currency, currency_code) is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown currency_code")

    rule = RecurrenceRule(**payload.recurrence.model_dump())
    db.add(rule)
    await db.flush()

    loan = Loan(
        user_id=current_user.id,
        name=payload.name,
        lender=payload.lender,
        principal_minor=payload.principal_minor,
        currency_code=currency_code,
        interest_rate=payload.interest_rate,
        interest_type=payload.interest_type,
        term_months=payload.term_months,
        start_date=payload.start_date,
        payment_amount_minor=payload.payment_amount_minor,
        payment_recurrence_rule_id=rule.id,
        linked_account_id=payload.linked_account_id,
        remaining_balance_minor=payload.principal_minor,
    )
    db.add(loan)
    await db.commit()
    await db.refresh(loan)
    return await _to_read(db, loan)


async def _get_own_loan(db: AsyncSession, loan_id: uuid.UUID, user: User) -> Loan:
    loan = await db.get(Loan, loan_id)
    if loan is None or loan.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Loan not found")
    return loan


@router.get("/{loan_id}", response_model=LoanRead)
async def get_loan(
    loan_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    loan = await _get_own_loan(db, loan_id, current_user)
    return await _to_read(db, loan)


@router.patch("/{loan_id}", response_model=LoanRead)
async def update_loan(
    loan_id: uuid.UUID,
    payload: LoanUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    loan = await _get_own_loan(db, loan_id, current_user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(loan, field, value)
    await db.commit()
    await db.refresh(loan)
    return await _to_read(db, loan)


@router.delete("/{loan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_loan(
    loan_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    loan = await _get_own_loan(db, loan_id, current_user)
    await db.delete(loan)
    await db.commit()
