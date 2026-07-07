"""Repository layer for reading and writing PostgreSQL data."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Engine

from db.connection import get_engine
from db.models import optimal_advertising_pressure


class DataRepository:
    """Thin repository around SQLAlchemy and pandas."""

    def __init__(self, engine: Engine | None = None) -> None:
        self.engine = engine or get_engine()

    def read_sql(
        self,
        query: str,
        params: Mapping[str, Any] | None = None,
    ) -> pd.DataFrame:
        """Read SQL query results into a DataFrame."""
        with self.engine.connect() as connection:
            return pd.read_sql_query(text(query), connection, params=params)

    def execute(
        self,
        statement: str,
        params: Mapping[str, Any] | None = None,
    ) -> None:
        """Execute a SQL statement in a transaction."""
        with self.engine.begin() as connection:
            connection.execute(text(statement), params or {})

    def write_dataframe(
        self,
        frame: pd.DataFrame,
        table_name: str,
        schema: str = "public",
        if_exists: str = "append",
    ) -> None:
        """Write a DataFrame to PostgreSQL with pandas."""
        frame.to_sql(
            table_name,
            self.engine,
            schema=schema,
            if_exists=if_exists,
            index=False,
            method="multi",
        )

    def upsert_optimal_pressure(self, frame: pd.DataFrame) -> None:
        """Insert or update optimal advertising pressure rows."""
        records = _records_from_frame(frame)
        if not records:
            return

        table = optimal_advertising_pressure
        statement = insert(table).values(records)
        update_columns = {
            column.name: statement.excluded[column.name]
            for column in table.c
            if column.name not in {"id", "created_at"}
        }
        statement = statement.on_conflict_do_update(
            index_elements=["stats_date", "sku"],
            set_=update_columns,
        )

        with self.engine.begin() as connection:
            connection.execute(statement)


def _records_from_frame(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert a DataFrame to JSON-like records for SQLAlchemy."""
    normalized = frame.where(pd.notna(frame), None)
    return normalized.to_dict(orient="records")
