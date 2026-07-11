"""Create source tables used by the optimization pipeline."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260711_0002"
down_revision = "20260707_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create source tables that are not present yet."""
    existing_tables = set(
        sa.inspect(op.get_bind()).get_table_names(schema="public"),
    )

    if "oz_category" not in existing_tables:
        op.create_table(
            "oz_category",
            sa.Column("type_id", sa.BigInteger(), nullable=False),
            sa.Column("category_1_name", sa.Text(), nullable=False),
            sa.Column("category_2_name", sa.Text(), nullable=False),
            sa.Column("type_name", sa.Text(), nullable=False),
            sa.PrimaryKeyConstraint("type_id"),
            schema="public",
        )

    if "oz_product" not in existing_tables:
        op.create_table(
            "oz_product",
            sa.Column("sku", sa.BigInteger(), nullable=False),
            sa.Column("offer_id", sa.Text(), nullable=False),
            sa.Column("type_id", sa.BigInteger(), nullable=False),
            sa.Column("customer_key", sa.Text(), nullable=False),
            sa.PrimaryKeyConstraint("sku"),
            schema="public",
        )

    if "oz_marketing_stat_rk" not in existing_tables:
        op.create_table(
            "oz_marketing_stat_rk",
            sa.Column("models_sku", sa.BigInteger(), nullable=False),
            sa.Column("date_period", sa.Date(), nullable=False),
            sa.Column("expences", sa.Numeric(18, 4), nullable=False),
            sa.Column("revenue", sa.Numeric(18, 4), nullable=False),
            sa.Column("date_load", sa.DateTime(), nullable=False),
            sa.Column("customer_key", sa.Text(), nullable=False),
            schema="public",
        )

    if "oz_prices" not in existing_tables:
        op.create_table(
            "oz_prices",
            sa.Column("product_id", sa.BigInteger(), nullable=False),
            sa.Column("offer_id", sa.Text(), nullable=False),
            sa.Column("price", sa.Numeric(18, 4), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("customer_key", sa.Text(), nullable=False),
            schema="public",
        )

    if "cost_price_data_test" not in existing_tables:
        op.create_table(
            "cost_price_data_test",
            sa.Column("marketplace_product_id", sa.BigInteger(), nullable=False),
            sa.Column("sku", sa.Text(), nullable=False),
            sa.Column("self_cost", sa.Numeric(18, 4), nullable=False),
            sa.Column("date_load", sa.DateTime(), nullable=False),
            sa.Column("customer_key", sa.Text(), nullable=False),
            schema="public",
        )

    if "company_register_data" not in existing_tables:
        op.create_table(
            "company_register_data",
            sa.Column("customer_key", sa.Text(), nullable=False),
            sa.Column("project_index", sa.Text(), nullable=False),
            sa.PrimaryKeyConstraint("customer_key"),
            schema="public",
        )

    if "oz_voronka_sales" not in existing_tables:
        op.create_table(
            "oz_voronka_sales",
            sa.Column("id", sa.BigInteger(), nullable=False),
            sa.Column("date_load", sa.DateTime(), nullable=False),
            sa.Column("customer_key", sa.Text(), nullable=False),
            sa.Column("company_name", sa.Text(), nullable=False),
            sa.Column("name", sa.Text(), nullable=False),
            sa.Column("sku", sa.BigInteger(), nullable=False),
            sa.Column("date_period", sa.Date(), nullable=False),
            sa.Column("revenue", sa.Numeric(18, 4), nullable=False),
            sa.Column("ordered_units", sa.BigInteger(), nullable=False),
            sa.Column("position_category", sa.Numeric(10, 4), nullable=False),
            sa.Column("hits_view", sa.BigInteger(), nullable=False),
            sa.Column("hits_view_pdp", sa.BigInteger(), nullable=False),
            sa.Column("hits_view_search", sa.BigInteger(), nullable=False),
            sa.Column("hits_tocart", sa.BigInteger(), nullable=False),
            sa.Column("hits_tocart_pdp", sa.BigInteger(), nullable=False),
            sa.Column("session_view", sa.BigInteger(), nullable=False),
            sa.Column("session_view_pdp", sa.BigInteger(), nullable=False),
            sa.Column("session_view_search", sa.BigInteger(), nullable=False),
            sa.Column("conv_tocart", sa.Numeric(10, 4), nullable=False),
            sa.Column("conv_tocart_pdp", sa.Numeric(10, 4), nullable=False),
            sa.Column("conv_tocart_search", sa.Numeric(10, 4), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            schema="public",
        )


def downgrade() -> None:
    """Drop source tables."""
    op.drop_table("oz_voronka_sales", schema="public")
    op.drop_table("company_register_data", schema="public")
    op.drop_table("cost_price_data_test", schema="public")
    op.drop_table("oz_prices", schema="public")
    op.drop_table("oz_marketing_stat_rk", schema="public")
    op.drop_table("oz_product", schema="public")
    op.drop_table("oz_category", schema="public")
