"""DataFrame preprocessing services."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from services.logging_utils import dataframe_step

GROUP_COLUMNS = [
    "sku",
    "stats_date",
    "category_1_name",
    "category_2_name",
    "type_name",
    "product",
    "model",
    "offer_id",
    "project_index",
    "customer_key",
    "company_name",
]

AGGREGATIONS = {
    "id": "max",
    "created_at": "max",
    "added_to_cart_total": "sum",
    "units_ordered": "sum",
    "unique_visitors_product_page": "sum",
    "search_and_catalog_impressions": "sum",
    "added_to_cart_from_product_page": "sum",
    "ordered_amount": "sum",
    "search_and_catalog_position": "mean",
    "price_elasticity_conversion_views_to_order": "mean",
    "advertising_budget_today": "max",
    "advertising_pressure_today": "max",
    "product_price": "max",
    "morning_price_unchanged": "max",
    "unit_cost_price": "max",
    "base_fixed_cost_per_unit": "max",
    "redemption_prct": "max",
    "unit_margin": "max",
    "cr1": "max",
    "cr2": "max",
}


@dataframe_step("build_feature_mart")
def build_feature_mart(
    sales: pd.DataFrame,
    categories: pd.DataFrame,
    advertising: pd.DataFrame,
    prices: pd.DataFrame,
    self_cost: pd.DataFrame,
) -> pd.DataFrame:
    """Join extracted source frames into a feature mart."""
    mart = sales.merge(categories, on="sku", how="left")
    mart = mart.merge(advertising, on=["sku", "stats_date"], how="left")
    mart = mart.merge(prices, on="sku", how="left", suffixes=("", "_price"))
    mart = mart.merge(self_cost, on="sku", how="left", suffixes=("", "_cost"))
    mart["advertising_budget_today"] = mart["advertising_budget_today"].fillna(0)
    mart["advertising_pressure_today"] = mart["advertising_pressure_today"].fillna(0)
    mart["base_fixed_cost_per_unit"] = 0.5
    return _select_feature_columns(mart)


@dataframe_step("aggregate_daily_metrics")
def aggregate_daily_metrics(feature_mart: pd.DataFrame) -> pd.DataFrame:
    """Aggregate feature rows to SKU and date grain."""
    normalized = _normalize_feature_types(feature_mart)
    aggregated = normalized.groupby(GROUP_COLUMNS, dropna=False).agg(AGGREGATIONS)
    return aggregated.reset_index()


@dataframe_step("calculate_history_features")
def calculate_history_features(daily_metrics: pd.DataFrame) -> pd.DataFrame:
    """Add date-aware lag and rolling average features."""
    frame = _normalize_feature_types(daily_metrics)
    frame = _sort_for_history(frame)
    for source, target, days in _lag_specs():
        frame = _add_lag_feature(frame, source, target, days)
    for source, target, days in _average_specs():
        frame = _add_average_feature(frame, source, target, days)
    return frame


def _select_feature_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Return columns used by the model pipeline."""
    columns = [*GROUP_COLUMNS, *AGGREGATIONS.keys()]
    present_columns = [column for column in columns if column in frame.columns]
    return frame[present_columns].copy()


def _normalize_feature_types(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize dates and numeric columns after SQL or CSV loading."""
    normalized = frame.copy()
    normalized["stats_date"] = pd.to_datetime(normalized["stats_date"]).dt.date
    _coerce_numeric_columns(normalized, _numeric_columns(normalized))
    _clip_rate_columns(normalized, ["cr1", "cr2", "redemption_prct"])
    return normalized


def _coerce_numeric_columns(frame: pd.DataFrame, columns: Iterable[str]) -> None:
    """Convert selected columns to numeric values in place."""
    for column in columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")


def _numeric_columns(frame: pd.DataFrame) -> list[str]:
    """Find columns that should be treated as numeric."""
    excluded = set(GROUP_COLUMNS) | {"created_at"}
    return [column for column in frame.columns if column not in excluded]


def _clip_rate_columns(frame: pd.DataFrame, columns: Iterable[str]) -> None:
    """Clip probability-like columns to the 0..1 interval."""
    for column in columns:
        if column in frame.columns:
            frame[column] = frame[column].clip(lower=0, upper=1)


def _sort_for_history(frame: pd.DataFrame) -> pd.DataFrame:
    """Sort rows for deterministic history calculations."""
    sorted_frame = frame.copy()
    sorted_frame["stats_date"] = pd.to_datetime(sorted_frame["stats_date"])
    return sorted_frame.sort_values(["sku", "stats_date"]).reset_index(drop=True)


def _lag_specs() -> list[tuple[str, str, int]]:
    """Return legacy lag feature definitions."""
    return [
        ("cr1", "cr1_yesterday", 1),
        ("cr2", "cr2_yesterday", 1),
        ("advertising_budget_today", "advertising_budget_yesterday", 1),
        ("advertising_pressure_today", "advertising_pressure_yesterday", 1),
        ("search_and_catalog_impressions", "impressions_yesterday", 1),
        ("search_and_catalog_position", "search_and_catalog_position_yesterday", 1),
        ("added_to_cart_total", "added_to_cart_yesterday", 1),
        ("cr1", "cr1_m2", 2),
        ("cr2", "cr2_m2", 2),
        ("search_and_catalog_impressions", "impressions_m2", 2),
        ("cr1", "cr1_m9", 9),
        ("cr2", "cr2_m9", 9),
        ("search_and_catalog_impressions", "impressions_m9", 9),
        ("cr1", "cr1_m10", 10),
        ("cr2", "cr2_m10", 10),
        ("search_and_catalog_impressions", "impressions_m10", 10),
        ("cr1", "cr1_m11", 11),
        ("cr2", "cr2_m11", 11),
        ("search_and_catalog_impressions", "impressions_m11", 11),
        ("cr1", "cr1_m12", 12),
        ("cr2", "cr2_m12", 12),
        ("search_and_catalog_impressions", "impressions_m12", 12),
        ("cr1", "cr1_m13", 13),
        ("cr2", "cr2_m13", 13),
        ("search_and_catalog_impressions", "impressions_m13", 13),
        ("cr1", "cr1_m14", 14),
        ("cr2", "cr2_m14", 14),
        ("search_and_catalog_impressions", "impressions_m14", 14),
    ]


def _average_specs() -> list[tuple[str, str, int]]:
    """Return legacy rolling average feature definitions."""
    return [
        ("cr1", "cr1_avg5", 5),
        ("cr2", "cr2_avg5", 5),
        ("cr1", "cr1_avg15", 15),
        ("cr2", "cr2_avg15", 15),
        ("cr1", "cr1_avg30", 30),
        ("cr2", "cr2_avg30", 30),
    ]


def _add_lag_feature(
    frame: pd.DataFrame,
    source_column: str,
    target_column: str,
    days: int,
) -> pd.DataFrame:
    """Add an exact date lag feature with current value fallback."""
    lag = frame[["sku", "stats_date", source_column]].copy()
    lag["stats_date"] = lag["stats_date"] + pd.Timedelta(days=days)
    lag = lag.rename(columns={source_column: target_column})
    joined = frame.merge(lag, on=["sku", "stats_date"], how="left")
    joined[target_column] = joined[target_column].fillna(joined[source_column])
    return joined


def _add_average_feature(
    frame: pd.DataFrame,
    source_column: str,
    target_column: str,
    days: int,
) -> pd.DataFrame:
    """Add a previous-days average feature with current value fallback."""
    values = frame[["sku", "stats_date", source_column]].copy()
    targets = frame[["sku", "stats_date"]].reset_index(names="row_id")
    pairs = targets.merge(values, on="sku", suffixes=("", "_source"))
    pairs = _filter_average_window(pairs, days)
    averages = pairs.groupby("row_id")[source_column].mean()
    result = frame.copy()
    mapped = pd.Series(result.index.map(averages), index=result.index)
    result[target_column] = mapped.fillna(result[source_column])
    return result


def _filter_average_window(frame: pd.DataFrame, days: int) -> pd.DataFrame:
    """Keep source rows from [target date - days, target date - 1]."""
    lower_bound = frame["stats_date"] - pd.Timedelta(days=days)
    upper_bound = frame["stats_date"] - pd.Timedelta(days=1)
    in_window = frame["stats_date_source"].between(lower_bound, upper_bound)
    return frame.loc[in_window]
