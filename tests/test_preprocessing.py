from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from services.preprocessing import calculate_history_features


def test_calculate_history_features_uses_exact_date_lags() -> None:
    frame = pd.DataFrame(
        {
            "sku": [1, 1, 1],
            "stats_date": [date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 4)],
            "cr1": [0.10, 0.20, 0.40],
            "cr2": [0.30, 0.35, 0.45],
            "advertising_budget_today": [0.1, 0.2, 0.4],
            "advertising_pressure_today": [10, 20, 40],
            "search_and_catalog_impressions": [100, 200, 400],
            "search_and_catalog_position": [90, 80, 60],
            "added_to_cart_total": [10, 20, 40],
        },
    )

    result = calculate_history_features(frame)

    second_day = result.loc[result["stats_date"] == pd.Timestamp("2026-01-02")].iloc[0]
    fourth_day = result.loc[result["stats_date"] == pd.Timestamp("2026-01-04")].iloc[0]
    assert second_day["cr1_yesterday"] == 0.10
    assert fourth_day["cr1_yesterday"] == 0.40
    assert fourth_day["cr1_m2"] == 0.20


def test_calculate_history_features_adds_rolling_average() -> None:
    frame = pd.DataFrame(
        {
            "sku": [1, 1, 1],
            "stats_date": [date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)],
            "cr1": [0.10, 0.20, 0.30],
            "cr2": [0.30, 0.40, 0.50],
            "advertising_budget_today": [0.1, 0.2, 0.3],
            "advertising_pressure_today": [10, 20, 30],
            "search_and_catalog_impressions": [100, 200, 300],
            "search_and_catalog_position": [90, 80, 70],
            "added_to_cart_total": [10, 20, 30],
        },
    )

    result = calculate_history_features(frame)

    third_day = result.loc[result["stats_date"] == pd.Timestamp("2026-01-03")].iloc[0]
    assert third_day["cr1_avg5"] == pytest.approx(0.15)
    assert third_day["cr2_avg5"] == pytest.approx(0.35)
