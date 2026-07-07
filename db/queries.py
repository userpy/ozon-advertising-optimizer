"""Small SQL queries that mirror the legacy view CTEs."""

from __future__ import annotations

DEFAULT_CUSTOMER_KEY = "OZ_2232506"
RESULT_TABLE = "optimal_advertising_pressure"

# Получает справочник товаров с категориями Ozon по клиенту.
CATEGORIES_SQL = """
SELECT
    CAST(product.sku AS bigint) AS sku,
    product.offer_id,
    category.category_1_name,
    category.category_2_name,
    category.type_name
FROM oz_product AS product
LEFT JOIN oz_category AS category ON product.type_id = category.type_id
WHERE product.customer_key = :customer_key
"""

# Получает последнюю рекламную статистику по SKU и дате.
ADVERTISING_SQL = """
SELECT
    ranked.sku,
    ranked.stats_date,
    ranked.advertising_budget_today,
    ranked.advertising_pressure_today
FROM (
    SELECT
        CAST(models_sku AS bigint) AS sku,
        CAST(date_period AS date) AS stats_date,
        expences / revenue AS advertising_budget_today,
        ROUND(expences / revenue * 100, 0) AS advertising_pressure_today,
        ROW_NUMBER() OVER (
            PARTITION BY models_sku, date_period
            ORDER BY date_load DESC
        ) AS row_number
    FROM oz_marketing_stat_rk
    WHERE customer_key = :customer_key
      AND revenue > 0
) AS ranked
WHERE ranked.row_number = 1
"""

# Получает первую зафиксированную цену товара и коэффициент эластичности.
PRICES_SQL = """
SELECT
    ranked.sku,
    ranked.offer_id,
    ranked.morning_price_unchanged,
    ranked.price_elasticity_conversion_views_to_order
FROM (
    SELECT
        product_id AS sku,
        offer_id,
        price AS morning_price_unchanged,
        -3 AS price_elasticity_conversion_views_to_order,
        ROW_NUMBER() OVER (
            PARTITION BY product_id
            ORDER BY created_at
        ) AS row_number
    FROM oz_prices
    WHERE customer_key = :customer_key
) AS ranked
WHERE ranked.row_number = 1
"""

# Получает себестоимость товара из таблицы управленческих данных.
SELF_COST_SQL = """
SELECT
    ranked.sku,
    ranked.offer_id,
    ranked.unit_cost_price
FROM (
    SELECT
        CAST(marketplace_product_id AS bigint) AS sku,
        sku AS offer_id,
        self_cost AS unit_cost_price,
        ROW_NUMBER() OVER (
            PARTITION BY sku
            ORDER BY date_load
        ) AS row_number
    FROM cost_price_data_test
    WHERE customer_key = :customer_key
) AS ranked
WHERE ranked.row_number = 1
"""

# Получает дневную воронку продаж и рассчитывает базовые конверсии CR1/CR2.
SALES_SQL = """
SELECT
    ranked.id,
    ranked.created_at,
    ranked.project_index,
    ranked.customer_key,
    ranked.company_name,
    ranked.product,
    CAST(NULL AS text) AS model,
    ranked.sku,
    ranked.stats_date,
    ranked.ordered_amount,
    ranked.units_ordered,
    ranked.search_and_catalog_position,
    ranked.impressions,
    ranked.pdp_impressions,
    ranked.search_and_catalog_impressions,
    ranked.added_to_cart_total,
    ranked.added_to_cart_from_product_page,
    ranked.unique_visitors,
    ranked.unique_visitors_product_page,
    ranked.unique_visitors_search,
    ranked.cr1,
    ranked.cr1_pdp,
    ranked.cr1_search,
    ranked.cr2,
    ranked.cr2_pdp,
    ranked.product_price,
    CAST(ranked.product_price * 0.5 AS numeric(15, 2)) AS unit_margin,
    CAST(0.9 AS numeric(10, 9)) AS redemption_prct
FROM (
    SELECT
        v.id,
        v.date_load AS created_at,
        v.customer_key,
        v.company_name,
        reg.project_index,
        v.name AS product,
        v.sku,
        v.date_period AS stats_date,
        CAST(v.revenue AS integer) AS ordered_amount,
        CAST(v.ordered_units AS bigint) AS units_ordered,
        CAST(v.position_category AS numeric(6, 2)) AS search_and_catalog_position,
        v.hits_view AS impressions,
        v.hits_view_pdp AS pdp_impressions,
        CAST(v.hits_view_search AS bigint) AS search_and_catalog_impressions,
        CAST(v.hits_tocart AS bigint) AS added_to_cart_total,
        CAST(v.hits_tocart_pdp AS bigint) AS added_to_cart_from_product_page,
        v.session_view AS unique_visitors,
        CAST(v.session_view_pdp AS bigint) AS unique_visitors_product_page,
        v.session_view_search AS unique_visitors_search,
        CAST(v.conv_tocart * 0.01 AS numeric(10, 4)) AS cr1,
        CAST(v.conv_tocart_pdp * 0.01 AS numeric(10, 4)) AS cr1_pdp,
        CAST(v.conv_tocart_search * 0.01 AS numeric(10, 4)) AS cr1_search,
        GREATEST(
            0,
            LEAST(
                1,
                CASE
                    WHEN v.hits_tocart <> 0
                    THEN CAST(v.ordered_units AS numeric(10, 4)) / v.hits_tocart
                    ELSE 0
                END
            )
        ) AS cr2,
        GREATEST(
            0,
            LEAST(
                1,
                CASE
                    WHEN v.hits_tocart_pdp <> 0
                    THEN CAST(v.ordered_units AS numeric(10, 4)) / v.hits_tocart_pdp
                    ELSE 0
                END
            )
        ) AS cr2_pdp,
        CASE
            WHEN v.ordered_units <> 0 THEN v.revenue / v.ordered_units
            ELSE NULL
        END AS product_price,
        ROW_NUMBER() OVER (
            PARTITION BY v.sku, v.date_period
            ORDER BY v.position_category
        ) AS row_number
    FROM oz_voronka_sales AS v
    LEFT JOIN company_register_data AS reg ON v.customer_key = reg.customer_key
    WHERE v.customer_key = :customer_key
      AND v.position_category IS NOT NULL
      AND v.ordered_units > 0
      AND v.conv_tocart IS NOT NULL
) AS ranked
WHERE ranked.row_number = 1
"""
