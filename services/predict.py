"""Prediction services with replaceable ML-model placeholders."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd

from services.logging_utils import dataframe_step

PRESSURE_COLUMN = "candidate_pressure"


@dataframe_step("predict_metrics")
def predict_metrics(
    features: pd.DataFrame,
    pressure_values: Iterable[int] | None = None,
    models: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Build pressure scenarios and predict all target metrics."""
    scenarios = build_pressure_scenarios(features, pressure_values)
    scenarios["expected_position"] = predict_position(
        scenarios,
        _model(models, "position"),
    )
    scenarios["expected_impressions"] = predict_impressions(
        scenarios,
        _model(models, "impressions"),
    )
    scenarios["expected_cr1"] = predict_cr1(scenarios, _model(models, "cr1"))
    scenarios["expected_cr2"] = predict_cr2(scenarios, _model(models, "cr2"))
    scenarios["expected_orders"] = predict_orders(scenarios)
    return scenarios


def build_pressure_scenarios(
    features: pd.DataFrame,
    pressure_values: Iterable[int] | None = None,
) -> pd.DataFrame:
    """Duplicate feature rows for every candidate pressure."""
    pressures = list(range(101)) if pressure_values is None else list(pressure_values)
    latest_features = features.copy()
    latest_features["stats_date"] = pd.to_datetime(latest_features["stats_date"])
    latest_indexes = latest_features.groupby("sku")["stats_date"].idxmax()
    scenarios = latest_features.loc[latest_indexes].copy()
    scenarios = scenarios.merge(pd.DataFrame({PRESSURE_COLUMN: pressures}), how="cross")
    return scenarios.reset_index(drop=True)


def predict_position(frame: pd.DataFrame, model: Any | None = None) -> pd.Series:
    """Predict search and catalog position."""
    if model is not None:
        return pd.Series(model.predict(frame), index=frame.index)

    base = _numeric(frame, "search_and_catalog_position_yesterday")
    current = _numeric(frame, "advertising_pressure_yesterday")
    pressure_delta = _numeric(frame, PRESSURE_COLUMN) - current
    predicted = base - pressure_delta * 0.85
    return predicted.clip(lower=1)


def predict_impressions(frame: pd.DataFrame, model: Any | None = None) -> pd.Series:
    """Predict search and catalog impressions."""
    if model is not None:
        return pd.Series(model.predict(frame), index=frame.index)

    base = _numeric(frame, "impressions_yesterday").clip(lower=1)
    pressure_growth = 1 + _numeric(frame, PRESSURE_COLUMN).clip(lower=0) / 180
    position_effect = (
        1 + (100 - _numeric(frame, "expected_position")).clip(lower=0) / 250
    )
    return (base * pressure_growth * position_effect).clip(lower=0)


def predict_cr1(frame: pd.DataFrame, model: Any | None = None) -> pd.Series:
    """Predict conversion from impression to cart."""
    if model is not None:
        return pd.Series(model.predict(frame), index=frame.index).clip(0, 1)

    base = _average_rate(frame, ["cr1_avg15", "cr1_avg5", "cr1_yesterday", "cr1"])
    pressure_bonus = _numeric(frame, PRESSURE_COLUMN) * 0.00035
    return (base + pressure_bonus).clip(lower=0, upper=1)


def predict_cr2(frame: pd.DataFrame, model: Any | None = None) -> pd.Series:
    """Predict conversion from cart to order."""
    if model is not None:
        return pd.Series(model.predict(frame), index=frame.index).clip(0, 1)

    base = _average_rate(frame, ["cr2_avg15", "cr2_avg5", "cr2_yesterday", "cr2"])
    pressure_penalty = _numeric(frame, PRESSURE_COLUMN) * 0.00005
    return (base - pressure_penalty).clip(lower=0, upper=1)


def predict_orders(frame: pd.DataFrame) -> pd.Series:
    """Predict ordered units from impressions and conversion rates."""
    orders = (
        _numeric(frame, "expected_impressions")
        * _numeric(frame, "expected_cr1")
        * _numeric(frame, "expected_cr2")
    )
    return orders.clip(lower=0)


def _model(models: dict[str, Any] | None, name: str) -> Any | None:
    """Return a named optional model."""
    return None if models is None else models.get(name)


def _numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    """Read a numeric column with zero fallback."""
    if column not in frame.columns:
        return pd.Series(0.0, index=frame.index)
    return pd.to_numeric(frame[column], errors="coerce").fillna(0)


def _average_rate(frame: pd.DataFrame, columns: list[str]) -> pd.Series:
    """Average available rate columns by row."""
    present_columns = [column for column in columns if column in frame.columns]
    rates = frame[present_columns].apply(pd.to_numeric, errors="coerce")
    return rates.mean(axis=1).fillna(0).clip(lower=0, upper=1)
