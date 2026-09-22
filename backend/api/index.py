"""Vercel entrypoint. Vercel's Python runtime auto-detects the ASGI `app`
object in this file and serves it directly — no adapter needed. Route
definitions, prefixes, and CORS all live in app.main; this file only needs
to exist here so Vercel can find it."""
from app.main import app  # noqa: F401
