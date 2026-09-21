"""FastAPI entrypoint. Route modules get wired in as Phase 2+ fill them in."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.jobs.subscription_reminders import start_scheduler, stop_scheduler

from app.api.v1 import (
    accounts,
    auth,
    categories,
    credit_cards,
    currencies,
    leases,
    loans,
    subscriptions,
    transactions,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Finance Tracker API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(currencies.router, prefix="/api/v1/currencies", tags=["currencies"])
app.include_router(categories.router, prefix="/api/v1/categories", tags=["categories"])
app.include_router(accounts.router, prefix="/api/v1/accounts", tags=["accounts"])
app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["transactions"])
app.include_router(loans.router, prefix="/api/v1/loans", tags=["loans"])
app.include_router(credit_cards.router, prefix="/api/v1/credit-cards", tags=["credit-cards"])
app.include_router(leases.router, prefix="/api/v1/leases", tags=["leases"])
app.include_router(subscriptions.router, prefix="/api/v1/subscriptions", tags=["subscriptions"])
# ... one include_router per model, added as each is implemented


@app.get("/health")
async def health():
    return {"status": "ok"}
