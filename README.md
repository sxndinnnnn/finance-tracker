# Finance Tracker — Project Scaffold

A localized, multi-currency personal finance tracker for working professionals.
Tracks income, expenses, loans, credit cards, leases, and subscriptions, with
email reminders before subscriptions renew.

This repo is a **starting scaffold**, meant to be opened in Claude Code and
built out phase by phase. See `docs/claude-code-build-plan.md` for the
recommended build order, and `CONCEPT.md` for the full product/technical
concept. `docs/data-model.md` documents every table and why it's shaped the
way it is.

## Stack

- **Backend:** Python, FastAPI, SQLAlchemy 2.0, Alembic migrations, PostgreSQL,
  APScheduler for the reminder job (matches your existing FastAPI/Uvicorn setup).
- **Frontend:** Next.js (App Router) + TypeScript + Tailwind CSS, responsive
  by default and installable as a PWA on mobile — one codebase for web and
  mobile rather than a separate native app.
- **Email:** provider-agnostic sender (SMTP by default; drop in SendGrid/Resend
  by swapping one class) — see `backend/app/services/email_service.py`.

## Why this stack

You've already got FastAPI/Uvicorn and Python working on your machine from the
ESG dashboard, so the backend reuses that rather than introducing a second
language. Next.js gives you one responsive codebase that covers both "mobile"
and "web" from the brief without a separate React Native app — you can wrap it
in Capacitor later if you want an app-store build.

## Getting started

```bash
# 1. Copy env file and fill in real values
cp .env.example .env

# 2. Start Postgres (and optionally the full stack) via Docker
docker compose up -d db

# 3. Backend
cd backend
python -m venv .venv && .venv\Scripts\activate   # Windows/PowerShell
pip install -r requirements.txt
alembic upgrade head
python -m app.seed.seed_currencies   # seeds ISO 4217 currencies — nothing hardcoded
uvicorn app.main:app --reload

# 4. Frontend
cd ../frontend
npm install
npm run dev
```

## Repo layout

```
finance-tracker/
├── CONCEPT.md                 # full product + technical concept
├── docs/
│   ├── data-model.md          # every table, field, and why
│   └── claude-code-build-plan.md   # phased build plan for Claude Code
├── backend/                   # FastAPI service
│   └── app/
│       ├── core/              # settings, db session, security — env-driven, no hardcoded values
│       ├── models/            # SQLAlchemy models (the data model)
│       ├── schemas/           # Pydantic request/response schemas (stubs — fill in per model)
│       ├── api/v1/            # route modules (stubs — fill in per model)
│       ├── services/          # currency lookup, recurrence expansion, email sending
│       ├── jobs/              # subscription reminder cron job
│       └── seed/              # seeds currencies from pycountry — never hand-typed
└── frontend/                  # Next.js app (web + mobile via responsive/PWA)
    └── src/
        ├── app/(dashboard)/   # one route folder per feature
        ├── app/(auth)/
        ├── components/, hooks/, lib/, types/
```

## The "no hardcoding" rule, concretely

- **Currencies & symbols** come from `pycountry` / `Intl.supportedValuesOf`,
  seeded into a `currencies` table — never a hand-typed array in code.
- **Categories** ship with a small seeded default set but live in the
  database as user-editable rows, not an enum in code.
- **Recurrence** (fixed expenses, loan payments, lease payments, subscription
  billing) is one generic `recurrence_rules` table driven by RRULE semantics,
  not a `WEEKLY | MONTHLY | ...` branch repeated in five different models.
- **Reminder lead time, currency formatting, locale** are per-user settings
  columns or env config, not constants baked into the frontend.

The only things that are intentionally fixed are structural: table names,
enum *kinds* (e.g. `transaction_type = income | expense` is a real fixed
distinction, not a localization concern).
