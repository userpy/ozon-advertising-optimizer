"""Source extraction services."""

from __future__ import annotations

import pandas as pd

from db import queries
from db.repository import DataRepository
from services.logging_utils import dataframe_step


@dataframe_step("extract_categories")
def extract_categories(
    repository: DataRepository,
    customer_key: str = queries.DEFAULT_CUSTOMER_KEY,
) -> pd.DataFrame:
    """Read SKU category attributes."""
    return repository.read_sql(queries.CATEGORIES_SQL, {"customer_key": customer_key})


@dataframe_step("extract_advertising")
def extract_advertising(
    repository: DataRepository,
    customer_key: str = queries.DEFAULT_CUSTOMER_KEY,
) -> pd.DataFrame:
    """Read daily advertising pressure."""
    return repository.read_sql(queries.ADVERTISING_SQL, {"customer_key": customer_key})


@dataframe_step("extract_prices")
def extract_prices(
    repository: DataRepository,
    customer_key: str = queries.DEFAULT_CUSTOMER_KEY,
) -> pd.DataFrame:
    """Read product prices."""
    return repository.read_sql(queries.PRICES_SQL, {"customer_key": customer_key})


@dataframe_step("extract_self_cost")
def extract_self_cost(
    repository: DataRepository,
    customer_key: str = queries.DEFAULT_CUSTOMER_KEY,
) -> pd.DataFrame:
    """Read product self cost values."""
    return repository.read_sql(queries.SELF_COST_SQL, {"customer_key": customer_key})


@dataframe_step("extract_sales")
def extract_sales(
    repository: DataRepository,
    customer_key: str = queries.DEFAULT_CUSTOMER_KEY,
) -> pd.DataFrame:
    """Read sales funnel metrics."""
    return repository.read_sql(queries.SALES_SQL, {"customer_key": customer_key})
