# Finance Tracker — Project Scaffold

A localized, multi-currency personal finance tracker for working professionals.
Tracks income, expenses, loans, credit cards, leases, and subscriptions, with
email reminders before subscriptions renew.

Built out phase by phase per `docs/claude-code-build-plan.md` — see
`CONCEPT.md` for the full product/technical concept and `docs/data-model.md`
for every table and why it's shaped the way it is.

## Stack

- **Backend:** Python, FastAPI, SQLAlchemy 2.0, Alembic migrations, PostgreSQL.
  The daily reminder sweep runs via an in-process APScheduler job locally
  (`ENABLE_IN_PROCESS_SCHEDULER=true`, the default) or via a Vercel Cron Job
  hitting a protected endpoint when deployed serverless (see Deployment).
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

## Deployment (Vercel + Vercel + Supabase)

Frontend and backend are **two separate Vercel projects** from this one
repo. The backend deploys as a Python serverless function
(`backend/api/index.py` re-exports the FastAPI `app`; `backend/vercel.json`
routes every path to it and defines the Vercel Cron Job that replaces the
in-process reminder scheduler — serverless functions don't stay alive
between requests, so `app/jobs/subscription_reminders.py`'s APScheduler
loop can't run there the way it does locally).

### 1. Database — Supabase

Create a project, then get connection strings from Project Settings →
Database → **Connection string**. You'll use two different ones:

- **Direct connection** (port 5432) — for running migrations (step 3 below).
- **Supavisor transaction pooler** (port 6543, "Transaction" mode) — for the
  deployed backend's `DATABASE_URL` (step 2). Many short-lived serverless
  invocations opening direct connections would exhaust Supabase's
  connection limit fast; the pooler is built for exactly this.

Both come back as `postgres://...`; `DATABASE_URL` accepts either unmodified.

### 2. Backend — Vercel

**Add New → Project**, import this repo, set **Root Directory** to `backend`.
Vercel picks up `backend/vercel.json` and `backend/api/index.py`
automatically. Set these env vars:

- `DATABASE_URL` — the Supabase **pooler** connection string from step 1
- `DB_SSL_REQUIRE=true`
- `DB_DISABLE_PREPARED_STATEMENT_CACHE=true` — required alongside the pooler;
  asyncpg's prepared-statement cache doesn't work under transaction-mode pooling
- `ENABLE_IN_PROCESS_SCHEDULER=false` — the Vercel Cron Job defined in
  `vercel.json` handles the daily reminder sweep instead
- `CRON_SECRET` — a random value (e.g. `openssl rand -hex 32`); Vercel sends
  it back as `Authorization: Bearer $CRON_SECRET` on cron requests, which
  `/api/v1/cron/reminder-sweep` checks before running anything
- `SECRET_KEY` — a random value, same idea
- `CORS_ORIGINS` — your frontend's Vercel URL once you have it (step 4);
  comma-separated if there's more than one
- `SMTP_HOST` / `SMTP_USERNAME` / `SMTP_PASSWORD` — optional, only needed for
  subscription-reminder emails to actually send

### 3. Run migrations (one-time, and after any future migration)

There's no persistent deploy step to run these automatically on Vercel, so
run them yourself, from `backend/`, with `DATABASE_URL` pointed at Supabase's
**direct** connection (not the pooler) and `DB_SSL_REQUIRE=true`:

```bash
alembic upgrade head
python -m app.seed.seed_currencies
python -m app.seed.seed_default_categories
```

Both seed scripts are idempotent — safe to re-run.

### 4. Frontend — Vercel

**Add New → Project**, import this repo again, set **Root Directory** to
`frontend`. Framework preset (Next.js) is auto-detected. Set one env var:

- `NEXT_PUBLIC_API_BASE_URL` — your backend project's URL plus `/api/v1`,
  e.g. `https://finance-tracker-backend.vercel.app/api/v1`

Deploy, then copy the resulting `https://<project>.vercel.app` URL back into
the backend project's `CORS_ORIGINS` (step 2) and redeploy it so the API
accepts requests from it — `CORS_ORIGINS` defaults to `*` for local dev, but
production needs it locked to the real frontend origin.

### What to check after first deploy

The routing (`vercel.json`'s rewrite), function size (`pycountry`/`Babel`
bundle real locale data), and the Cron Job's daily run can only be confirmed
against a live deployment, not from local testing:

- `curl https://<backend>.vercel.app/health` and `.../api/v1/currencies` —
  both should return normally, not 404.
- Vercel dashboard → your backend project → **Cron Jobs** tab, the day after
  deploy — confirms it actually fired and got a 200 back.
- Build output for the backend project — flags it if the function's bundled
  size is getting close to Vercel's limit.

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
