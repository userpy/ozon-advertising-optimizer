"""Persistence service for optimizer results."""

from __future__ import annotations

import pandas as pd

from db.repository import DataRepository
from services.logging_utils import dataframe_step


@dataframe_step("save_results")
def save_results(
    frame: pd.DataFrame,
    repository: DataRepository | None = None,
) -> pd.DataFrame:
    """Save optimizer results to PostgreSQL."""
    repository = repository or DataRepository()
    prepared = _prepare_for_database(frame)
    repository.upsert_optimal_pressure(prepared)
    return prepared


def _prepare_for_database(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize persisted columns before writing."""
    prepared = frame.copy()
    prepared["stats_date"] = pd.to_datetime(prepared["stats_date"]).dt.date
    numeric_columns = [column for column in prepared.columns if column != "offer_id"]
    numeric_columns = [column for column in numeric_columns if column != "stats_date"]
    for column in numeric_columns:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
    return prepared
