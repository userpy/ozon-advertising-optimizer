"""Seed PostgreSQL with deterministic test data for the optimizer."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import MetaData, create_engine, text

from db.connection import get_database_url
from db.queries import DEFAULT_CUSTOMER_KEY

LOGGER = logging.getLogger(__name__)
COMPANY_NAME = "Fuji Test Seller"
PROJECT_INDEX = "fuji-oz-2232506"


def main() -> None:
    """Create source tables and insert deterministic sample data."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    engine = create_engine(get_database_url(), pool_pre_ping=True, future=True)
    with engine.begin() as connection:
        LOGGER.info("Creating source tables")
        for statement in _source_table_ddl():
            connection.execute(text(statement))

        LOGGER.info("Cleaning old seed data")
        connection.execute(text(_truncate_statement()))
        connection.execute(text(_truncate_results_statement()))

        LOGGER.info("Inserting seed data")
        metadata = MetaData()
        metadata.reflect(bind=connection, schema="public", only=_source_table_names())
        for table_name, rows in _build_seed_payload().items():
            if rows:
                table = metadata.tables[f"public.{table_name}"]
                connection.execute(table.insert(), rows)

    LOGGER.info("Seed completed")


def _source_table_names() -> list[str]:
    """Return all source table names used by the pipeline."""
    return [
        "oz_category",
        "oz_product",
        "oz_marketing_stat_rk",
        "oz_prices",
        "cost_price_data_test",
        "company_register_data",
        "oz_voronka_sales",
    ]


def _source_table_ddl() -> list[str]:
    """Return source table DDL statements."""
    return [
        """
        CREATE TABLE IF NOT EXISTS public.oz_category (
            type_id bigint PRIMARY KEY,
            category_1_name text NOT NULL,
            category_2_name text NOT NULL,
            type_name text NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS public.oz_product (
            sku bigint PRIMARY KEY,
            offer_id text NOT NULL,
            type_id bigint NOT NULL,
            customer_key text NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS public.oz_marketing_stat_rk (
            models_sku bigint NOT NULL,
            date_period date NOT NULL,
            expences numeric(18, 4) NOT NULL,
            revenue numeric(18, 4) NOT NULL,
            date_load timestamp NOT NULL,
            customer_key text NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS public.oz_prices (
            product_id bigint NOT NULL,
            offer_id text NOT NULL,
            price numeric(18, 4) NOT NULL,
            created_at timestamp NOT NULL,
            customer_key text NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS public.cost_price_data_test (
            marketplace_product_id bigint NOT NULL,
            sku text NOT NULL,
            self_cost numeric(18, 4) NOT NULL,
            date_load timestamp NOT NULL,
            customer_key text NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS public.company_register_data (
            customer_key text PRIMARY KEY,
            project_index text NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS public.oz_voronka_sales (
            id bigint PRIMARY KEY,
            date_load timestamp NOT NULL,
            customer_key text NOT NULL,
            company_name text NOT NULL,
            name text NOT NULL,
            sku bigint NOT NULL,
            date_period date NOT NULL,
            revenue numeric(18, 4) NOT NULL,
            ordered_units bigint NOT NULL,
            position_category numeric(10, 4) NOT NULL,
            hits_view bigint NOT NULL,
            hits_view_pdp bigint NOT NULL,
            hits_view_search bigint NOT NULL,
            hits_tocart bigint NOT NULL,
            hits_tocart_pdp bigint NOT NULL,
            session_view bigint NOT NULL,
            session_view_pdp bigint NOT NULL,
            session_view_search bigint NOT NULL,
            conv_tocart numeric(10, 4) NOT NULL,
            conv_tocart_pdp numeric(10, 4) NOT NULL,
            conv_tocart_search numeric(10, 4) NOT NULL
        )
        """,
    ]


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
