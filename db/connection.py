"""PostgreSQL connection helpers."""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from services.settings import Settings


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Create a cached SQLAlchemy engine."""
    return create_engine(
        Settings().database_url,
        pool_pre_ping=True,
        future=True,
    )
