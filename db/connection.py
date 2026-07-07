"""PostgreSQL connection helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

load_dotenv()


@dataclass(frozen=True)
class DatabaseSettings:
    """Connection settings for PostgreSQL."""

    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", "5432"))
    name: str = os.getenv("DB_NAME", "airflow")
    user: str = os.getenv("DB_USER", "airflow")
    password: str = os.getenv("DB_PASSWORD", "airflow")

    @property
    def url(self) -> str:
        """Build a SQLAlchemy URL for the Airflow-compatible psycopg2 driver."""
        return (
            f"postgresql+psycopg2://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
        )


def get_database_url() -> str:
    """Return the configured database URL."""
    return os.getenv("DATABASE_URL", DatabaseSettings().url)


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Create a cached SQLAlchemy engine."""
    return create_engine(get_database_url(), pool_pre_ping=True, future=True)
