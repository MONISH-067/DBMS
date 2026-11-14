-- ============================================================
-- Olist E-Commerce  –  Report Queries (R01 – R10)
-- Authors: Monish L, Prasannakumar S, S Hari Surendran
-- ============================================================
-- Reference copy of every parameterized report query.
-- The canonical versions live in app/reports.py (report registry).
-- Parameters use %(name)s syntax for mysql-connector-python.
--
-- Optional filters follow the pattern:
--   (%(param)s IS NULL OR column = %(param)s)
-- so passing NULL means "no filter".
--
-- SQL features used across the set:
--   JOINs          : R01-R10
--   GROUP BY       : R01-R10
--   HAVING         : R06
--   Subquery       : R07
--   CASE           : R06, R09, R10
--   Views          : R05, R06, R09, R10 (v_delivery_performance)
--   Window function: R07 (RANK() OVER)
-- ============================================================

USE olist;

-- ────────────────────────────────────────────────────────────────
-- R01  Monthly Orders  (line chart)
-- ────────────────────────────────────────────────────────────────
-- Counts orders per calendar month.
SELECT
    DATE_FORMAT(o.order_purchase_timestamp, '%%Y-%%m')  AS order_month,
    COUNT(*)                                            AS order_count
FROM orders o
WHERE (%(start_date)s IS NULL OR o.order_purchase_timestamp >= %(start_date)s)
  AND (%(end_date)s   IS NULL OR o.order_purchase_timestamp <  %(end_date)s)
  AND (%(status)s     IS NULL OR o.order_status = %(status)s)
GROUP BY order_month
ORDER BY order_month;


-- ────────────────────────────────────────────────────────────────
-- R02  Order Status Share  (donut chart)
-- ────────────────────────────────────────────────────────────────
SELECT
    o.order_status,
    COUNT(*)    AS order_count
FROM orders o
WHERE (%(start_date)s IS NULL OR o.order_purchase_timestamp >= %(start_date)s)
  AND (%(end_date)s   IS NULL OR o.order_purchase_timestamp <  %(end_date)s)
GROUP BY o.order_status
ORDER BY order_count DESC;


-- ────────────────────────────────────────────────────────────────
-- R03  Top 10 States by Orders  (horizontal bar)
-- ────────────────────────────────────────────────────────────────
SELECT
    g.state,
    COUNT(*)    AS order_count
FROM orders o
JOIN customers c  ON c.customer_id = o.customer_id
JOIN geolocation g ON g.zip_prefix = c.zip_prefix
WHERE (%(start_date)s IS NULL OR o.order_purchase_timestamp >= %(start_date)s)
  AND (%(end_date)s   IS NULL OR o.order_purchase_timestamp <  %(end_date)s)
  AND (%(status)s     IS NULL OR o.order_status = %(status)s)
GROUP BY g.state
ORDER BY order_count DESC
LIMIT 10;


-- ────────────────────────────────────────────────────────────────
-- R04  Payment Type Share  (donut chart)
-- ────────────────────────────────────────────────────────────────
SELECT
    op.payment_type,
    SUM(op.payment_value)   AS total_value,
    COUNT(*)                AS payment_count
FROM order_payments op
JOIN orders o ON o.order_id = op.order_id
WHERE (%(start_date)s IS NULL OR o.order_purchase_timestamp >= %(start_date)s)
  AND (%(end_date)s   IS NULL OR o.order_purchase_timestamp <  %(end_date)s)
GROUP BY op.payment_type
ORDER BY total_value DESC;


-- ────────────────────────────────────────────────────────────────
-- R05  Avg Delivery Days by Month  (line chart)
-- Uses view: v_delivery_performance
-- ────────────────────────────────────────────────────────────────
SELECT
    DATE_FORMAT(vdp.order_purchase_timestamp, '%%Y-%%m') AS order_month,
    ROUND(AVG(vdp.delivery_days), 1)                     AS avg_delivery_days
FROM v_delivery_performance vdp
WHERE vdp.delivery_days IS NOT NULL
  AND (%(start_date)s IS NULL OR vdp.order_purchase_timestamp >= %(start_date)s)
  AND (%(end_date)s   IS NULL OR vdp.order_purchase_timestamp <  %(end_date)s)
  AND (%(state)s      IS NULL OR vdp.state = %(state)s)
GROUP BY order_month
ORDER BY order_month;


-- ────────────────────────────────────────────────────────────────
-- R06  On-Time vs Late Deliveries by State  (grouped bar)
-- Uses view: v_delivery_performance
-- HAVING count >= 500 to show only high-volume states.
-- ────────────────────────────────────────────────────────────────
SELECT
    sub.state,
    sub.delivery_outcome,
    sub.cnt
FROM (
    SELECT
        vdp.state,
        vdp.delivery_outcome,
        COUNT(*) AS cnt
    FROM v_delivery_performance vdp
    WHERE vdp.delivery_outcome IN ('on_time', 'late')
      AND (%(start_date)s IS NULL OR vdp.order_purchase_timestamp >= %(start_date)s)
      AND (%(end_date)s   IS NULL OR vdp.order_purchase_timestamp <  %(end_date)s)
    GROUP BY vdp.state, vdp.delivery_outcome
) sub
INNER JOIN (
    -- Only states with total deliveries >= 500
    SELECT
        vdp2.state
    FROM v_delivery_performance vdp2
    WHERE vdp2.delivery_outcome IN ('on_time', 'late')
      AND (%(start_date)s IS NULL OR vdp2.order_purchase_timestamp >= %(start_date)s)
      AND (%(end_date)s   IS NULL OR vdp2.order_purchase_timestamp <  %(end_date)s)
    GROUP BY vdp2.state
    HAVING COUNT(*) >= 500
) qualified ON qualified.state = sub.state
ORDER BY sub.state, sub.delivery_outcome;


-- ────────────────────────────────────────────────────────────────
-- R07  Revenue by Product Category – Top 10  (bar chart)
-- Window function: RANK() OVER to rank categories by revenue.
-- ────────────────────────────────────────────────────────────────
SELECT ranked.category_name_en, ranked.total_revenue, ranked.rnk
FROM (
    SELECT
        COALESCE(pc.category_name_en, pc.category_name, 'unknown') AS category_name_en,
        SUM(oi.price)                                               AS total_revenue,
        RANK() OVER (ORDER BY SUM(oi.price) DESC)                   AS rnk
    FROM order_items oi
    JOIN orders o     ON o.order_id = oi.order_id
    JOIN products p   ON p.product_id = oi.product_id
    JOIN product_categories pc ON pc.category_name = p.category_name
    WHERE (%(start_date)s IS NULL OR o.order_purchase_timestamp >= %(start_date)s)
      AND (%(end_date)s   IS NULL OR o.order_purchase_timestamp <  %(end_date)s)
      AND (%(state)s      IS NULL OR EXISTS (
              SELECT 1 FROM customers c
              JOIN geolocation g ON g.zip_prefix = c.zip_prefix
              WHERE c.customer_id = o.customer_id
                AND g.state = %(state)s
           ))
    GROUP BY COALESCE(pc.category_name_en, pc.category_name, 'unknown')
) ranked
WHERE ranked.rnk <= 10
ORDER BY ranked.rnk;


-- ────────────────────────────────────────────────────────────────
-- R08  Avg Freight Value by State  (column chart)
-- ────────────────────────────────────────────────────────────────
SELECT
    g.state,
    ROUND(AVG(oi.freight_value), 2)  AS avg_freight
FROM order_items oi
JOIN orders o      ON o.order_id    = oi.order_id
JOIN customers c   ON c.customer_id = o.customer_id
JOIN geolocation g ON g.zip_prefix  = c.zip_prefix
WHERE (%(start_date)s IS NULL OR o.order_purchase_timestamp >= %(start_date)s)
  AND (%(end_date)s   IS NULL OR o.order_purchase_timestamp <  %(end_date)s)
  AND (%(category)s   IS NULL OR EXISTS (
          SELECT 1 FROM products p
          WHERE p.product_id = oi.product_id
            AND p.category_name = %(category)s
       ))
GROUP BY g.state
ORDER BY avg_freight DESC;


-- ────────────────────────────────────────────────────────────────
-- R09  Delivery-Time Distribution  (histogram / bar)
-- Uses view: v_delivery_performance
-- CASE buckets: 0-7, 8-14, 15-21, 22-30, 31-45, 46+
-- ────────────────────────────────────────────────────────────────
SELECT
    CASE
        WHEN vdp.delivery_days BETWEEN  0 AND  7 THEN '0-7 days'
        WHEN vdp.delivery_days BETWEEN  8 AND 14 THEN '8-14 days'
        WHEN vdp.delivery_days BETWEEN 15 AND 21 THEN '15-21 days'
        WHEN vdp.delivery_days BETWEEN 22 AND 30 THEN '22-30 days'
        WHEN vdp.delivery_days BETWEEN 31 AND 45 THEN '31-45 days'
        ELSE '46+ days'
    END AS delivery_bucket,
    COUNT(*) AS order_count
FROM v_delivery_performance vdp
WHERE vdp.delivery_days IS NOT NULL
  AND (%(start_date)s IS NULL OR vdp.order_purchase_timestamp >= %(start_date)s)
  AND (%(end_date)s   IS NULL OR vdp.order_purchase_timestamp <  %(end_date)s)
  AND (%(state)s      IS NULL OR vdp.state = %(state)s)
GROUP BY delivery_bucket
ORDER BY MIN(vdp.delivery_days);


-- ────────────────────────────────────────────────────────────────
-- R10  Avg Review Score by Delivery Outcome  (bar chart)
-- Uses view: v_delivery_performance
-- ────────────────────────────────────────────────────────────────
SELECT
    vdp.delivery_outcome,
    ROUND(AVG(r.review_score), 2) AS avg_review_score,
    COUNT(*)                      AS review_count
FROM order_reviews r
JOIN v_delivery_performance vdp ON vdp.order_id = r.order_id
WHERE vdp.delivery_outcome IN ('on_time', 'late')
  AND (%(start_date)s IS NULL OR vdp.order_purchase_timestamp >= %(start_date)s)
  AND (%(end_date)s   IS NULL OR vdp.order_purchase_timestamp <  %(end_date)s)
  AND (%(state)s      IS NULL OR vdp.state = %(state)s)
GROUP BY vdp.delivery_outcome
ORDER BY avg_review_score DESC;
