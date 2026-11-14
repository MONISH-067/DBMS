-- ============================================================
-- Olist E-Commerce  –  Views
-- Authors: Monish L, Prasannakumar S, S Hari Surendran
-- ============================================================
-- Run after schema.sql:  mysql -u olist_admin -p olist < sql/views.sql
-- ============================================================

USE olist;

DROP VIEW IF EXISTS v_delivery_performance;
DROP VIEW IF EXISTS v_order_summary;

-- ── View 1: v_delivery_performance ─────────────────────────────
-- Joins orders → customers → geolocation.
-- Computes delivery_days and on_time flag for every DELIVERED order.
-- Non-delivered orders are included with NULL delivery metrics.
-- ────────────────────────────────────────────────────────────────
CREATE VIEW v_delivery_performance AS
SELECT
    o.order_id,
    o.customer_id,
    o.order_status,
    o.order_purchase_timestamp,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,
    c.customer_unique_id,
    g.zip_prefix,
    g.city,
    g.state,
    -- Delivery days (NULL when not yet delivered)
    DATEDIFF(o.order_delivered_customer_date,
             o.order_purchase_timestamp)           AS delivery_days,
    -- On-time flag: 1 = on time or early, 0 = late, NULL = not delivered
    CASE
        WHEN o.order_delivered_customer_date IS NULL THEN NULL
        WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date
             THEN 1
        ELSE 0
    END                                             AS is_on_time,
    -- Human-readable delivery outcome
    CASE
        WHEN o.order_delivered_customer_date IS NULL THEN 'not_delivered'
        WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date
             THEN 'on_time'
        ELSE 'late'
    END                                             AS delivery_outcome
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
JOIN geolocation g ON g.zip_prefix = c.zip_prefix;


-- ── View 2: v_order_summary ────────────────────────────────────
-- Aggregates revenue, freight, and item count per order.
-- Joins orders → order_items → products → product_categories.
-- ────────────────────────────────────────────────────────────────
CREATE VIEW v_order_summary AS
SELECT
    o.order_id,
    o.customer_id,
    o.order_status,
    o.order_purchase_timestamp,
    COUNT(oi.order_item_id)                         AS item_count,
    SUM(oi.price)                                   AS total_price,
    SUM(oi.freight_value)                           AS total_freight,
    SUM(oi.price) + SUM(oi.freight_value)           AS total_revenue
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
GROUP BY
    o.order_id,
    o.customer_id,
    o.order_status,
    o.order_purchase_timestamp;
