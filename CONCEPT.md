# Finance Tracker — Concept

## 1. Who it's for

Working professionals who want one place to see income, spending, debt, and
recurring charges — regardless of what country or currency they operate in.
A user in Colombo tracking LKR alongside a USD freelance income, and a user
in Berlin tracking EUR, should both get a first-class experience with zero
code changes on your end.

## 2. Core principle: nothing about a specific country or currency is baked in

Every place the app would normally hardcode "USD, EUR, GBP, ..." or
"United States, Germany, ...", it instead:
- reads from **ISO 4217** (currencies) and **ISO 3166** (countries) via a
  library (`pycountry` on the backend, `Intl` in the browser) at seed/runtime,
- lets the *user* pick their base currency and locale at signup, and
- formats numbers/dates via `Intl.NumberFormat` / `Intl.DateTimeFormat`
  (frontend) and `babel.numbers` (backend), never a hand-written `$` or
  `,` separator.

The only exception — per your "unless absolutely necessary" — is the seed
list of **default categories** (Groceries, Rent, Salary, etc.), because a
completely empty category list is a bad first-run experience. Even that seed
is a data fixture the user can rename, delete, or ignore, not logic.

## 3. Feature set

### 3.1 Income & expenses
- Every transaction is `income` or `expense`, and separately `fixed` or
  `variable`. Fixed items (rent, salary) can carry a `recurrence_rule` so
  they auto-generate future instances; variable items are one-off entries.
- Each transaction has its own currency (defaults to the account's currency),
  with an `exchange_rate_to_base` captured at entry time so historical
  reports stay accurate even if rates move later.
- User-defined, unlimited categories (income and expense are separate
  category trees), each with an icon/color the user picks — not a fixed enum.

### 3.2 Accounts
- Bank accounts, cash wallets, and e-wallets, each with their own currency.
  A user can hold accounts in multiple currencies simultaneously; the
  dashboard converts to their base currency for the summary view only.

### 3.3 Loans
- Principal, interest rate (fixed or variable), term, lender, linked
  repayment account, and a recurrence rule for the payment schedule.
- Remaining balance is derived from principal minus paid installments, not
  manually re-typed each month.

### 3.4 Credit cards
- Modeled as an account subtype: credit limit, statement day, due day,
  current balance, and currency. Network (Visa/Mastercard/local card
  scheme/etc.) is a free-text field, not a fixed dropdown, since card
  networks vary a lot by country.
- Subscriptions link to a specific card, so "which card is this subscription
  on" is answerable at a glance, and if a card is cancelled you can see every
  subscription that needs to move.

### 3.5 Leases
- Asset description, lessor, monthly payment, start/end date, linked payment
  account, and a recurrence rule — structurally identical to a loan's payment
  schedule, so the two share the same recurrence engine.

### 3.6 Subscriptions & reminders
- Name, amount, currency, billing recurrence, linked card/account, and a
  per-subscription (or account-default) "remind me N days before" setting.
- A daily job compares `next_billing_date - reminder_days_before` to today
  and sends an email for every match, logging each send so a restart or a
  slow job never double-sends.

## 4. Architecture at a glance

```
┌─────────────┐        HTTPS/JSON        ┌──────────────┐
│  Next.js     │ ───────────────────────▶ │   FastAPI     │
│  (web+PWA)   │ ◀─────────────────────── │   backend     │
└─────────────┘                           └──────┬───────┘
                                                   │
                                     ┌─────────────┼─────────────┐
                                     ▼             ▼             ▼
                              PostgreSQL   APScheduler job   Email sender
                              (all data)   (daily reminder    (SMTP/SendGrid/
                                            sweep)             Resend — pick
                                                                one via env)
```

- **One responsive frontend** serves both mobile browsers and desktop (this
  satisfies "mobile and web" without maintaining a separate native codebase);
  it ships a PWA manifest so it's installable to a phone home screen.
- **FastAPI backend** exposes a versioned REST API (`/api/v1/...`) so a
  native app can be added later without breaking the web client.
- **Reminder job** runs inside the backend process via APScheduler for
  simplicity; the scaffold isolates it in `app/jobs/` so it can be moved to
  a separate worker/Celery/cron later without touching business logic.

## 5. Data model summary

See `docs/data-model.md` for full field-by-field detail. Tables:
`users`, `currencies`, `categories`, `recurrence_rules`, `accounts`,
`transactions`, `loans`, `credit_cards`, `leases`, `subscriptions`,
`reminder_logs`.

## 6. What's scaffolded vs. what you'll build next

**Scaffolded now:** project structure, settings/config (env-driven), the
full SQLAlchemy data model, the currency seed service, the email service
abstraction, and the reminder job skeleton, plus the frontend route
structure and a currency-formatting utility.

**Left for Claude Code, in the order `docs/claude-code-build-plan.md`
suggests:** Alembic migration generation, auth flow, CRUD endpoints per
model, the recurrence-expansion logic, the dashboard UI and charts, and the
PWA install experience.
