from __future__ import annotations

from datetime import date

import pandas as pd

from services.predict import predict_metrics


def test_predict_metrics_expands_pressure_grid() -> None:
    features = _features()

    result = predict_metrics(features, pressure_values=[0, 50, 100])

    assert result["candidate_pressure"].tolist() == [0, 50, 100]
    assert "expected_orders" in result.columns


def test_predict_metrics_improves_position_with_more_pressure() -> None:
    features = _features()

    result = predict_metrics(features, pressure_values=[0, 100])

    low_pressure = result.loc[result["candidate_pressure"] == 0].iloc[0]
    high_pressure = result.loc[result["candidate_pressure"] == 100].iloc[0]
    assert high_pressure["expected_position"] < low_pressure["expected_position"]
    assert high_pressure["expected_impressions"] > low_pressure["expected_impressions"]


def _features() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "sku": [1],
            "stats_date": [date(2026, 1, 1)],
            "offer_id": ["A-1"],
            "advertising_pressure_today": [10],
            "advertising_pressure_yesterday": [10],
            "search_and_catalog_position_yesterday": [100],
            "impressions_yesterday": [1000],
            "cr1": [0.10],
            "cr1_yesterday": [0.10],
            "cr1_avg5": [0.10],
            "cr1_avg15": [0.10],
            "cr2": [0.20],
            "cr2_yesterday": [0.20],
            "cr2_avg5": [0.20],
            "cr2_avg15": [0.20],
            "product_price": [1000],
            "unit_cost_price": [450],
            "unit_margin": [500],
            "base_fixed_cost_per_unit": [0.5],
            "redemption_prct": [0.9],
        },
    )
