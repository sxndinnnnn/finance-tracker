# Claude Code build plan

Structured the same way as the ESG dashboard phases: each phase checks the
existing stack before adding a dependency, and confirms it understands the
current architecture before writing code. Paste one phase at a time into
Claude Code.

## Reusable context block (paste before each phase prompt)

```
This is the finance-tracker project (see README.md and CONCEPT.md at the
repo root, and docs/data-model.md for the schema). Backend: FastAPI +
SQLAlchemy 2.0 + PostgreSQL. Frontend: Next.js App Router + TypeScript +
Tailwind. Nothing about currencies, countries, or categories should be
hardcoded — see the "no hardcoding" section of README.md. Before adding any
new dependency, check requirements.txt / package.json for something that
already does the job.
```

## Phase 1 — Database & migrations
- Review the SQLAlchemy models in `backend/app/models/`.
- Generate the first Alembic migration and apply it.
- Run `app/seed/seed_currencies.py` and a small default-categories seed.
- Verify: tables exist, currencies table has 150+ rows with no hand-typed data.

## Phase 2 — Auth
- Implement signup/login/JWT refresh in `app/api/v1/auth.py`.
- Signup should collect: email, password, full name, base currency (dropdown
  populated from `GET /currencies`, not a hardcoded list), locale, timezone.

## Phase 3 — Core CRUD: accounts, categories, transactions
- Fill in `app/schemas/` and `app/api/v1/` for these three models.
- Implement the recurrence-expansion service: given a `recurrence_rule`,
  generate the next N occurrences (use `python-dateutil.rrule`).
- Frontend: accounts and transactions pages, currency-aware amount inputs.

## Phase 4 — Loans, credit cards, leases
- CRUD endpoints + pages for each.
- Credit card page should show every subscription linked to that card
  (join on `subscriptions.linked_credit_card_id`).
- Loan/lease "remaining balance" derived from payments made, not stored as
  a manually-edited field.

## Phase 5 — Subscriptions & email reminders
- CRUD for subscriptions.
- Implement `app/jobs/subscription_reminders.py` with APScheduler: daily
  sweep, compare `next_billing_date - reminder_days_before` to today, send
  via `email_service.py`, write a `reminder_logs` row so it never double-sends.
- Frontend subscriptions page: list, linked card badge, next billing date,
  "remind me in N days" control.

## Phase 6 — Dashboard & reporting
- Summary cards (total income/expense this month, fixed vs. variable split,
  upcoming bills) converted to the user's base currency via
  `exchange_rate_to_base`.
- Charts (recharts): income vs. expense trend, spending by category.

## Phase 7 — Polish
- PWA manifest + install prompt on mobile.
- Locale-aware formatting pass (`Intl.NumberFormat`/`Intl.DateTimeFormat`)
  everywhere an amount or date is rendered.
- Dark mode, empty states, loading states.

Remaining phases beyond this (multi-user households, budgets/goals,
CSV/bank import, native app wrapper) are intentionally left out of scope for
v1 — flag them if you want a Phase 8 written once the above is stable.
