#!/usr/bin/env bash
# Render start command: migrate, seed (both idempotent — safe on every
# deploy, not just the first), then serve.
set -euo pipefail

export PYTHONPATH=.

alembic upgrade head
python -m app.seed.seed_currencies
python -m app.seed.seed_default_categories

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
