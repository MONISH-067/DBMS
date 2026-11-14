"""
Olist E-Commerce ETL Importer
Authors: Monish L (1972260035), Prasannakumar S (1924260253),
         S Hari Surendran (1912260615)

Usage:
    python etl/import_olist.py --reset    # Drop, recreate, and import
    python etl/import_olist.py            # Import only (tables must exist)
"""

import argparse
from datetime import datetime
import logging
import os
from pathlib import Path
import sys
import time

from dotenv import load_dotenv
import mysql.connector
import numpy as np
import pandas as pd

# ── Paths Configuration ───────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
SCHEMA_SQL_PATH = PROJECT_ROOT / "SQL" / "schema.sql"
VIEWS_SQL_PATH = PROJECT_ROOT / "SQL" / "views.sql"

# ── Logging Configuration ─────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("import_olist")


# ── Data Cleaning Helpers ─────────────────────────────────────────────────────
def format_zip_prefix(val) -> str | None:
    """Format Brazilian postal code prefix to a 5-digit zero-padded string."""
    if val is None or pd.isna(val):
        return None
    try:
        num = int(float(val))
        return f"{num:05d}"[:5]
    except (ValueError, TypeError):
        s = str(val).strip()
        if not s or s.lower() in ("nan", "null"):
            return None
        return s.zfill(5)[:5]


def clean_str(val, max_length: int | None = None) -> str | None:
    """Clean string value, returning None for empty/null strings."""
    if val is None or pd.isna(val):
        return None
    s = str(val).strip()
    if not s or s.lower() in ("nan", "null"):
        return None
    if max_length is not None:
        return s[:max_length]
    return s


def clean_int(val) -> int | None:
    """Convert value to int or None if invalid/missing."""
    if val is None or pd.isna(val):
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def clean_float(val, decimals: int | None = 2) -> float | None:
    """Convert value to rounded float or None if invalid/missing."""
    if val is None or pd.isna(val):
        return None
    try:
        f = float(val)
        if np.isnan(f) or np.isinf(f):
            return None
        return round(f, decimals) if decimals is not None else f
    except (ValueError, TypeError):
        return None


def clean_datetime(val) -> str | None:
    """Parse datetime and format as standard MySQL DATETIME string or None."""
    if val is None or pd.isna(val):
        return None
    if isinstance(val, (datetime, pd.Timestamp)):
        return val.strftime("%Y-%m-%d %H:%M:%S")
    s = str(val).strip()
    if not s or s.lower() in ("nat", "nan", "null"):
        return None
    try:
        dt = pd.to_datetime(s)
        if pd.isna(dt):
            return None
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


# ── Database Execution Helpers ────────────────────────────────────────────────
def get_db_connection(config: dict, for_reset: bool = False):
    """
    Establish connection to MySQL server.
    Exits with error code 1 if connection fails.
    """
    try:
        conn = mysql.connector.connect(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=config["password"],
            database=None if for_reset else config["database"],
            autocommit=False,
            use_pure=True,
        )
        return conn
    except mysql.connector.Error as err:
        logger.error("Failed to connect to MySQL database at %s:%s: %s", config["host"], config["port"], err)
        sys.exit(1)


def execute_sql_file(cursor, conn, file_path: Path):
    """Execute SQL file by splitting on semicolons and running each statement."""
    if not file_path.is_file():
        logger.error("SQL file not found: %s", file_path)
        sys.exit(1)

    logger.info("Executing SQL script: %s", file_path.name)
    with open(file_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    try:
        # Split on semicolons and execute each non-empty statement
        statements = [s.strip() for s in sql_content.split(";") if s.strip()]
        for stmt in statements:
            try:
                cursor.execute(stmt)
                if cursor.with_rows:
                    cursor.fetchall()
            except mysql.connector.Error as stmt_err:
                # Log but continue (e.g. CREATE USER may fail if not root)
                logger.warning("Statement warning: %s", stmt_err)
        conn.commit()
        logger.info("Successfully executed %s", file_path.name)
    except mysql.connector.Error as err:
        logger.error("Error executing %s: %s", file_path.name, err)
        conn.rollback()
        raise


def batch_insert(
    cursor,
    conn,
    table_name: str,
    insert_sql: str,
    records: list[tuple],
    batch_size: int = 5000,
) -> tuple[int, int, float]:
    """
    Inserts records in batches using cursor.executemany with INSERT IGNORE.
    Wraps the table insert in a transaction and commits after all batches.
    Falls back to row-by-row on batch failure to catch and log per-row errors.
    Returns (inserted_count, skipped_count, elapsed_time).
    """
    total_records = len(records)
    if total_records == 0:
        logger.info("[%s] No records to insert", table_name)
        return 0, 0, 0.0

    start_time = time.time()

    cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
    count_before = cursor.fetchone()[0]

    for i in range(0, total_records, batch_size):
        batch = records[i:i + batch_size]
        try:
            cursor.executemany(insert_sql, batch)
        except mysql.connector.Error as err:
            logger.warning(
                "[%s] Batch insert failed for rows %d-%d: %s. Falling back to row-by-row insert.",
                table_name,
                i + 1,
                min(i + batch_size, total_records),
                err,
            )
            for row in batch:
                try:
                    cursor.execute(insert_sql, row)
                except mysql.connector.Error as row_err:
                    logger.error("[%s] Row insert error: %s | Data: %s", table_name, row_err, row)

    conn.commit()

    cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
    count_after = cursor.fetchone()[0]

    inserted_count = count_after - count_before
    skipped_count = max(0, total_records - inserted_count)
    elapsed_time = time.time() - start_time

    return inserted_count, skipped_count, elapsed_time


# ── Table Importers ───────────────────────────────────────────────────────────
def import_geolocation(cursor, conn, data_dir: Path, batch_size: int) -> dict:
    """Import and deduplicate geolocation dataset, plus insert stub zip prefixes."""
    csv_file = data_dir / "olist_geolocation_dataset.csv"
    if not csv_file.is_file():
        logger.warning("CSV file not found: %s. Skipping table geolocation.", csv_file)
        return {
            "table": "geolocation",
            "rows_read": 0,
            "rows_inserted": 0,
            "rows_skipped": 0,
            "time_s": 0.0,
            "status": "SKIPPED (File not found)",
        }

    logger.info("--- Starting import for table: geolocation ---")
    start_time = time.time()
    logger.info("Reading %s ...", csv_file.name)
    df = pd.read_csv(csv_file, low_memory=False)
    rows_read = len(df)
    logger.info("Read %d rows from %s", rows_read, csv_file.name)

    # Clean zip code prefix
    df["zip_prefix"] = df["geolocation_zip_code_prefix"].apply(format_zip_prefix)
    df = df[df["zip_prefix"].notna()]

    # Group by geolocation_zip_code_prefix: AVG lat/lng, FIRST city/state
    agg_df = df.groupby("zip_prefix", as_index=False).agg({
        "geolocation_city": "first",
        "geolocation_state": "first",
        "geolocation_lat": "mean",
        "geolocation_lng": "mean",
    })
    agg_df.rename(columns={
        "geolocation_city": "city",
        "geolocation_state": "state",
        "geolocation_lat": "avg_lat",
        "geolocation_lng": "avg_lng",
    }, inplace=True)

    records = []
    for row in agg_df.itertuples(index=False):
        z_pref = clean_str(getattr(row, "zip_prefix", None), 5)
        city = clean_str(getattr(row, "city", None), 100) or "UNKNOWN"
        state = clean_str(getattr(row, "state", None), 2) or "XX"
        lat = clean_float(getattr(row, "avg_lat", None), 6) or 0.0
        lng = clean_float(getattr(row, "avg_lng", None), 6) or 0.0
        if z_pref:
            records.append((z_pref, city, state, lat, lng))

    insert_sql = (
        "INSERT IGNORE INTO geolocation (zip_prefix, city, state, avg_lat, avg_lng) "
        "VALUES (%s, %s, %s, %s, %s)"
    )
    inserted, _, _ = batch_insert(cursor, conn, "geolocation", insert_sql, records, batch_size)
    logger.info("[geolocation] Deduplicated to %d unique zip prefixes. Inserted: %d", len(records), inserted)

    # Stub zip prefixes from customers and sellers
    stub_inserted = 0
    try:
        cursor.execute("SELECT zip_prefix FROM geolocation")
        known_zips = {r[0] for r in cursor.fetchall()}

        needed_zips = set()
        cust_csv = data_dir / "olist_customers_dataset.csv"
        if cust_csv.is_file():
            cust_df = pd.read_csv(cust_csv, usecols=["customer_zip_code_prefix"], low_memory=False)
            cust_zips = set(cust_df["customer_zip_code_prefix"].apply(format_zip_prefix).dropna().unique())
            needed_zips.update(cust_zips)

        sellers_csv = data_dir / "olist_sellers_dataset.csv"
        if sellers_csv.is_file():
            sell_df = pd.read_csv(sellers_csv, usecols=["seller_zip_code_prefix"], low_memory=False)
            sell_zips = set(sell_df["seller_zip_code_prefix"].apply(format_zip_prefix).dropna().unique())
            needed_zips.update(sell_zips)

        missing_zips = sorted(needed_zips - known_zips)
        if missing_zips:
            logger.info("Found %d zip prefixes in customers/sellers missing from geolocation. Inserting stub rows...", len(missing_zips))
            stub_records = [(z, "UNKNOWN", "XX", 0.0, 0.0) for z in missing_zips]
            s_ins, _, _ = batch_insert(cursor, conn, "geolocation", insert_sql, stub_records, batch_size)
            stub_inserted = s_ins
            logger.info("Inserted %d stub zip prefix rows into geolocation", stub_inserted)
    except Exception as stub_err:
        logger.error("Error checking or inserting stub zip prefixes: %s", stub_err)

    total_inserted = inserted + stub_inserted
    total_skipped = max(0, rows_read - inserted)
    elapsed = time.time() - start_time

    return {
        "table": "geolocation",
        "rows_read": rows_read,
        "rows_inserted": total_inserted,
        "rows_skipped": total_skipped,
        "time_s": elapsed,
        "status": "SUCCESS",
    }


def import_customers(cursor, conn, data_dir: Path, batch_size: int) -> dict:
    """Import customers dataset."""
    csv_file = data_dir / "olist_customers_dataset.csv"
    if not csv_file.is_file():
        logger.warning("CSV file not found: %s. Skipping table customers.", csv_file)
        return {
            "table": "customers",
            "rows_read": 0,
            "rows_inserted": 0,
            "rows_skipped": 0,
            "time_s": 0.0,
            "status": "SKIPPED (File not found)",
        }

    logger.info("--- Starting import for table: customers ---")
    start_time = time.time()
    logger.info("Reading %s ...", csv_file.name)
    df = pd.read_csv(csv_file, low_memory=False)
    rows_read = len(df)
    logger.info("Read %d rows from %s", rows_read, csv_file.name)

    records = []
    for row in df.itertuples(index=False):
        cust_id = clean_str(getattr(row, "customer_id", None), 32)
        unique_id = clean_str(getattr(row, "customer_unique_id", None), 32)
        zip_prefix = format_zip_prefix(getattr(row, "customer_zip_code_prefix", None))
        if cust_id and unique_id and zip_prefix:
            records.append((cust_id, unique_id, zip_prefix))

    insert_sql = (
        "INSERT IGNORE INTO customers (customer_id, customer_unique_id, zip_prefix) "
        "VALUES (%s, %s, %s)"
    )
    inserted, _, elapsed = batch_insert(cursor, conn, "customers", insert_sql, records, batch_size)
    total_skipped = max(0, rows_read - inserted)

    return {
        "table": "customers",
        "rows_read": rows_read,
        "rows_inserted": inserted,
        "rows_skipped": total_skipped,
        "time_s": elapsed,
        "status": "SUCCESS",
    }


def import_sellers(cursor, conn, data_dir: Path, batch_size: int) -> dict:
    """Import sellers dataset."""
    csv_file = data_dir / "olist_sellers_dataset.csv"
    if not csv_file.is_file():
        logger.warning("CSV file not found: %s. Skipping table sellers.", csv_file)
        return {
            "table": "sellers",
            "rows_read": 0,
            "rows_inserted": 0,
            "rows_skipped": 0,
            "time_s": 0.0,
            "status": "SKIPPED (File not found)",
        }

    logger.info("--- Starting import for table: sellers ---")
    start_time = time.time()
    logger.info("Reading %s ...", csv_file.name)
    df = pd.read_csv(csv_file, low_memory=False)
    rows_read = len(df)
    logger.info("Read %d rows from %s", rows_read, csv_file.name)

    records = []
    for row in df.itertuples(index=False):
        seller_id = clean_str(getattr(row, "seller_id", None), 32)
        zip_prefix = format_zip_prefix(getattr(row, "seller_zip_code_prefix", None))
        if seller_id and zip_prefix:
            records.append((seller_id, zip_prefix))

    insert_sql = "INSERT IGNORE INTO sellers (seller_id, zip_prefix) VALUES (%s, %s)"
    inserted, _, elapsed = batch_insert(cursor, conn, "sellers", insert_sql, records, batch_size)
    total_skipped = max(0, rows_read - inserted)

    return {
        "table": "sellers",
        "rows_read": rows_read,
        "rows_inserted": inserted,
        "rows_skipped": total_skipped,
        "time_s": elapsed,
        "status": "SUCCESS",
    }


def import_product_categories(cursor, conn, data_dir: Path, batch_size: int) -> dict:
    """Import product categories from translation file and scan products CSV for untranslated names."""
    trans_file = data_dir / "product_category_name_translation.csv"
    prod_file = data_dir / "olist_products_dataset.csv"

    if not trans_file.is_file() and not prod_file.is_file():
        logger.warning("Neither translation nor products CSV found. Skipping product_categories.")
        return {
            "table": "product_categories",
            "rows_read": 0,
            "rows_inserted": 0,
            "rows_skipped": 0,
            "time_s": 0.0,
            "status": "SKIPPED (Files not found)",
        }

    logger.info("--- Starting import for table: product_categories ---")
    start_time = time.time()
    categories: dict[str, str | None] = {}
    rows_read = 0

    if trans_file.is_file():
        logger.info("Reading %s ...", trans_file.name)
        trans_df = pd.read_csv(trans_file, low_memory=False)
        rows_read += len(trans_df)
        for row in trans_df.itertuples(index=False):
            cat_name = clean_str(getattr(row, "product_category_name", None), 100)
            cat_en = clean_str(getattr(row, "product_category_name_english", None), 100)
            if cat_name:
                categories[cat_name] = cat_en

    if prod_file.is_file():
        logger.info("Scanning %s for untranslated product categories ...", prod_file.name)
        prod_df = pd.read_csv(prod_file, usecols=["product_category_name"], low_memory=False)
        for cat_val in prod_df["product_category_name"].dropna().unique():
            c_name = clean_str(cat_val, 100)
            if c_name and c_name not in categories:
                categories[c_name] = None
                rows_read += 1

    records = [(cat_name, cat_en) for cat_name, cat_en in categories.items()]
    insert_sql = (
        "INSERT IGNORE INTO product_categories (category_name, category_name_en) "
        "VALUES (%s, %s)"
    )
    inserted, _, elapsed = batch_insert(cursor, conn, "product_categories", insert_sql, records, batch_size)
    total_skipped = max(0, len(records) - inserted)

    return {
        "table": "product_categories",
        "rows_read": rows_read,
        "rows_inserted": inserted,
        "rows_skipped": total_skipped,
        "time_s": elapsed,
        "status": "SUCCESS",
    }


def import_products(cursor, conn, data_dir: Path, batch_size: int) -> dict:
    """Import products dataset."""
    csv_file = data_dir / "olist_products_dataset.csv"
    if not csv_file.is_file():
        logger.warning("CSV file not found: %s. Skipping table products.", csv_file)
        return {
            "table": "products",
            "rows_read": 0,
            "rows_inserted": 0,
            "rows_skipped": 0,
            "time_s": 0.0,
            "status": "SKIPPED (File not found)",
        }

    logger.info("--- Starting import for table: products ---")
    start_time = time.time()
    logger.info("Reading %s ...", csv_file.name)
    df = pd.read_csv(csv_file, low_memory=False)
    rows_read = len(df)
    logger.info("Read %d rows from %s", rows_read, csv_file.name)

    # Numeric columns to Int64 first per requirement 10
    int_cols = [
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
        "product_photos_qty",
    ]
    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    records = []
    for row in df.itertuples(index=False):
        prod_id = clean_str(getattr(row, "product_id", None), 32)
        if not prod_id:
            continue
        cat_name = clean_str(getattr(row, "product_category_name", None), 100)
        wt = clean_int(getattr(row, "product_weight_g", None))
        length = clean_int(getattr(row, "product_length_cm", None))
        ht = clean_int(getattr(row, "product_height_cm", None))
        wd = clean_int(getattr(row, "product_width_cm", None))
        photos = clean_int(getattr(row, "product_photos_qty", None))
        records.append((prod_id, cat_name, wt, length, ht, wd, photos))

    insert_sql = (
        "INSERT IGNORE INTO products ("
        "  product_id, category_name, weight_g, length_cm, height_cm, width_cm, photos_qty"
        ") VALUES (%s, %s, %s, %s, %s, %s, %s)"
    )
    inserted, _, elapsed = batch_insert(cursor, conn, "products", insert_sql, records, batch_size)
    total_skipped = max(0, rows_read - inserted)

    return {
        "table": "products",
        "rows_read": rows_read,
        "rows_inserted": inserted,
        "rows_skipped": total_skipped,
        "time_s": elapsed,
        "status": "SUCCESS",
    }


def import_orders(cursor, conn, data_dir: Path, batch_size: int) -> dict:
    """Import orders dataset."""
    csv_file = data_dir / "olist_orders_dataset.csv"
    if not csv_file.is_file():
        logger.warning("CSV file not found: %s. Skipping table orders.", csv_file)
        return {
            "table": "orders",
            "rows_read": 0,
            "rows_inserted": 0,
            "rows_skipped": 0,
            "time_s": 0.0,
            "status": "SKIPPED (File not found)",
        }

    logger.info("--- Starting import for table: orders ---")
    start_time = time.time()
    logger.info("Reading %s ...", csv_file.name)
    df = pd.read_csv(csv_file, low_memory=False)
    rows_read = len(df)
    logger.info("Read %d rows from %s", rows_read, csv_file.name)

    records = []
    for row in df.itertuples(index=False):
        order_id = clean_str(getattr(row, "order_id", None), 32)
        cust_id = clean_str(getattr(row, "customer_id", None), 32)
        status = clean_str(getattr(row, "order_status", None), 20) or "unknown"
        purchase_ts = clean_datetime(getattr(row, "order_purchase_timestamp", None))
        if not order_id or not cust_id or not purchase_ts:
            continue
        approved_at = clean_datetime(getattr(row, "order_approved_at", None))
        carrier_date = clean_datetime(getattr(row, "order_delivered_carrier_date", None))
        customer_date = clean_datetime(getattr(row, "order_delivered_customer_date", None))
        est_date = clean_datetime(getattr(row, "order_estimated_delivery_date", None))

        records.append((
            order_id,
            cust_id,
            status,
            purchase_ts,
            approved_at,
            carrier_date,
            customer_date,
            est_date,
        ))

    insert_sql = (
        "INSERT IGNORE INTO orders ("
        "  order_id, customer_id, order_status, order_purchase_timestamp, "
        "  order_approved_at, order_delivered_carrier_date, "
        "  order_delivered_customer_date, order_estimated_delivery_date"
        ") VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    )
    inserted, _, elapsed = batch_insert(cursor, conn, "orders", insert_sql, records, batch_size)
    total_skipped = max(0, rows_read - inserted)

    return {
        "table": "orders",
        "rows_read": rows_read,
        "rows_inserted": inserted,
        "rows_skipped": total_skipped,
        "time_s": elapsed,
        "status": "SUCCESS",
    }


def import_order_items(cursor, conn, data_dir: Path, batch_size: int) -> dict:
    """Import order items dataset."""
    csv_file = data_dir / "olist_order_items_dataset.csv"
    if not csv_file.is_file():
        logger.warning("CSV file not found: %s. Skipping table order_items.", csv_file)
        return {
            "table": "order_items",
            "rows_read": 0,
            "rows_inserted": 0,
            "rows_skipped": 0,
            "time_s": 0.0,
            "status": "SKIPPED (File not found)",
        }

    logger.info("--- Starting import for table: order_items ---")
    start_time = time.time()
    logger.info("Reading %s ...", csv_file.name)
    df = pd.read_csv(csv_file, low_memory=False)
    rows_read = len(df)
    logger.info("Read %d rows from %s", rows_read, csv_file.name)

    if "order_item_id" in df.columns:
        df["order_item_id"] = pd.to_numeric(df["order_item_id"], errors="coerce").astype("Int64")

    records = []
    for row in df.itertuples(index=False):
        order_id = clean_str(getattr(row, "order_id", None), 32)
        item_id = clean_int(getattr(row, "order_item_id", None))
        prod_id = clean_str(getattr(row, "product_id", None), 32)
        seller_id = clean_str(getattr(row, "seller_id", None), 32)
        shipping_date = clean_datetime(getattr(row, "shipping_limit_date", None))
        price = clean_float(getattr(row, "price", None), 2)
        freight = clean_float(getattr(row, "freight_value", None), 2)

        if not order_id or item_id is None or not prod_id or not seller_id or not shipping_date or price is None or freight is None:
            continue

        records.append((order_id, item_id, prod_id, seller_id, shipping_date, price, freight))

    insert_sql = (
        "INSERT IGNORE INTO order_items ("
        "  order_id, order_item_id, product_id, seller_id, shipping_limit_date, price, freight_value"
        ") VALUES (%s, %s, %s, %s, %s, %s, %s)"
    )
    inserted, _, elapsed = batch_insert(cursor, conn, "order_items", insert_sql, records, batch_size)
    total_skipped = max(0, rows_read - inserted)

    return {
        "table": "order_items",
        "rows_read": rows_read,
        "rows_inserted": inserted,
        "rows_skipped": total_skipped,
        "time_s": elapsed,
        "status": "SUCCESS",
    }


def import_order_payments(cursor, conn, data_dir: Path, batch_size: int) -> dict:
    """Import order payments dataset."""
    csv_file = data_dir / "olist_order_payments_dataset.csv"
    if not csv_file.is_file():
        logger.warning("CSV file not found: %s. Skipping table order_payments.", csv_file)
        return {
            "table": "order_payments",
            "rows_read": 0,
            "rows_inserted": 0,
            "rows_skipped": 0,
            "time_s": 0.0,
            "status": "SKIPPED (File not found)",
        }

    logger.info("--- Starting import for table: order_payments ---")
    start_time = time.time()
    logger.info("Reading %s ...", csv_file.name)
    df = pd.read_csv(csv_file, low_memory=False)
    rows_read = len(df)
    logger.info("Read %d rows from %s", rows_read, csv_file.name)

    for col in ["payment_sequential", "payment_installments"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    records = []
    for row in df.itertuples(index=False):
        order_id = clean_str(getattr(row, "order_id", None), 32)
        seq = clean_int(getattr(row, "payment_sequential", None))
        ptype = clean_str(getattr(row, "payment_type", None), 30) or "not_defined"
        inst = clean_int(getattr(row, "payment_installments", None))
        if inst is None or inst < 1:
            inst = 1
        pval = clean_float(getattr(row, "payment_value", None), 2)

        if not order_id or seq is None or pval is None:
            continue

        records.append((order_id, seq, ptype, inst, pval))

    insert_sql = (
        "INSERT IGNORE INTO order_payments ("
        "  order_id, payment_sequential, payment_type, installments, payment_value"
        ") VALUES (%s, %s, %s, %s, %s)"
    )
    inserted, _, elapsed = batch_insert(cursor, conn, "order_payments", insert_sql, records, batch_size)
    total_skipped = max(0, rows_read - inserted)

    return {
        "table": "order_payments",
        "rows_read": rows_read,
        "rows_inserted": inserted,
        "rows_skipped": total_skipped,
        "time_s": elapsed,
        "status": "SUCCESS",
    }


def import_order_reviews(cursor, conn, data_dir: Path, batch_size: int) -> dict:
    """Import order reviews dataset."""
    csv_file = data_dir / "olist_order_reviews_dataset.csv"
    if not csv_file.is_file():
        logger.warning("CSV file not found: %s. Skipping table order_reviews.", csv_file)
        return {
            "table": "order_reviews",
            "rows_read": 0,
            "rows_inserted": 0,
            "rows_skipped": 0,
            "time_s": 0.0,
            "status": "SKIPPED (File not found)",
        }

    logger.info("--- Starting import for table: order_reviews ---")
    start_time = time.time()
    logger.info("Reading %s ...", csv_file.name)
    df = pd.read_csv(csv_file, low_memory=False)
    rows_read = len(df)
    logger.info("Read %d rows from %s", rows_read, csv_file.name)

    if "review_score" in df.columns:
        df["review_score"] = pd.to_numeric(df["review_score"], errors="coerce").astype("Int64")

    records = []
    for row in df.itertuples(index=False):
        rev_id = clean_str(getattr(row, "review_id", None), 32)
        order_id = clean_str(getattr(row, "order_id", None), 32)
        score = clean_int(getattr(row, "review_score", None))
        if not rev_id or not order_id or score is None:
            continue
        if score < 1 or score > 5:
            continue
        title = clean_str(getattr(row, "review_comment_title", None))
        msg = clean_str(getattr(row, "review_comment_message", None))
        c_date = clean_datetime(getattr(row, "review_creation_date", None))
        a_date = clean_datetime(getattr(row, "review_answer_timestamp", None))

        records.append((rev_id, order_id, score, title, msg, c_date, a_date))

    insert_sql = (
        "INSERT IGNORE INTO order_reviews ("
        "  review_id, order_id, review_score, review_comment_title, "
        "  review_comment_message, review_creation_date, review_answer_timestamp"
        ") VALUES (%s, %s, %s, %s, %s, %s, %s)"
    )
    inserted, _, elapsed = batch_insert(cursor, conn, "order_reviews", insert_sql, records, batch_size)
    total_skipped = max(0, rows_read - inserted)

    return {
        "table": "order_reviews",
        "rows_read": rows_read,
        "rows_inserted": inserted,
        "rows_skipped": total_skipped,
        "time_s": elapsed,
        "status": "SUCCESS",
    }


# ── Summary Output Helper ─────────────────────────────────────────────────────
def print_summary_table(summary_results: list[dict]):
    """Format and display the final summary table of all imported tables."""
    headers = ["Table", "Rows Read", "Rows Inserted", "Rows Skipped", "Time (s)", "Status"]
    col_widths = [20, 12, 14, 14, 10, 24]

    border = "+-" + "-+-".join("-" * w for w in col_widths) + "-+"
    header_row = "| " + " | ".join(f"{h:<{w}}" for h, w in zip(headers, col_widths)) + " |"

    lines = [
        "",
        border,
        header_row,
        border,
    ]

    total_read = 0
    total_inserted = 0
    total_skipped = 0
    total_time = 0.0

    for r in summary_results:
        total_read += r["rows_read"]
        total_inserted += r["rows_inserted"]
        total_skipped += r["rows_skipped"]
        total_time += r["time_s"]

        row_str = (
            f"| {r['table']:<{col_widths[0]}} "
            f"| {r['rows_read']:>{col_widths[1]},} "
            f"| {r['rows_inserted']:>{col_widths[2]},} "
            f"| {r['rows_skipped']:>{col_widths[3]},} "
            f"| {r['time_s']:>{col_widths[4] - 1}.2f}s "
            f"| {r['status']:<{col_widths[5]}} |"
        )
        lines.append(row_str)

    lines.append(border)
    total_row = (
        f"| {'TOTAL':<{col_widths[0]}} "
        f"| {total_read:>{col_widths[1]},} "
        f"| {total_inserted:>{col_widths[2]},} "
        f"| {total_skipped:>{col_widths[3]},} "
        f"| {total_time:>{col_widths[4] - 1}.2f}s "
        f"| {'':<{col_widths[5]}} |"
    )
    lines.append(total_row)
    lines.append(border)

    summary_text = "\n".join(lines)
    logger.info("\n%s", summary_text)


# ── Main Entrypoint ───────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Olist E-Commerce ETL Importer - Loads dataset CSVs into MySQL database."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop and recreate all tables and views from schema.sql and views.sql before importing.",
    )
    parser.add_argument(
        "--data-dir",
        default=None,
        help="Directory containing the CSV datasets (defaults to DATA_DIR env or ./data/).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5000,
        help="Batch size for database inserts (default: 5000).",
    )
    args = parser.parse_args()

    # Load credentials from .env
    dotenv_path = PROJECT_ROOT / ".env"
    if dotenv_path.is_file():
        load_dotenv(dotenv_path=dotenv_path)
    else:
        load_dotenv()

    db_config = {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_ADMIN_USER", "olist_admin"),
        "password": os.getenv("MYSQL_ADMIN_PASS", ""),
        "database": os.getenv("MYSQL_DATABASE", "olist"),
    }

    # Resolve data directory
    if args.data_dir:
        data_dir = Path(args.data_dir).resolve()
    elif os.getenv("DATA_DIR"):
        data_dir = Path(os.getenv("DATA_DIR")).resolve()
    else:
        data_dir = DEFAULT_DATA_DIR.resolve()

    logger.info("Olist ETL Importer initializing...")
    logger.info("Project Root: %s", PROJECT_ROOT)
    logger.info("Data Directory: %s", data_dir)
    logger.info("Target Database: %s@%s:%s/%s", db_config["user"], db_config["host"], db_config["port"], db_config["database"])
    logger.info("Mode: %s", "RESET & IMPORT (--reset)" if args.reset else "INSERT ONLY")

    conn = get_db_connection(db_config, for_reset=args.reset)
    cursor = conn.cursor()

    try:
        # If reset mode requested, execute schema.sql and views.sql
        if args.reset:
            logger.info("Reset requested: sourcing schema.sql and views.sql...")
            execute_sql_file(cursor, conn, SCHEMA_SQL_PATH)
            execute_sql_file(cursor, conn, VIEWS_SQL_PATH)
            # Switch session database to target database
            cursor.execute(f"USE `{db_config['database']}`")
            conn.database = db_config["database"]

        # Import order respecting foreign key constraints:
        # a. geolocation (deduplicated + stubs)
        # b. customers
        # c. sellers
        # d. product_categories
        # e. products
        # f. orders
        # g. order_items
        # h. order_payments
        # i. order_reviews
        summary_results = []
        importers = [
            ("geolocation", import_geolocation),
            ("customers", import_customers),
            ("sellers", import_sellers),
            ("product_categories", import_product_categories),
            ("products", import_products),
            ("orders", import_orders),
            ("order_items", import_order_items),
            ("order_payments", import_order_payments),
            ("order_reviews", import_order_reviews),
        ]

        for tbl_name, importer_func in importers:
            try:
                res = importer_func(cursor, conn, data_dir, args.batch_size)
                summary_results.append(res)
            except Exception as e:
                logger.error("Unexpected error importing %s: %s", tbl_name, e, exc_info=True)
                summary_results.append({
                    "table": tbl_name,
                    "rows_read": 0,
                    "rows_inserted": 0,
                    "rows_skipped": 0,
                    "time_s": 0.0,
                    "status": f"ERROR: {str(e)[:20]}",
                })

        print_summary_table(summary_results)
        logger.info("Olist ETL import process finished.")

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
