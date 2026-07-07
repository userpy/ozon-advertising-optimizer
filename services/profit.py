"""Profit calculation and optimal pressure selection."""

from __future__ import annotations

import pandas as pd

from services.logging_utils import dataframe_step


@dataframe_step("calculate_profit")
def calculate_profit(predictions: pd.DataFrame) -> pd.DataFrame:
    """Calculate expected profit for each pressure scenario."""
    frame = predictions.copy()
    revenue = _expected_revenue(frame)
    advertising_cost = revenue * _numeric(frame, "candidate_pressure") / 100
    variable_cost = _numeric(frame, "expected_orders") * _unit_cost(frame)
    frame["expected_profit"] = revenue - advertising_cost - variable_cost
    return frame


@dataframe_step("select_best_pressure")
def select_best_pressure(profit_frame: pd.DataFrame) -> pd.DataFrame:
    """Select the highest-profit pressure for every SKU."""
    sorted_frame = profit_frame.sort_values(
        ["sku", "expected_profit", "candidate_pressure"],
        ascending=[True, False, True],
    )
    best_rows = sorted_frame.drop_duplicates(["sku", "stats_date"], keep="first")
    result = best_rows.rename(
        columns={
            "advertising_pressure_today": "current_pressure",
            "candidate_pressure": "optimal_pressure",
        },
    )
    return result[_result_columns()].reset_index(drop=True)


def _expected_revenue(frame: pd.DataFrame) -> pd.Series:
    """Calculate revenue after redemption."""
    return (
        _numeric(frame, "expected_orders")
        * _numeric(frame, "product_price")
        * _numeric(frame, "redemption_prct").replace(0, 1)
    )


def _unit_cost(frame: pd.DataFrame) -> pd.Series:
    """Calculate per-unit cost with fallback to margin data."""
    explicit_cost = _numeric(frame, "unit_cost_price")
    inferred_cost = _numeric(frame, "product_price") - _numeric(frame, "unit_margin")
    base_cost = explicit_cost.where(explicit_cost > 0, inferred_cost)
    return base_cost + _numeric(frame, "base_fixed_cost_per_unit")


def _numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    """Read a numeric column with zero fallback."""
    if column not in frame.columns:
        return pd.Series(0.0, index=frame.index)
    return pd.to_numeric(frame[column], errors="coerce").fillna(0)


def _result_columns() -> list[str]:
    """Return persisted result columns."""
    return [
        "stats_date",
        "sku",
        "offer_id",
        "current_pressure",
        "optimal_pressure",
        "expected_position",
        "expected_impressions",
        "expected_cr1",
        "expected_cr2",
        "expected_orders",
        "expected_profit",
    ]
