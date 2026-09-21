"""Shared FastAPI dependencies: current-user resolution, DB session, etc.
Fill in get_current_user() in Phase 2 once auth exists."""
from app.core.database import get_db  # re-exported for convenience

__all__ = ["get_db"]
