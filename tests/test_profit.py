from __future__ import annotations

from datetime import date

import pandas as pd

from services.profit import calculate_profit, select_best_pressure


def test_calculate_profit_subtracts_ads_and_costs() -> None:
    predictions = pd.DataFrame(
        {
            "expected_orders": [10],
            "product_price": [100],
            "redemption_prct": [1],
            "candidate_pressure": [10],
            "unit_cost_price": [40],
            "unit_margin": [60],
            "base_fixed_cost_per_unit": [1],
        },
    )

    result = calculate_profit(predictions)

    assert result.loc[0, "expected_profit"] == 490


def test_select_best_pressure_returns_required_columns() -> None:
    frame = pd.DataFrame(
        {
            "stats_date": [date(2026, 1, 1), date(2026, 1, 1)],
            "sku": [1, 1],
            "offer_id": ["A-1", "A-1"],
            "advertising_pressure_today": [15, 15],
            "candidate_pressure": [20, 30],
            "expected_position": [80, 70],
            "expected_impressions": [1000, 1200],
            "expected_cr1": [0.10, 0.11],
            "expected_cr2": [0.20, 0.20],
            "expected_orders": [20, 26.4],
            "expected_profit": [100, 150],
        },
    )

    result = select_best_pressure(frame)

    assert result.loc[0, "optimal_pressure"] == 30
    assert result.loc[0, "current_pressure"] == 15
