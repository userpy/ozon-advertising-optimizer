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
