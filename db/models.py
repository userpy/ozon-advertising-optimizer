"""SQLAlchemy table declarations."""

from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    Index,
    Integer,
    MetaData,
    Numeric,
    Table,
    Text,
    UniqueConstraint,
    func,
)

metadata = MetaData(schema="public")

# Справочник категорий товаров Ozon.
oz_category = Table(
    "oz_category",
    metadata,
    Column("type_id", BigInteger, primary_key=True),
    Column("category_1_name", Text, nullable=False),
    Column("category_2_name", Text, nullable=False),
    Column("type_name", Text, nullable=False),
)

# Товары продавца с привязкой к категории и клиенту.
oz_product = Table(
    "oz_product",
    metadata,
    Column("sku", BigInteger, primary_key=True),
    Column("offer_id", Text, nullable=False),
    Column("type_id", BigInteger, nullable=False),
    Column("customer_key", Text, nullable=False),
)

# Дневная статистика расходов и выручки рекламных кампаний.
oz_marketing_stat_rk = Table(
    "oz_marketing_stat_rk",
    metadata,
    Column("models_sku", BigInteger, nullable=False),
    Column("date_period", Date, nullable=False),
    Column("expences", Numeric(18, 4), nullable=False),
    Column("revenue", Numeric(18, 4), nullable=False),
    Column("date_load", DateTime, nullable=False),
    Column("customer_key", Text, nullable=False),
)

# История цен товаров продавца.
oz_prices = Table(
    "oz_prices",
    metadata,
    Column("product_id", BigInteger, nullable=False),
    Column("offer_id", Text, nullable=False),
    Column("price", Numeric(18, 4), nullable=False),
    Column("created_at", DateTime, nullable=False),
    Column("customer_key", Text, nullable=False),
)

# Себестоимость товаров из управленческих данных.
cost_price_data_test = Table(
    "cost_price_data_test",
    metadata,
    Column("marketplace_product_id", BigInteger, nullable=False),
    Column("sku", Text, nullable=False),
    Column("self_cost", Numeric(18, 4), nullable=False),
    Column("date_load", DateTime, nullable=False),
    Column("customer_key", Text, nullable=False),
)

# Связь клиента с индексом проекта.
company_register_data = Table(
    "company_register_data",
    metadata,
    Column("customer_key", Text, primary_key=True),
    Column("project_index", Text, nullable=False),
)

# Дневная воронка продаж и конверсии товаров Ozon.
oz_voronka_sales = Table(
    "oz_voronka_sales",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("date_load", DateTime, nullable=False),
    Column("customer_key", Text, nullable=False),
    Column("company_name", Text, nullable=False),
    Column("name", Text, nullable=False),
    Column("sku", BigInteger, nullable=False),
    Column("date_period", Date, nullable=False),
    Column("revenue", Numeric(18, 4), nullable=False),
    Column("ordered_units", BigInteger, nullable=False),
    Column("position_category", Numeric(10, 4), nullable=False),
    Column("hits_view", BigInteger, nullable=False),
    Column("hits_view_pdp", BigInteger, nullable=False),
    Column("hits_view_search", BigInteger, nullable=False),
    Column("hits_tocart", BigInteger, nullable=False),
    Column("hits_tocart_pdp", BigInteger, nullable=False),
    Column("session_view", BigInteger, nullable=False),
    Column("session_view_pdp", BigInteger, nullable=False),
    Column("session_view_search", BigInteger, nullable=False),
    Column("conv_tocart", Numeric(10, 4), nullable=False),
    Column("conv_tocart_pdp", Numeric(10, 4), nullable=False),
    Column("conv_tocart_search", Numeric(10, 4), nullable=False),
)

SOURCE_TABLES = {
    table.name: table
    for table in (
        oz_category,
        oz_product,
        oz_marketing_stat_rk,
        oz_prices,
        cost_price_data_test,
        company_register_data,
        oz_voronka_sales,
    )
}

# Результаты расчёта оптимального рекламного давления.
optimal_advertising_pressure = Table(
    "optimal_advertising_pressure",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("stats_date", Date, nullable=False),
    Column("sku", BigInteger, nullable=False),
    Column("offer_id", Text, nullable=True),
    Column("current_pressure", Numeric(10, 4), nullable=False),
    Column("optimal_pressure", Numeric(10, 4), nullable=False),
    Column("expected_position", Numeric(12, 4), nullable=False),
    Column("expected_impressions", Numeric(18, 4), nullable=False),
    Column("expected_cr1", Numeric(12, 9), nullable=False),
    Column("expected_cr2", Numeric(12, 9), nullable=False),
    Column("expected_orders", Numeric(18, 4), nullable=False),
    Column("expected_profit", Numeric(18, 4), nullable=False),
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    ),
    UniqueConstraint("stats_date", "sku", name="uq_optimal_pressure_stats_date_sku"),
    Index("ix_optimal_pressure_stats_date", "stats_date"),
    Index("ix_optimal_pressure_sku", "sku"),
)
