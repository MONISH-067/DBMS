"""
Page 5: SQL Query Explorer
Authors: Monish L (1972260035), Prasannakumar S (1924260253),
         S Hari Surendran (1912260615)
"""

import re
import time
from typing import Tuple

import pandas as pd
import streamlit as st

try:
    from app.db import run_query
    from app.exports import to_csv
except ImportError:
    from db import run_query
    from exports import to_csv

EXAMPLE_QUERIES = [
    (
        "Recent Orders Sample",
        "SELECT * FROM orders LIMIT 10;",
    ),
    (
        "Orders Count by Customer State",
        "SELECT g.state, COUNT(*) AS cnt\n"
        "FROM orders o\n"
        "JOIN customers c ON c.customer_id = o.customer_id\n"
        "JOIN geolocation g ON g.zip_prefix = c.zip_prefix\n"
        "GROUP BY g.state\n"
        "ORDER BY cnt DESC;",
    ),
    (
        "Delivery Performance View Sample",
        "SELECT * FROM v_delivery_performance LIMIT 10;",
    ),
    (
        "Order Breakdown by Status",
        "SELECT order_status, COUNT(*)\n"
        "FROM orders\n"
        "GROUP BY order_status;",
    ),
]


def validate_sql(sql: str) -> Tuple[bool, str]:
    """
    Validate that an input SQL query adheres to strict read-only safety rules.

    Rules:
    - Rejects empty queries or whitespace-only input.
    - Permits queries beginning with SELECT, WITH, SHOW, DESCRIBE, DESC, or EXPLAIN.
    - Rejects queries containing destructive DML, DDL, or DCL keywords:
      INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, TRUNCATE, GRANT, REVOKE, EXEC, EXECUTE, CALL.
    - Rejects multi-statement execution (semicolon followed by non-whitespace).

    Returns:
        (True, "") if query is safe and valid.
        (False, error_message) if query fails validation.
    """
    if not sql or not sql.strip():
        return False, "Query cannot be empty. Please enter a valid SQL query."

    # Strip single-line and multi-line SQL comments before inspecting tokens
    cleaned = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    cleaned = re.sub(r"--[^\r\n]*", "", cleaned)
    cleaned = re.sub(r"#[^\r\n]*", "", cleaned).strip()

    if not cleaned:
        return False, "Query cannot be empty. Please enter a valid SQL query."

    # Reject multi-statement queries: semicolon followed by any non-whitespace
    if re.search(r";\s*\S", cleaned):
        return False, "Multiple statements are not permitted. Please execute one query at a time."

    # Ensure query starts with an allowed read-only command keyword
    match_start = re.match(r"^\s*([a-zA-Z]+)", cleaned)
    if not match_start:
        return False, "Invalid SQL syntax: missing command keyword."

    start_token = match_start.group(1).upper()
    allowed_starts = {"SELECT", "WITH", "SHOW", "DESCRIBE", "DESC", "EXPLAIN"}
    if start_token not in allowed_starts:
        return False, (
            f"Permission Denied: Queries must start with SELECT, WITH, SHOW, DESCRIBE, or EXPLAIN. "
            f"Found forbidden command: '{start_token}'."
        )

    # Reject forbidden DML/DDL/DCL keywords with word boundary matching
    forbidden_keywords = [
        "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER",
        "TRUNCATE", "GRANT", "REVOKE", "EXEC", "EXECUTE", "CALL"
    ]
    forbidden_pattern = r"\b(" + "|".join(forbidden_keywords) + r")\b"
    forbidden_match = re.search(forbidden_pattern, cleaned, re.IGNORECASE)
    if forbidden_match:
        matched_kw = forbidden_match.group(1).upper()
        return False, (
            f"Forbidden keyword detected: '{matched_kw}'. "
            f"The SQL Query Explorer operates strictly in read-only mode."
        )

    return True, ""


@st.cache_data(ttl=300)
def _get_available_tables() -> pd.DataFrame:
    """
    Fetch all accessible tables and views from information_schema.
    Returns a cached DataFrame with table names and types.
    """
    try:
        sql = """
        SELECT table_name AS `Table Name`, table_type AS `Type`
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
        ORDER BY table_type, table_name;
        """
        df = run_query(sql)
        if not df.empty:
            return df
    except Exception:
        pass

    # Static fallback metadata if database is temporarily unreachable
    return pd.DataFrame([
        {"Table Name": "customers", "Type": "BASE TABLE"},
        {"Table Name": "geolocation", "Type": "BASE TABLE"},
        {"Table Name": "order_items", "Type": "BASE TABLE"},
        {"Table Name": "order_payments", "Type": "BASE TABLE"},
        {"Table Name": "order_reviews", "Type": "BASE TABLE"},
        {"Table Name": "orders", "Type": "BASE TABLE"},
        {"Table Name": "product_categories", "Type": "BASE TABLE"},
        {"Table Name": "products", "Type": "BASE TABLE"},
        {"Table Name": "sellers", "Type": "BASE TABLE"},
        {"Table Name": "v_delivery_performance", "Type": "VIEW"},
        {"Table Name": "v_order_summary", "Type": "VIEW"},
    ])


def render() -> None:
    """
    Render the interactive SQL Query Explorer page.
    Provides a secure, read-only SQL editor with automatic LIMIT enforcement,
    table inspection, example queries, and CSV data export.
    """
    st.title("SQL Query Explorer")
    st.subheader("Execute SELECT queries against the Olist database (read-only)")

    # ─────────────────────────────────────────────────────────────
    # Reference Expander: Available Tables & Schema Introspection
    # ─────────────────────────────────────────────────────────────
    with st.expander("📋 Available Tables & Views"):
        st.markdown(
            "Below is the list of introspected tables and views currently available in the database:"
        )
        tables_df = _get_available_tables()
        st.dataframe(tables_df, use_container_width=True, hide_index=True)

    # ─────────────────────────────────────────────────────────────
    # Reference Expander: Example Queries
    # ─────────────────────────────────────────────────────────────
    with st.expander("💡 Example Queries (Click 'Load' to copy to editor)"):
        for idx, (title, query_text) in enumerate(EXAMPLE_QUERIES):
            st.markdown(f"**{title}**")
            st.code(query_text, language="sql")
            if st.button(f"Load into Editor", key=f"load_query_{idx}"):
                st.session_state["sql_query_text"] = query_text
                st.rerun()

    # ─────────────────────────────────────────────────────────────
    # SQL Editor Input Area
    # ─────────────────────────────────────────────────────────────
    default_sql = st.session_state.get(
        "sql_query_text",
        "SELECT * FROM orders LIMIT 10;"
    )

    query_input = st.text_area(
        label="SQL Statement",
        value=default_sql,
        height=200,
        placeholder="SELECT * FROM orders LIMIT 10;",
        help="Enter a SELECT, WITH, SHOW, or DESCRIBE query. Automatically capped at 1,000 rows if LIMIT is omitted.",
        key="sql_editor_area",
    )

    run_col, clear_col = st.columns([1, 5])
    with run_col:
        run_clicked = st.button("Run Query", type="primary", use_container_width=True)

    # ─────────────────────────────────────────────────────────────
    # Query Validation and Execution
    # ─────────────────────────────────────────────────────────────
    if run_clicked:
        is_valid, error_msg = validate_sql(query_input)

        if not is_valid:
            st.error(f"⚠️ Validation Error: {error_msg}")
            return

        # Prepare query with automatic LIMIT 1000 safety cap
        clean_sql = query_input.strip().rstrip(";").strip()
        first_token = clean_sql.split()[0].upper() if clean_sql.split() else ""

        # Only append LIMIT if query doesn't already contain LIMIT
        if not re.search(r"\bLIMIT\b", clean_sql, re.IGNORECASE):
            if first_token in ("SELECT", "WITH"):
                exec_sql = f"{clean_sql}\nLIMIT 1000"
            elif first_token in ("DESCRIBE", "DESC", "EXPLAIN"):
                exec_sql = clean_sql
            else:
                exec_sql = f"{clean_sql}\nLIMIT 1000"
        else:
            exec_sql = clean_sql

        try:
            start_time = time.perf_counter()
            result_df = run_query(exec_sql)
            elapsed_sec = time.perf_counter() - start_time

            st.success(f"Returned {len(result_df)} rows in {elapsed_sec:.3f} seconds.")

            if not result_df.empty:
                st.dataframe(result_df, use_container_width=True)

                csv_bytes = to_csv(result_df)
                st.download_button(
                    label="📥 Export as CSV",
                    data=csv_bytes,
                    file_name="query_results.csv",
                    mime="text/csv",
                )
            else:
                st.info("Query executed successfully, but returned 0 rows.")

        except Exception as exc:
            # Display only the MySQL error message without full Python traceback
            st.error(f"MySQL Error: {exc}")
