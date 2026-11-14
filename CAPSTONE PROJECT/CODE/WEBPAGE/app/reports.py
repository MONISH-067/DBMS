"""
Report Registry & Executor
Authors: Monish L (1972260035), Prasannakumar S (1924260253),
         S Hari Surendran (1912260615)
"""

from typing import Any, Dict, List, Optional
import pandas as pd

try:
    from app import db
except ImportError:
    import db


REPORTS: List[Dict[str, Any]] = [
    {
        "id": "R01",
        "title": "Monthly Orders",
        "description": "Monthly trend of total orders placed across the marketplace",
        "chart_type": "line",
        "sql": """SELECT DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m') AS order_month,
       COUNT(*) AS order_count
FROM orders o
WHERE (%(start_date)s IS NULL OR o.order_purchase_timestamp >= %(start_date)s)
  AND (%(end_date)s IS NULL OR o.order_purchase_timestamp < %(end_date)s)
  AND (%(status)s IS NULL OR o.order_status = %(status)s)
GROUP BY order_month
ORDER BY order_month""",
        "default_params": {"start_date": None, "end_date": None, "status": None},
        "filters": ["start_date", "end_date", "status"],
    },
    {
        "id": "R02",
        "title": "Order Status Share",
        "description": "Distribution of orders across different order statuses",
        "chart_type": "donut",
        "sql": """SELECT o.order_status, COUNT(*) AS order_count
FROM orders o
WHERE (%(start_date)s IS NULL OR o.order_purchase_timestamp >= %(start_date)s)
  AND (%(end_date)s IS NULL OR o.order_purchase_timestamp < %(end_date)s)
GROUP BY o.order_status
ORDER BY order_count DESC""",
        "default_params": {"start_date": None, "end_date": None},
        "filters": ["start_date", "end_date"],
    },
    {
        "id": "R03",
        "title": "Top 10 States by Orders",
        "description": "Top 10 Brazilian states ranked by total order volume",
        "chart_type": "hbar",
        "sql": """SELECT g.state, COUNT(*) AS order_count
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
JOIN geolocation g ON g.zip_prefix = c.zip_prefix
WHERE (%(start_date)s IS NULL OR o.order_purchase_timestamp >= %(start_date)s)
  AND (%(end_date)s IS NULL OR o.order_purchase_timestamp < %(end_date)s)
  AND (%(status)s IS NULL OR o.order_status = %(status)s)
GROUP BY g.state
ORDER BY order_count DESC
LIMIT 10""",
        "default_params": {"start_date": None, "end_date": None, "status": None},
        "filters": ["start_date", "end_date", "status"],
    },
    {
        "id": "R04",
        "title": "Payment Type Share",
        "description": "Breakdown of total transaction value and count by payment method",
        "chart_type": "donut",
        "sql": """SELECT op.payment_type, SUM(op.payment_value) AS total_value,
       COUNT(*) AS payment_count
FROM order_payments op
JOIN orders o ON o.order_id = op.order_id
WHERE (%(start_date)s IS NULL OR o.order_purchase_timestamp >= %(start_date)s)
  AND (%(end_date)s IS NULL OR o.order_purchase_timestamp < %(end_date)s)
GROUP BY op.payment_type
ORDER BY total_value DESC""",
        "default_params": {"start_date": None, "end_date": None},
        "filters": ["start_date", "end_date"],
    },
    {
        "id": "R05",
        "title": "Avg Delivery Days by Month",
        "description": "Average delivery duration in days per order purchase month",
        "chart_type": "line",
        "sql": """SELECT DATE_FORMAT(vdp.order_purchase_timestamp, '%Y-%m') AS order_month,
       ROUND(AVG(vdp.delivery_days), 1) AS avg_delivery_days
FROM v_delivery_performance vdp
WHERE vdp.delivery_days IS NOT NULL
  AND (%(start_date)s IS NULL OR vdp.order_purchase_timestamp >= %(start_date)s)
  AND (%(end_date)s IS NULL OR vdp.order_purchase_timestamp < %(end_date)s)
  AND (%(state)s IS NULL OR vdp.state = %(state)s)
GROUP BY order_month
ORDER BY order_month""",
        "default_params": {"start_date": None, "end_date": None, "state": None},
        "filters": ["start_date", "end_date", "state"],
    },
    {
        "id": "R06",
        "title": "On-Time vs Late Deliveries by State",
        "description": "Delivery timeliness comparison for high-volume states (>= 500 deliveries)",
        "chart_type": "grouped_bar",
        "sql": """SELECT sub.state, sub.delivery_outcome, sub.cnt
FROM (
    SELECT vdp.state, vdp.delivery_outcome, COUNT(*) AS cnt
    FROM v_delivery_performance vdp
    WHERE vdp.delivery_outcome IN ('on_time', 'late')
      AND (%(start_date)s IS NULL OR vdp.order_purchase_timestamp >= %(start_date)s)
      AND (%(end_date)s IS NULL OR vdp.order_purchase_timestamp < %(end_date)s)
    GROUP BY vdp.state, vdp.delivery_outcome
) sub
INNER JOIN (
    SELECT vdp2.state
    FROM v_delivery_performance vdp2
    WHERE vdp2.delivery_outcome IN ('on_time', 'late')
      AND (%(start_date)s IS NULL OR vdp2.order_purchase_timestamp >= %(start_date)s)
      AND (%(end_date)s IS NULL OR vdp2.order_purchase_timestamp < %(end_date)s)
    GROUP BY vdp2.state
    HAVING COUNT(*) >= 500
) qualified ON qualified.state = sub.state
ORDER BY sub.state, sub.delivery_outcome""",
        "default_params": {"start_date": None, "end_date": None},
        "filters": ["start_date", "end_date"],
    },
    {
        "id": "R07",
        "title": "Revenue by Product Category Top 10",
        "description": "Top 10 product categories ranked by total revenue using window function",
        "chart_type": "bar",
        "sql": """SELECT ranked.category_name_en, ranked.total_revenue, ranked.rnk
FROM (
    SELECT COALESCE(pc.category_name_en, pc.category_name, 'unknown') AS category_name_en,
           SUM(oi.price) AS total_revenue,
           RANK() OVER (ORDER BY SUM(oi.price) DESC) AS rnk
    FROM order_items oi
    JOIN orders o ON o.order_id = oi.order_id
    JOIN products p ON p.product_id = oi.product_id
    JOIN product_categories pc ON pc.category_name = p.category_name
    WHERE (%(start_date)s IS NULL OR o.order_purchase_timestamp >= %(start_date)s)
      AND (%(end_date)s IS NULL OR o.order_purchase_timestamp < %(end_date)s)
      AND (%(state)s IS NULL OR EXISTS (
              SELECT 1 FROM customers c
              JOIN geolocation g ON g.zip_prefix = c.zip_prefix
              WHERE c.customer_id = o.customer_id AND g.state = %(state)s
           ))
    GROUP BY COALESCE(pc.category_name_en, pc.category_name, 'unknown')
) ranked
WHERE ranked.rnk <= 10
ORDER BY ranked.rnk""",
        "default_params": {"start_date": None, "end_date": None, "state": None},
        "filters": ["start_date", "end_date", "state"],
    },
    {
        "id": "R08",
        "title": "Avg Freight Value by State",
        "description": "Average freight value per destination state sorted descending",
        "chart_type": "column",
        "sql": """SELECT g.state, ROUND(AVG(oi.freight_value), 2) AS avg_freight
FROM order_items oi
JOIN orders o ON o.order_id = oi.order_id
JOIN customers c ON c.customer_id = o.customer_id
JOIN geolocation g ON g.zip_prefix = c.zip_prefix
WHERE (%(start_date)s IS NULL OR o.order_purchase_timestamp >= %(start_date)s)
  AND (%(end_date)s IS NULL OR o.order_purchase_timestamp < %(end_date)s)
  AND (%(category)s IS NULL OR EXISTS (
          SELECT 1 FROM products p
          WHERE p.product_id = oi.product_id AND p.category_name = %(category)s
       ))
GROUP BY g.state
ORDER BY avg_freight DESC""",
        "default_params": {"start_date": None, "end_date": None, "category": None},
        "filters": ["start_date", "end_date", "category"],
    },
    {
        "id": "R09",
        "title": "Delivery-Time Distribution",
        "description": "Histogram buckets of order delivery duration in days",
        "chart_type": "histogram",
        "sql": """SELECT CASE
        WHEN vdp.delivery_days BETWEEN 0 AND 7 THEN '0-7 days'
        WHEN vdp.delivery_days BETWEEN 8 AND 14 THEN '8-14 days'
        WHEN vdp.delivery_days BETWEEN 15 AND 21 THEN '15-21 days'
        WHEN vdp.delivery_days BETWEEN 22 AND 30 THEN '22-30 days'
        WHEN vdp.delivery_days BETWEEN 31 AND 45 THEN '31-45 days'
        ELSE '46+ days'
       END AS delivery_bucket,
       COUNT(*) AS order_count
FROM v_delivery_performance vdp
WHERE vdp.delivery_days IS NOT NULL
  AND (%(start_date)s IS NULL OR vdp.order_purchase_timestamp >= %(start_date)s)
  AND (%(end_date)s IS NULL OR vdp.order_purchase_timestamp < %(end_date)s)
  AND (%(state)s IS NULL OR vdp.state = %(state)s)
GROUP BY delivery_bucket
ORDER BY MIN(vdp.delivery_days)""",
        "default_params": {"start_date": None, "end_date": None, "state": None},
        "filters": ["start_date", "end_date", "state"],
    },
    {
        "id": "R10",
        "title": "Avg Review Score by Delivery Outcome",
        "description": "Customer review scores for on-time vs late deliveries",
        "chart_type": "bar",
        "sql": """SELECT vdp.delivery_outcome,
       ROUND(AVG(r.review_score), 2) AS avg_review_score,
       COUNT(*) AS review_count
FROM order_reviews r
JOIN v_delivery_performance vdp ON vdp.order_id = r.order_id
WHERE vdp.delivery_outcome IN ('on_time', 'late')
  AND (%(start_date)s IS NULL OR vdp.order_purchase_timestamp >= %(start_date)s)
  AND (%(end_date)s IS NULL OR vdp.order_purchase_timestamp < %(end_date)s)
  AND (%(state)s IS NULL OR vdp.state = %(state)s)
GROUP BY vdp.delivery_outcome
ORDER BY avg_review_score DESC""",
        "default_params": {"start_date": None, "end_date": None, "state": None},
        "filters": ["start_date", "end_date", "state"],
    },
]


def get_report(report_id: str) -> Dict[str, Any]:
    """
    Look up a report definition by ID (case-insensitive, e.g. 'R01').
    Raises KeyError if report_id is not registered.
    """
    normalized_id = report_id.strip().upper()
    for report in REPORTS:
        if report["id"].upper() == normalized_id:
            return report
    raise KeyError(f"Report '{report_id}' not found in registry.")


def get_all_reports() -> List[Dict[str, Any]]:
    """
    Return the full list of all 10 registered report definitions.
    """
    return list(REPORTS)


def run_report(report_id: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    Execute a registered report query with parameter overrides.
    Merges user parameters with default_params (where all filter keys default to None).
    Calls db.run_query(sql, merged_params) and returns the resulting DataFrame.

    Parameters:
        report_id: Identifier of the report (e.g., 'R01').
        params: Optional dictionary of filter overrides (e.g. {'start_date': '2017-01-01'}).
    """
    report = get_report(report_id)
    merged_params = dict(report["default_params"])
    if params:
        merged_params.update(params)
    return db.run_query(report["sql"], merged_params)
