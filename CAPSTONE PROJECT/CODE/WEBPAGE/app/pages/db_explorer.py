"""
Page 2: Database Explorer
Authors: Monish L (1972260035), Prasannakumar S (1924260253),
         S Hari Surendran (1912260615)
"""

import math
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
import streamlit as st

# Ensure project root is available in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db import run_query, run_query_raw


def format_bytes(size_bytes: Optional[int]) -> str:
    """Format bytes into readable string."""
    if size_bytes is None:
        return "0 B"
    val = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if val < 1024.0:
            return f"{val:.2f} {unit}"
        val /= 1024.0
    return f"{val:.2f} TB"


def render() -> None:
    """Render Page 2: Database Explorer."""
    st.header("🗄️ Database Explorer")
    st.markdown("Inspect MySQL catalog metadata, schemas, column structures, constraints, and live records.")

    db_name = os.getenv("MYSQL_DATABASE", "olist")

    # ── Database Connectivity Check & Section 1: Database Info ───────────────
    try:
        version_df = run_query("SELECT VERSION() AS mysql_version")
        mysql_version = (
            str(version_df.iloc[0]["mysql_version"]) if not version_df.empty else "Unknown"
        )
    except Exception as exc:
        st.error(f"❌ Failed to connect to MySQL database `{db_name}`.")
        st.warning(
            f"**Error Details:** `{exc}`\n\n"
            "Please verify that the MySQL service is running and that connection credentials "
            "in your `.env` file (e.g., `MYSQL_RO_USER`, `MYSQL_RO_PASS`) are configured properly."
        )
        return

    # ── Section 2: Table List with Row Counts ─────────────────────────────────
    tables_sql = """
        SELECT TABLE_NAME,
               TABLE_ROWS,
               DATA_LENGTH,
               CREATE_TIME
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = %(schema)s
        ORDER BY TABLE_NAME
    """
    try:
        tables_df = run_query(tables_sql, {"schema": db_name})
    except Exception as exc:
        st.error(f"Error querying information_schema.TABLES: {exc}")
        return

    total_table_count = len(tables_df)

    # Section 1 Header & Metrics
    st.subheader("1. Database Info")
    col1, col2, col3 = st.columns(3)
    col1.metric("Database Name", db_name)
    col2.metric("MySQL Version", mysql_version)
    col3.metric("Total Tables", total_table_count)

    if total_table_count == 0:
        st.warning(
            f"⚠️ No tables found in schema `{db_name}`.\n\n"
            "Please run the ETL migration script (`python etl/import_olist.py --reset`) to initialize and populate the database."
        )
        return

    # Build whitelisted table name list directly from information_schema
    valid_tables: List[str] = tables_df["TABLE_NAME"].tolist()

    # Section 2 Display
    st.subheader("2. Table List with Row Counts")
    display_tables_df = tables_df.copy()
    display_tables_df["Formatted Size"] = display_tables_df["DATA_LENGTH"].apply(format_bytes)
    display_tables_df["Estimated Rows"] = display_tables_df["TABLE_ROWS"].apply(
        lambda x: f"{int(x):,}" if pd.notna(x) else "0"
    )

    st.dataframe(
        display_tables_df[["TABLE_NAME", "Estimated Rows", "Formatted Size", "CREATE_TIME"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "TABLE_NAME": st.column_config.TextColumn("Table Name", help="Name of table in schema"),
            "Estimated Rows": st.column_config.TextColumn("Row Count (Est.)", help="TABLE_ROWS from MySQL statistics"),
            "Formatted Size": st.column_config.TextColumn("Data Length", help="Data storage consumed"),
            "CREATE_TIME": st.column_config.DatetimeColumn("Created Time", format="YYYY-MM-DD HH:mm:ss"),
        },
    )

    # ── Section 3: Column Details ─────────────────────────────────────────────
    st.subheader("3. Column Details")
    selected_table = st.selectbox(
        "Select Table to Inspect Columns & Constraints",
        options=valid_tables,
        index=0,
        key="db_selected_table",
    )

    # Security check: verify selected table is whitelisted
    if selected_table not in valid_tables:
        st.error("Access denied: Invalid table selection.")
        return

    columns_sql = """
        SELECT COLUMN_NAME,
               COLUMN_TYPE,
               IS_NULLABLE,
               COLUMN_KEY,
               COLUMN_DEFAULT,
               EXTRA
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %(schema)s
          AND TABLE_NAME = %(table)s
        ORDER BY ORDINAL_POSITION
    """
    try:
        columns_df = run_query(columns_sql, {"schema": db_name, "table": selected_table})
    except Exception as exc:
        st.error(f"Error querying information_schema.COLUMNS: {exc}")
        columns_df = pd.DataFrame()

    st.dataframe(
        columns_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "COLUMN_NAME": st.column_config.TextColumn("Column Name"),
            "COLUMN_TYPE": st.column_config.TextColumn("Column Type"),
            "IS_NULLABLE": st.column_config.TextColumn("Nullable?"),
            "COLUMN_KEY": st.column_config.TextColumn("Key"),
            "COLUMN_DEFAULT": st.column_config.TextColumn("Default Value"),
            "EXTRA": st.column_config.TextColumn("Extra Attributes"),
        },
    )

    # ── Section 4: Constraints ────────────────────────────────────────────────
    st.subheader(f"4. Constraints for Table `{selected_table}`")
    constraints_sql = """
        SELECT tc.CONSTRAINT_TYPE,
               tc.CONSTRAINT_NAME,
               kcu.COLUMN_NAME,
               kcu.REFERENCED_TABLE_NAME,
               kcu.REFERENCED_COLUMN_NAME
        FROM information_schema.TABLE_CONSTRAINTS tc
        JOIN information_schema.KEY_COLUMN_USAGE kcu
          ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
         AND tc.TABLE_SCHEMA = kcu.TABLE_SCHEMA
         AND tc.TABLE_NAME = kcu.TABLE_NAME
        WHERE tc.TABLE_SCHEMA = %(schema)s
          AND tc.TABLE_NAME = %(table)s
        ORDER BY tc.CONSTRAINT_TYPE, tc.CONSTRAINT_NAME, kcu.ORDINAL_POSITION
    """
    try:
        constraints_df = run_query(constraints_sql, {"schema": db_name, "table": selected_table})
    except Exception as exc:
        st.error(f"Error querying table constraints: {exc}")
        constraints_df = pd.DataFrame()

    if constraints_df.empty:
        st.info(f"No explicit constraints defined for table `{selected_table}`.")
    else:
        # Categorized views of constraints
        pk_rows = constraints_df[constraints_df["CONSTRAINT_TYPE"] == "PRIMARY KEY"]
        fk_rows = constraints_df[constraints_df["CONSTRAINT_TYPE"] == "FOREIGN KEY"]
        uniq_rows = constraints_df[constraints_df["CONSTRAINT_TYPE"] == "UNIQUE"]

        tab_all, tab_pk, tab_fk, tab_uniq = st.tabs(
            [
                f"All Constraints ({len(constraints_df)})",
                f"Primary Key ({len(pk_rows)})",
                f"Foreign Keys ({len(fk_rows)})",
                f"Unique Constraints ({len(uniq_rows)})",
            ]
        )

        with tab_all:
            st.dataframe(constraints_df, use_container_width=True, hide_index=True)

        with tab_pk:
            if not pk_rows.empty:
                st.dataframe(
                    pk_rows[["CONSTRAINT_NAME", "COLUMN_NAME"]],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No Primary Key constraint defined.")

        with tab_fk:
            if not fk_rows.empty:
                st.dataframe(
                    fk_rows[["CONSTRAINT_NAME", "COLUMN_NAME", "REFERENCED_TABLE_NAME", "REFERENCED_COLUMN_NAME"]],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No Foreign Key constraints defined.")

        with tab_uniq:
            if not uniq_rows.empty:
                st.dataframe(
                    uniq_rows[["CONSTRAINT_NAME", "COLUMN_NAME"]],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No Unique constraints defined.")

    # ── Section 5: Relationships ──────────────────────────────────────────────
    st.subheader("5. Database Foreign Key Relationships")
    relationships_sql = """
        SELECT TABLE_NAME AS source_table,
               COLUMN_NAME AS source_column,
               REFERENCED_TABLE_NAME AS referenced_table,
               REFERENCED_COLUMN_NAME AS referenced_column,
               CONSTRAINT_NAME AS constraint_name
        FROM information_schema.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = %(schema)s
          AND REFERENCED_TABLE_NAME IS NOT NULL
        ORDER BY TABLE_NAME, CONSTRAINT_NAME, ORDINAL_POSITION
    """
    try:
        relationships_df = run_query(relationships_sql, {"schema": db_name})
    except Exception as exc:
        st.error(f"Error querying relationships: {exc}")
        relationships_df = pd.DataFrame()

    if relationships_df.empty:
        st.info("No Foreign Key relationships found in information_schema.")
    else:
        rel_display = relationships_df.copy()
        rel_display["Relationship"] = (
            rel_display["source_table"]
            + "."
            + rel_display["source_column"]
            + " -> "
            + rel_display["referenced_table"]
            + "."
            + rel_display["referenced_column"]
        )

        st.dataframe(
            rel_display[
                [
                    "Relationship",
                    "source_table",
                    "source_column",
                    "referenced_table",
                    "referenced_column",
                    "constraint_name",
                ]
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Relationship": st.column_config.TextColumn("Relationship Mapping", width="large"),
                "source_table": st.column_config.TextColumn("Source Table"),
                "source_column": st.column_config.TextColumn("Source Column"),
                "referenced_table": st.column_config.TextColumn("Referenced Table"),
                "referenced_column": st.column_config.TextColumn("Referenced Column"),
                "constraint_name": st.column_config.TextColumn("FK Constraint Name"),
            },
        )

    # ── Section 6: Record Viewer ──────────────────────────────────────────────
    st.subheader("6. Live Record Viewer")
    st.markdown(
        "Browse table rows with whitelisted column filtering, keyword searching, and sorting. "
        "*(Queries strictly parameterized with a safety limit of 1,000 records)*"
    )

    # Selected table from whitelisted dropdown (same options as Section 3)
    viewer_table = selected_table

    # Fetch columns strictly from information_schema to whitelist column identifiers
    viewer_cols_sql = """
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %(schema)s
          AND TABLE_NAME = %(table)s
        ORDER BY ORDINAL_POSITION
    """
    try:
        cols_res = run_query(viewer_cols_sql, {"schema": db_name, "table": viewer_table})
        whitelisted_cols = cols_res["COLUMN_NAME"].tolist() if not cols_res.empty else []
    except Exception as exc:
        st.error(f"Error loading table columns: {exc}")
        whitelisted_cols = []

    if not whitelisted_cols:
        st.warning(f"No columns accessible for table `{viewer_table}`.")
        return

    # Filter & Sort controls
    c_search_col, c_search_val = st.columns([1, 2])
    with c_search_col:
        search_col = st.selectbox(
            "Filter Column",
            options=whitelisted_cols,
            index=0,
            key=f"rec_search_col_{viewer_table}",
        )
    with c_search_val:
        search_val = st.text_input(
            "Filter Value (LIKE %keyword%)",
            value="",
            placeholder=f"Filter {search_col}...",
            key=f"rec_search_val_{viewer_table}",
        )

    c_sort_col, c_sort_dir = st.columns([2, 1])
    with c_sort_col:
        sort_col = st.selectbox(
            "Sort Column",
            options=whitelisted_cols,
            index=0,
            key=f"rec_sort_col_{viewer_table}",
        )
    with c_sort_dir:
        sort_dir = st.radio(
            "Direction",
            options=["ASC", "DESC"],
            index=0,
            horizontal=True,
            key=f"rec_sort_dir_{viewer_table}",
        )

    # Whitelist validation
    if viewer_table not in valid_tables:
        st.error("Invalid table specified.")
        return
    if search_col not in whitelisted_cols:
        st.error("Invalid search column specified.")
        return
    if sort_col not in whitelisted_cols:
        st.error("Invalid sort column specified.")
        return
    if sort_dir not in ("ASC", "DESC"):
        sort_dir = "ASC"

    # Count matching records (capped at 1,000 for safety)
    has_search = bool(search_val.strip())
    if has_search:
        count_sql = f"SELECT COUNT(*) AS total_count FROM `{viewer_table}` WHERE `{search_col}` LIKE %(search)s"
        count_params = {"search": f"%{search_val.strip()}%"}
    else:
        count_sql = f"SELECT COUNT(*) AS total_count FROM `{viewer_table}`"
        count_params = None

    try:
        count_res = run_query(count_sql, count_params)
        total_matched = int(count_res.iloc[0]["total_count"]) if not count_res.empty else 0
    except Exception as exc:
        st.error(f"Error calculating total row count: {exc}")
        total_matched = 0

    MAX_RECORDS = 1000
    viewable_records = min(total_matched, MAX_RECORDS)
    PAGE_SIZE = 25
    total_pages = max(1, math.ceil(viewable_records / PAGE_SIZE))

    # Manage pagination session state
    page_state_key = f"db_rec_page_{viewer_table}"
    if page_state_key not in st.session_state:
        st.session_state[page_state_key] = 1

    search_signature = f"{search_col}:{search_val.strip()}"
    sig_state_key = f"db_rec_sig_{viewer_table}"
    if st.session_state.get(sig_state_key) != search_signature:
        st.session_state[sig_state_key] = search_signature
        st.session_state[page_state_key] = 1

    current_page = st.session_state.get(page_state_key, 1)
    if current_page > total_pages:
        current_page = total_pages
        st.session_state[page_state_key] = current_page
    if current_page < 1:
        current_page = 1
        st.session_state[page_state_key] = current_page

    offset = (current_page - 1) * PAGE_SIZE
    fetch_limit = min(PAGE_SIZE, viewable_records - offset)
    if fetch_limit <= 0:
        fetch_limit = PAGE_SIZE

    # Parameterized record query
    if has_search:
        records_sql = f"""
            SELECT *
            FROM `{viewer_table}`
            WHERE `{search_col}` LIKE %(search)s
            ORDER BY `{sort_col}` {sort_dir}
            LIMIT %(limit)s OFFSET %(offset)s
        """
        records_params = {
            "search": f"%{search_val.strip()}%",
            "limit": int(fetch_limit),
            "offset": int(offset),
        }
    else:
        records_sql = f"""
            SELECT *
            FROM `{viewer_table}`
            ORDER BY `{sort_col}` {sort_dir}
            LIMIT %(limit)s OFFSET %(offset)s
        """
        records_params = {
            "limit": int(fetch_limit),
            "offset": int(offset),
        }

    try:
        records_df = run_query(records_sql, records_params)
    except Exception as exc:
        st.error(f"Error executing record query: {exc}")
        records_df = pd.DataFrame()

    if records_df.empty:
        if has_search:
            st.info(f"No records found in `{viewer_table}` where `{search_col}` matches '{search_val}'.")
        else:
            st.info(f"Table `{viewer_table}` contains no records.")
    else:
        st.dataframe(records_df, use_container_width=True)

    # Navigation buttons
    c_prev, c_center, c_next = st.columns([1, 3, 1])
    with c_prev:
        if st.button("⬅️ Previous", disabled=(current_page <= 1), key=f"btn_prev_{viewer_table}"):
            st.session_state[page_state_key] = current_page - 1
            st.rerun()

    with c_center:
        capped_msg = " (capped at 1,000 records)" if total_matched > MAX_RECORDS else ""
        st.markdown(
            f"<div style='text-align: center; line-height: 2.2rem; font-size: 0.95rem;'>"
            f"Page <b>{current_page}</b> of <b>{total_pages}</b> &nbsp;|&nbsp; "
            f"Showing {offset + 1 if viewable_records > 0 else 0}–{min(offset + fetch_limit, viewable_records):,} of {viewable_records:,} records{capped_msg}"
            f"</div>",
            unsafe_allow_html=True,
        )

    with c_next:
        if st.button("Next ➡️", disabled=(current_page >= total_pages), key=f"btn_next_{viewer_table}"):
            st.session_state[page_state_key] = current_page + 1
            st.rerun()
