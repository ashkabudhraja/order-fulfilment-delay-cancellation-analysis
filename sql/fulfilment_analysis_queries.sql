
-- =====================================================
-- PROJECT: Order Fulfilment Delay & Cancellation Analysis
-- DATABASE: olist_fulfilment_analysis
-- TOOL: MySQL Workbench
-- DATASET: Public Olist Brazilian E-Commerce Dataset
-- =====================================================

USE olist_fulfilment_analysis;


-- =====================================================
-- QUERY 1: ORDER STATUS DISTRIBUTION
-- Business Question:
-- What is the distribution of orders across different
-- order statuses?
-- =====================================================

SELECT
    order_status,
    COUNT(*) AS total_orders,
    ROUND(
        COUNT(*) * 100.0 /
        (SELECT COUNT(*) FROM olist_orders_dataset),
        2
    ) AS percentage
FROM olist_orders_dataset
GROUP BY order_status
ORDER BY total_orders DESC;


-- =====================================================
-- QUERY 2: OVERALL LATE DELIVERY PERCENTAGE
-- Business Question:
-- What percentage of eligible delivered orders
-- were delivered after their estimated delivery date?
-- =====================================================

SELECT
    COUNT(*) AS eligible_delivered_orders,

    SUM(
        CASE
            WHEN DATE(order_delivered_customer_date) >
                 DATE(order_estimated_delivery_date)
            THEN 1
            ELSE 0
        END
    ) AS late_orders,

    ROUND(
        SUM(
            CASE
                WHEN DATE(order_delivered_customer_date) >
                     DATE(order_estimated_delivery_date)
                THEN 1
                ELSE 0
            END
        ) * 100.0 / COUNT(*),
        2
    ) AS late_delivery_percentage

FROM olist_orders_dataset

WHERE order_status = 'delivered'
AND NULLIF(order_delivered_customer_date, '') IS NOT NULL
AND NULLIF(order_estimated_delivery_date, '') IS NOT NULL;


-- =====================================================
-- QUERY 3: MONTHLY LATE DELIVERY TRENDS
-- Business Question:
-- How does the late delivery percentage change
-- across different order purchase months?
-- =====================================================

SELECT
    DATE_FORMAT(
        STR_TO_DATE(
            order_purchase_timestamp,
            '%Y-%m-%d %H:%i:%s'
        ),
        '%Y-%m'
    ) AS purchase_month,

    COUNT(*) AS eligible_delivered_orders,

    SUM(
        CASE
            WHEN DATE(order_delivered_customer_date) >
                 DATE(order_estimated_delivery_date)
            THEN 1
            ELSE 0
        END
    ) AS late_orders,

    ROUND(
        SUM(
            CASE
                WHEN DATE(order_delivered_customer_date) >
                     DATE(order_estimated_delivery_date)
                THEN 1
                ELSE 0
            END
        ) * 100.0 / COUNT(*),
        2
    ) AS late_delivery_percentage

FROM olist_orders_dataset

WHERE order_status = 'delivered'
AND NULLIF(order_delivered_customer_date, '') IS NOT NULL
AND NULLIF(order_estimated_delivery_date, '') IS NOT NULL

GROUP BY purchase_month
ORDER BY purchase_month;


-- =====================================================
-- QUERY 4: LATE DELIVERY BY PRODUCT CATEGORY
-- Business Question:
-- Which product categories have higher late delivery
-- rates?
-- Minimum eligible orders per category: 100
-- =====================================================

SELECT
    REPLACE(
        COALESCE(t.product_category_name_english, 'Unknown'),
        '\r',
        ''
    ) AS product_category,

    COUNT(DISTINCT o.order_id) AS eligible_orders,

    COUNT(DISTINCT
        CASE
            WHEN DATE(o.order_delivered_customer_date) >
                 DATE(o.order_estimated_delivery_date)
            THEN o.order_id
        END
    ) AS late_orders,

    ROUND(
        COUNT(DISTINCT
            CASE
                WHEN DATE(o.order_delivered_customer_date) >
                     DATE(o.order_estimated_delivery_date)
                THEN o.order_id
            END
        ) * 100.0 / COUNT(DISTINCT o.order_id),
        2
    ) AS late_delivery_percentage

FROM olist_orders_dataset o

JOIN olist_order_items_dataset i
    ON o.order_id = i.order_id

JOIN olist_products_dataset p
    ON i.product_id = p.product_id

LEFT JOIN product_category_name_translation t
    ON p.product_category_name = t.product_category_name

WHERE o.order_status = 'delivered'
AND NULLIF(o.order_delivered_customer_date, '') IS NOT NULL
AND NULLIF(o.order_estimated_delivery_date, '') IS NOT NULL

GROUP BY product_category

HAVING COUNT(DISTINCT o.order_id) >= 100

ORDER BY late_delivery_percentage DESC;


-- =====================================================
-- QUERY 5: LATE DELIVERY BY SELLER
-- Business Question:
-- Which sellers have higher late delivery rates?
-- Minimum eligible orders per seller: 30
-- =====================================================

SELECT
    i.seller_id,

    COUNT(DISTINCT o.order_id) AS eligible_orders,

    COUNT(DISTINCT
        CASE
            WHEN DATE(o.order_delivered_customer_date) >
                 DATE(o.order_estimated_delivery_date)
            THEN o.order_id
        END
    ) AS late_orders,

    ROUND(
        COUNT(DISTINCT
            CASE
                WHEN DATE(o.order_delivered_customer_date) >
                     DATE(o.order_estimated_delivery_date)
                THEN o.order_id
            END
        ) * 100.0 /
        COUNT(DISTINCT o.order_id),
        2
    ) AS late_delivery_percentage

FROM olist_orders_dataset o

JOIN olist_order_items_dataset i
    ON o.order_id = i.order_id

WHERE o.order_status = 'delivered'
AND NULLIF(o.order_delivered_customer_date, '') IS NOT NULL
AND NULLIF(o.order_estimated_delivery_date, '') IS NOT NULL

GROUP BY i.seller_id

HAVING COUNT(DISTINCT o.order_id) >= 30

ORDER BY late_delivery_percentage DESC;


-- =====================================================
-- END OF PROJECT SQL QUERIES
-- =====================================================
