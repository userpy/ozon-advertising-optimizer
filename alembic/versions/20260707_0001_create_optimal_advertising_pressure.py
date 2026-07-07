"""Create optimal advertising pressure result table."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260707_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create result table and indexes."""
    op.create_table(
        "optimal_advertising_pressure",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("stats_date", sa.Date(), nullable=False),
        sa.Column("sku", sa.BigInteger(), nullable=False),
        sa.Column("offer_id", sa.Text(), nullable=True),
        sa.Column("current_pressure", sa.Numeric(10, 4), nullable=False),
        sa.Column("optimal_pressure", sa.Numeric(10, 4), nullable=False),
        sa.Column("expected_position", sa.Numeric(12, 4), nullable=False),
        sa.Column("expected_impressions", sa.Numeric(18, 4), nullable=False),
        sa.Column("expected_cr1", sa.Numeric(12, 9), nullable=False),
        sa.Column("expected_cr2", sa.Numeric(12, 9), nullable=False),
        sa.Column("expected_orders", sa.Numeric(18, 4), nullable=False),
        sa.Column("expected_profit", sa.Numeric(18, 4), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "stats_date",
            "sku",
            name="uq_optimal_pressure_stats_date_sku",
        ),
        schema="public",
    )
    op.create_index(
        "ix_optimal_pressure_stats_date",
        "optimal_advertising_pressure",
        ["stats_date"],
        schema="public",
    )
    op.create_index(
        "ix_optimal_pressure_sku",
        "optimal_advertising_pressure",
        ["sku"],
        schema="public",
    )


def downgrade() -> None:
    """Drop result table and indexes."""
    op.drop_index(
        "ix_optimal_pressure_sku",
        table_name="optimal_advertising_pressure",
        schema="public",
    )
    op.drop_index(
        "ix_optimal_pressure_stats_date",
        table_name="optimal_advertising_pressure",
        schema="public",
    )
    op.drop_table("optimal_advertising_pressure", schema="public")
