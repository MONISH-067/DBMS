"""Local, read-only Marketplace Operations Dashboard."""
import argparse
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
from pathlib import Path
import re
from urllib.parse import parse_qsl, urlsplit

from marketplace.cache import cached

from app.db import run_query
from app.exports import to_csv, to_pdf, to_xlsx
from app.reports import get_all_reports, get_report, run_report

run_report = cached(run_report)

ROOT = Path(__file__).resolve().parent
PAGE_SIZE = 25
SCOPE = """FROM v_delivery_performance d
WHERE (%(state)s IS NULL OR d.state = %(state)s)
AND (%(start_date)s IS NULL OR d.order_purchase_timestamp >= %(start_date)s)
AND (%(end_date)s IS NULL OR d.order_purchase_timestamp < %(end_date)s)"""


def filters(params):
    state = params.get("state") or None
    if state and not re.fullmatch(r"[A-Z]{2}", state):
        raise ValueError("Choose a two-letter Brazilian state.")
    start = date.fromisoformat(params["start_date"]) if params.get("start_date") else None
    end = date.fromisoformat(params["end_date"]) if params.get("end_date") else None
    if start and end and start > end:
        raise ValueError("Start date must be on or before end date.")
    if end == date.max:
        raise ValueError("Choose an earlier end date.")
    return dict(state=state, start_date=start.isoformat() if start else None,
                end_date=(end + timedelta(days=1)).isoformat() if end else None)


def order_page(page):
    number = int(page)
    if not 1 <= number <= 10000:
        raise ValueError("Page number is out of range.")
    return (number - 1) * PAGE_SIZE


def records(frame):
    return json.loads(frame.to_json(orient="records", date_format="iso", force_ascii=False))


@cached
def overview(params):
    order_stats = run_query(f"""SELECT COUNT(*) AS orders, AVG(d.delivery_days) AS delivery_days,
       AVG(d.is_on_time) AS on_time {SCOPE}""", params)
    revenue = run_query(f"""SELECT SUM(i.price) AS revenue FROM order_items i
        JOIN (SELECT d.order_id {SCOPE}) scoped ON scoped.order_id = i.order_id""", params)
    review = run_query(f"""SELECT AVG(r.review_score) AS review FROM order_reviews r
        JOIN (SELECT d.order_id {SCOPE}) scoped ON scoped.order_id = r.order_id""", params)
    outcomes = run_query(f"""SELECT d.delivery_outcome AS outcome, COUNT(*) AS orders
        {SCOPE} GROUP BY d.delivery_outcome""", params)
    return {
        "metrics": records(order_stats)[0] | records(revenue)[0] | records(review)[0],
        "monthly": records(run_query(f"""SELECT DATE_FORMAT(d.order_purchase_timestamp, '%Y-%m') AS order_month,
            COUNT(*) AS order_count {SCOPE} GROUP BY order_month ORDER BY order_month""", params)),
        "outcomes": records(outcomes),
        "states": records(run_query("SELECT DISTINCT state FROM geolocation WHERE state REGEXP '^[A-Z]{2}$' ORDER BY state")),
    }


@cached
def orders(params, query):
    offset = order_page(query.get("page", "1"))
    prefix = query.get("q", "").strip().lower()
    if prefix and not re.fullmatch(r"[0-9a-f]{1,32}", prefix):
        raise ValueError("Enter up to 32 hexadecimal characters from an order ID.")
    outcome = query.get("outcome") or None
    if outcome not in {None, "late", "on_time", "not_delivered"}:
        raise ValueError("Choose a delivery outcome.")
    rows = records(run_query(f"""SELECT d.order_id, d.order_purchase_timestamp AS purchased,
        d.order_status AS status, d.city, d.state, d.delivery_outcome AS outcome
        {SCOPE}
        AND (%(prefix)s IS NULL OR d.order_id LIKE %(prefix)s)
        AND (%(outcome)s IS NULL OR d.delivery_outcome = %(outcome)s)
        ORDER BY d.order_purchase_timestamp DESC, d.order_id DESC
        LIMIT {PAGE_SIZE + 1} OFFSET %(offset)s""",
        params | dict(prefix=prefix + "%" if prefix else None, outcome=outcome, offset=offset)))
    return {"rows": rows[:PAGE_SIZE], "has_more": len(rows) > PAGE_SIZE}


@cached
def detail(order_id):
    if not re.fullmatch(r"[a-f0-9]{32}", order_id):
        raise ValueError("Order ID must contain 32 hexadecimal characters.")
    order = records(run_query("""SELECT d.order_id, d.order_status, d.city, d.state, d.delivery_outcome,
        d.order_purchase_timestamp AS purchased, o.order_approved_at AS approved,
        o.order_delivered_carrier_date AS shipped, d.order_delivered_customer_date AS delivered,
        d.order_estimated_delivery_date AS estimated
        FROM v_delivery_performance d JOIN orders o USING (order_id)
        WHERE d.order_id = %s""", (order_id,)))
    if not order:
        raise KeyError(order_id)
    sections = {
        "items": """SELECT i.order_item_id, i.product_id, i.seller_id,
            COALESCE(pc.category_name_en, p.category_name) AS category, i.price, i.freight_value
            FROM order_items i JOIN products p USING (product_id)
            LEFT JOIN product_categories pc ON pc.category_name = p.category_name
            WHERE i.order_id = %s ORDER BY i.order_item_id""",
        "payments": """SELECT payment_type, installments, payment_value FROM order_payments
            WHERE order_id = %s ORDER BY payment_sequential""",
        "reviews": """SELECT review_score, review_comment_title, review_comment_message
            FROM order_reviews WHERE order_id = %s ORDER BY review_creation_date""",
    }
    return {"order": order[0]} | {key: records(run_query(sql, (order_id,))) for key, sql in sections.items()}


@cached
def schema():
    return {
        "columns": records(run_query("""SELECT TABLE_NAME AS entity, COLUMN_NAME AS field,
            COLUMN_TYPE AS type, COLUMN_KEY AS key_type FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE() ORDER BY TABLE_NAME, ORDINAL_POSITION""")),
        "relationships": records(run_query("""SELECT TABLE_NAME AS entity, COLUMN_NAME AS field,
            REFERENCED_TABLE_NAME AS references_table, REFERENCED_COLUMN_NAME AS references_field
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE() AND REFERENCED_TABLE_NAME IS NOT NULL
            ORDER BY TABLE_NAME, COLUMN_NAME""")),
        "views": records(run_query("""SELECT TABLE_NAME AS name FROM information_schema.VIEWS
            WHERE TABLE_SCHEMA = DATABASE() ORDER BY TABLE_NAME""")),
    }


class Handler(BaseHTTPRequestHandler):
    def send_content(self, body, content_type, status=200, filename=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, value, status=200):
        self.send_content(json.dumps(value, ensure_ascii=False).encode(), "application/json; charset=utf-8", status)

    def do_GET(self):
        request = urlsplit(self.path)
        assets = {"/": ("index.html", "text/html"), "/style.css": ("style.css", "text/css"),
                  "/app.js": ("app.js", "text/javascript"), "/theme.js": ("theme.js", "text/javascript")}
        try:
            if request.path in assets:
                name, mime = assets[request.path]
                self.send_content((ROOT / name).read_bytes(), f"{mime}; charset=utf-8")
                return
            query = dict(parse_qsl(request.query, max_num_fields=12))
            params = filters(query)
            if request.path == "/api/overview":
                result = overview(params)
            elif request.path == "/api/orders":
                result = orders(params, query)
            elif request.path.startswith("/api/orders/"):
                result = detail(request.path.rsplit("/", 1)[-1])
            elif request.path == "/api/schema":
                result = schema()
            elif request.path == "/api/reports":
                result = [{key: report[key] for key in ("id", "title", "description", "filters")}
                          for report in get_all_reports()]
            elif request.path.startswith("/api/reports/"):
                report = get_report(request.path.rsplit("/", 1)[-1])
                supported = {key: params[key] for key in report["filters"] if key in params}
                for key in ("status", "category"):
                    if key in report["filters"] and query.get(key):
                        supported[key] = query[key]
                frame = run_report(report["id"], supported)
                exports = {
                    "csv": ("text/csv", lambda: to_csv(frame)),
                    "xlsx": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", lambda: to_xlsx(frame)),
                    "pdf": ("application/pdf", lambda: to_pdf(frame, report["title"])),
                }
                if query.get("format"):
                    mime, render = exports[query["format"]]
                    self.send_content(render(), mime, filename=f'{report["id"]}.{query["format"]}')
                    return
                result = {"rows": records(frame), "sql": report["sql"]}
            else:
                raise KeyError(request.path)
            self.send_json(result)
        except ValueError as exc:
            self.send_json({"error": str(exc)}, 400)
        except KeyError:
            self.send_json({"error": "This resource could not be found."}, 404)
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception:
            logging.exception("Dashboard request failed")
            self.send_json({"error": "Could not load the data. Check the local MySQL connection and try again."}, 500)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8502)
    args = parser.parse_args()
    with ThreadingHTTPServer(("127.0.0.1", args.port), Handler) as server:
        print(f"Marketplace Operations Dashboard: http://127.0.0.1:{args.port}", flush=True)
        server.serve_forever()

