"""Seed PostgreSQL with deterministic test data for the optimizer."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import create_engine, text

from db.models import SOURCE_TABLES
from db.queries import DEFAULT_CUSTOMER_KEY
from services.settings import Settings

LOGGER = logging.getLogger(__name__)
COMPANY_NAME = "Fuji Test Seller"
PROJECT_INDEX = "fuji-oz-2232506"


def main() -> None:
    """Replace source table contents with deterministic sample data."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    engine = create_engine(
        Settings().database_url,
        pool_pre_ping=True,
        future=True,
    )
    with engine.begin() as connection:
        LOGGER.info("Cleaning old seed data")
        connection.execute(text(_truncate_statement()))
        connection.execute(text(_truncate_results_statement()))

        LOGGER.info("Inserting seed data")
        for table_name, rows in _build_seed_payload().items():
            if rows:
                table = SOURCE_TABLES[table_name]
                connection.execute(table.insert(), rows)

    LOGGER.info("Seed completed")


def _source_table_names() -> list[str]:
    """Return all source table names used by the pipeline."""
    return list(SOURCE_TABLES)


def _truncate_statement() -> str:
    """Return a truncate statement for repeatable seeding."""
    tables = ", ".join(f"public.{name}" for name in _source_table_names())
    return f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"


def _truncate_results_statement() -> str:
    """Return a safe truncate statement for generated optimizer results."""
    return """
    DO $$
    BEGIN
        IF to_regclass('public.optimal_advertising_pressure') IS NOT NULL THEN
            TRUNCATE TABLE public.optimal_advertising_pressure RESTART IDENTITY;
        END IF;
    END $$;
    """


def _build_seed_payload() -> dict[str, list[dict[str, Any]]]:
    """Build linked deterministic source rows."""
    categories = _category_rows()
    products = _product_rows()
    prices = _price_rows(products)
    costs = _cost_rows(products)
    marketing, sales = _fact_rows(products)
    return {
        "oz_category": categories,
        "oz_product": products,
        "oz_marketing_stat_rk": marketing,
        "oz_prices": prices,
        "cost_price_data_test": costs,
        "company_register_data": [_company_row()],
        "oz_voronka_sales": sales,
    }


def _category_rows() -> list[dict[str, Any]]:
    """Create category dictionary rows."""
    return [
        _category(1, "Electronics", "Photo", "Instant camera"),
        _category(2, "Electronics", "Accessories", "Camera film"),
        _category(3, "Home", "Decor", "Photo frame"),
    ]


def _category(
    type_id: int,
    category_1_name: str,
    category_2_name: str,
    type_name: str,
) -> dict[str, Any]:
    """Build one category row."""
    return {
        "type_id": type_id,
        "category_1_name": category_1_name,
        "category_2_name": category_2_name,
        "type_name": type_name,
    }


def _product_rows() -> list[dict[str, Any]]:
    """Create ten products."""
    rows = []
    for index in range(10):
        rows.append(
            {
                "sku": 2232506000 + index,
                "offer_id": f"FUJI-{index + 1:03d}",
                "type_id": index % 3 + 1,
                "customer_key": DEFAULT_CUSTOMER_KEY,
            },
        )
    return rows


def _price_rows(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create one price row per product."""
    loaded_at = datetime(2026, 1, 1, 8, 0)
    return [
        {
            "product_id": product["sku"],
            "offer_id": product["offer_id"],
            "price": _money(1200 + index * 75),
            "created_at": loaded_at,
            "customer_key": DEFAULT_CUSTOMER_KEY,
        }
        for index, product in enumerate(products)
    ]


def _cost_rows(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create one self-cost row per product."""
    loaded_at = datetime(2026, 1, 1, 8, 10)
    return [
        {
            "marketplace_product_id": product["sku"],
            "sku": product["offer_id"],
            "self_cost": _money((1200 + index * 75) * 0.45),
            "date_load": loaded_at,
            "customer_key": DEFAULT_CUSTOMER_KEY,
        }
        for index, product in enumerate(products)
    ]


def _company_row() -> dict[str, Any]:
    """Create the company register row."""
    return {
        "customer_key": DEFAULT_CUSTOMER_KEY,
        "project_index": PROJECT_INDEX,
    }


def _fact_rows(
    products: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Create linked marketing and sales facts."""
    marketing_rows: list[dict[str, Any]] = []
    sales_rows: list[dict[str, Any]] = []
    start_date = date(2026, 1, 1)
    for product_index, product in enumerate(products):
        for day_index in range(10):
            metrics = _daily_metrics(product_index, day_index)
            stats_date = start_date + timedelta(days=day_index)
            sales_rows.append(
                _sales_row(product, stats_date, metrics, len(sales_rows) + 1),
            )
            marketing_rows.append(_marketing_row(product, stats_date, metrics))
    return marketing_rows, sales_rows


def _daily_metrics(product_index: int, day_index: int) -> dict[str, Any]:
    """Calculate coherent metrics for one SKU and day."""
    pressure = min(100, 6 + day_index * 4 + product_index % 4)
    position = max(1, 180 - pressure * 1.15 - day_index * 2 - product_index * 2)
    impressions = int(450 + pressure * 18 + day_index * 21 + product_index * 35)
    cr1 = min(0.35, 0.045 + pressure * 0.0012 + product_index * 0.0008)
    cr2 = min(0.65, 0.19 + pressure * 0.001 + day_index * 0.002)
    carts = max(1, int(impressions * cr1))
    orders = max(1, int(carts * cr2))
    product_price = 1200 + product_index * 75
    revenue = orders * product_price
    return {
        "pressure": pressure,
        "position": position,
        "impressions": impressions,
        "cr1": cr1,
        "cr2": cr2,
        "carts": carts,
        "orders": orders,
        "price": product_price,
        "revenue": revenue,
    }


def _sales_row(
    product: dict[str, Any],
    stats_date: date,
    metrics: dict[str, Any],
    row_id: int,
) -> dict[str, Any]:
    """Build one sales funnel row."""
    loaded_at = datetime.combine(stats_date, datetime.min.time()) + timedelta(hours=9)
    return {
        "id": row_id,
        "date_load": loaded_at,
        "customer_key": DEFAULT_CUSTOMER_KEY,
        "company_name": COMPANY_NAME,
        "name": f"Product {product['offer_id']}",
        "sku": product["sku"],
        "date_period": stats_date,
        "revenue": _money(metrics["revenue"]),
        "ordered_units": metrics["orders"],
        "position_category": _money(metrics["position"]),
        "hits_view": metrics["impressions"] + 120,
        "hits_view_pdp": metrics["impressions"] // 2,
        "hits_view_search": metrics["impressions"],
        "hits_tocart": metrics["carts"],
        "hits_tocart_pdp": max(1, int(metrics["carts"] * 0.62)),
        "session_view": metrics["impressions"] // 2,
        "session_view_pdp": metrics["impressions"] // 3,
        "session_view_search": metrics["impressions"] // 2,
        "conv_tocart": _money(metrics["cr1"] * 100),
        "conv_tocart_pdp": _money(metrics["cr1"] * 92),
        "conv_tocart_search": _money(metrics["cr1"] * 108),
    }


def _marketing_row(
    product: dict[str, Any],
    stats_date: date,
    metrics: dict[str, Any],
) -> dict[str, Any]:
    """Build one advertising statistics row."""
    loaded_at = datetime.combine(stats_date, datetime.min.time()) + timedelta(hours=11)
    return {
        "models_sku": product["sku"],
        "date_period": stats_date,
        "expences": _money(metrics["revenue"] * metrics["pressure"] / 100),
        "revenue": _money(metrics["revenue"]),
        "date_load": loaded_at,
        "customer_key": DEFAULT_CUSTOMER_KEY,
    }


def _money(value: float | int) -> Decimal:
    """Convert numeric values to a two-decimal Decimal."""
    return Decimal(str(round(value, 2)))


if __name__ == "__main__":
    main()
