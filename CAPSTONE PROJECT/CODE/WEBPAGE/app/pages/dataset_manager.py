"""
Page 1: Dataset Manager
Authors: Monish L (1972260035), Prasannakumar S (1924260253),
         S Hari Surendran (1912260615)
"""

import math
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
import streamlit as st

try:
    import plotly.express as px
except ImportError:
    px = None

# ── Complete Olist Column Descriptions Dictionary ────────────────────────────
COLUMN_DESCRIPTIONS: Dict[str, str] = {
    # Geolocation
    "geolocation_zip_code_prefix": "First 5 digits of customer/seller zip code",
    "geolocation_lat": "Latitude coordinate",
    "geolocation_lng": "Longitude coordinate",
    "geolocation_city": "City name",
    "geolocation_state": "State abbreviation (2 letters)",
    # Customers
    "customer_id": "Key to the orders dataset. Each order has a unique customer_id",
    "customer_unique_id": "Unique identifier of a customer (may have multiple customer_ids)",
    "customer_zip_code_prefix": "First 5 digits of customer zip code",
    "customer_city": "Customer city name",
    "customer_state": "Customer state abbreviation",
    # Orders
    "order_id": "Unique order identifier",
    "order_status": "Order status (delivered, shipped, canceled, etc.)",
    "order_purchase_timestamp": "Purchase timestamp",
    "order_approved_at": "Payment approval timestamp",
    "order_delivered_carrier_date": "Order posted / handed to carrier timestamp",
    "order_delivered_customer_date": "Actual delivery date to customer",
    "order_estimated_delivery_date": "Estimated delivery date informed to customer at purchase",
    # Order Items
    "order_item_id": "Sequential number identifying items within an order",
    "product_id": "Product unique identifier",
    "seller_id": "Seller unique identifier",
    "shipping_limit_date": "Seller shipping limit date for handing order to carrier",
    "price": "Item price (BRL)",
    "freight_value": "Item freight value (BRL) — if an order has multiple items, freight is split",
    # Payments
    "payment_sequential": "Sequential number for multiple payment methods on one order",
    "payment_type": "Payment method (credit_card, boleto, voucher, debit_card)",
    "payment_installments": "Number of installments chosen by customer",
    "payment_value": "Transaction value (BRL)",
    # Reviews
    "review_id": "Review unique identifier",
    "review_score": "Rating from 1 to 5 given by customer",
    "review_comment_title": "Comment title (in Portuguese)",
    "review_comment_message": "Comment message (in Portuguese)",
    "review_creation_date": "Date the satisfaction survey was sent",
    "review_answer_timestamp": "Date the customer answered the survey",
    # Products
    "product_category_name": "Product category name (in Portuguese)",
    "product_name_lenght": "Number of characters in the product name",
    "product_description_lenght": "Number of characters in the product description",
    "product_photos_qty": "Number of product photos published",
    "product_weight_g": "Product weight in grams",
    "product_length_cm": "Product length in centimeters",
    "product_height_cm": "Product height in centimeters",
    "product_width_cm": "Product width in centimeters",
    # Normalized / alternative spellings
    "product_name_length": "Number of characters in the product name",
    "product_description_length": "Number of characters in the product description",
    # Sellers
    "seller_zip_code_prefix": "First 5 digits of seller zip code",
    "seller_city": "Seller city name",
    "seller_state": "Seller state abbreviation",
    # Category Translation
    "product_category_name_english": "Category name translated to English",
}


def format_file_size(size_bytes: int) -> str:
    """Format byte size into human-readable unit (B, KB, MB, GB)."""
    val = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if val < 1024.0:
            return f"{val:.2f} {unit}"
        val /= 1024.0
    return f"{val:.2f} TB"


@st.cache_data(show_spinner="Scanning dataset files in data/ directory...")
def scan_data_directory(data_dir_str: str) -> List[Dict[str, Any]]:
    """Scan the data directory for CSV files and gather size, row, and column counts."""
    data_dir = Path(data_dir_str)
    if not data_dir.exists():
        return []

    csv_paths = sorted(data_dir.glob("*.csv"))
    file_info_list = []

    for path in csv_paths:
        size_bytes = path.stat().st_size
        size_str = format_file_size(size_bytes)
        try:
            # Quick row count reading single column
            first_col = pd.read_csv(path, usecols=[0], low_memory=False)
            row_count = len(first_col)
            # Column count reading header only
            header_df = pd.read_csv(path, nrows=0)
            col_count = len(header_df.columns)
        except Exception:
            row_count = 0
            col_count = 0

        file_info_list.append(
            {
                "Filename": path.name,
                "File Size": size_str,
                "Size (Bytes)": size_bytes,
                "Row Count": row_count,
                "Column Count": col_count,
                "Path": str(path),
            }
        )

    return file_info_list


@st.cache_data(show_spinner="Loading CSV file into memory...")
def load_csv_dataframe(filepath_str: str) -> pd.DataFrame:
    """Load a CSV file with pandas caching."""
    return pd.read_csv(filepath_str, low_memory=False)


def render() -> None:
    """Render Page 1: Dataset Manager."""
    st.header("📋 Dataset Manager")
    st.markdown("Explore raw CSV files, inspect schema definitions, and validate data quality.")

    # Locate project root and data directory
    project_root = Path(__file__).resolve().parents[3]
    data_dir = project_root / "data"

    # ── Section 1 — Dataset Overview ──────────────────────────────────────────
    st.subheader("1. Dataset Overview")
    st.markdown(
        """
        The **Brazilian E-Commerce Public Dataset by Olist** comprises 100,000 real-world commercial orders 
        placed between 2016 and 2018 across Brazilian marketplaces. It offers a multifaceted view of an enterprise 
        relational database, containing customer identifiers, order lifecycles, item pricing, freight calculations, 
        geographical coordinates, seller metrics, customer reviews, and bilingual product classifications.

        - **Source Platform:** [Kaggle Brazilian E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
        - **Target DBMS:** MySQL 8.x (3NF Normalized Relational Architecture)
        - **Original Files:** 9 core CSV files detailing the Brazilian marketplace ecosystem
        """
    )
    st.info(
        "💡 **Tip:** Place all 9 uncompressed CSV files from Kaggle inside the `data/` folder at "
        f"`{data_dir}` to analyze and import them into MySQL."
    )

    # ── Section 2 — File Information ──────────────────────────────────────────
    st.subheader("2. File Information")
    file_info = scan_data_directory(str(data_dir))

    if not data_dir.exists() or not file_info:
        st.warning(
            f"⚠️ No CSV files found in directory: `{data_dir}`.\n\n"
            "Please ensure the Olist CSV files are placed in the `data/` directory relative to the project root."
        )
        return

    # Create summary DataFrame for display
    summary_df = pd.DataFrame(
        [
            {
                "CSV Filename": item["Filename"],
                "File Size": item["File Size"],
                "Row Count": f"{item['Row Count']:,}",
                "Column Count": item["Column Count"],
            }
            for item in file_info
        ]
    )

    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "CSV Filename": st.column_config.TextColumn("CSV Filename", help="Dataset filename"),
            "File Size": st.column_config.TextColumn("File Size", help="Size on disk"),
            "Row Count": st.column_config.TextColumn("Row Count", help="Total records"),
            "Column Count": st.column_config.NumberColumn("Column Count", help="Number of fields"),
        },
    )

    # ── Section 3 — Data Dictionary ───────────────────────────────────────────
    st.subheader("3. Data Dictionary")
    file_name_map = {item["Filename"]: item["Path"] for item in file_info}
    selected_filename = st.selectbox(
        "Select a CSV File to Inspect",
        options=list(file_name_map.keys()),
        index=0,
        key="dm_file_selector",
    )

    selected_filepath = file_name_map[selected_filename]
    try:
        df = load_csv_dataframe(selected_filepath)
    except Exception as e:
        st.error(f"Failed to read CSV file `{selected_filename}`: {e}")
        return

    total_rows = len(df)
    total_cols = len(df.columns)

    # Build Data Dictionary
    dict_rows = []
    for col in df.columns:
        col_series = df[col]
        missing_count = int(col_series.isna().sum())
        missing_pct = (missing_count / total_rows * 100.0) if total_rows > 0 else 0.0

        # Retrieve first non-null example value
        valid_series = col_series.dropna()
        if not valid_series.empty:
            example_raw = str(valid_series.iloc[0]).strip()
            example_val = (example_raw[:60] + "...") if len(example_raw) > 60 else example_raw
        else:
            example_val = "-"

        # Map description
        description = COLUMN_DESCRIPTIONS.get(col, COLUMN_DESCRIPTIONS.get(col.lower(), "-"))

        dict_rows.append(
            {
                "Column Name": col,
                "Data Type": str(col_series.dtype),
                "Description/Meaning": description,
                "Missing Count": missing_count,
                "Missing %": missing_pct,
                "Example Value": example_val,
            }
        )

    dict_df = pd.DataFrame(dict_rows)

    st.dataframe(
        dict_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Column Name": st.column_config.TextColumn("Column Name", help="Attribute name"),
            "Data Type": st.column_config.TextColumn("Data Type", help="Pandas column type"),
            "Description/Meaning": st.column_config.TextColumn(
                "Description / Meaning", width="large"
            ),
            "Missing Count": st.column_config.NumberColumn("Missing Count", format="%d"),
            "Missing %": st.column_config.NumberColumn("Missing %", format="%.2f%%"),
            "Example Value": st.column_config.TextColumn("Example Value", width="medium"),
        },
    )

    # ── Section 4 — Validation Summary ────────────────────────────────────────
    st.subheader("4. Validation Summary")

    duplicate_rows_count = int(df.duplicated().sum())
    missing_by_col = df.isna().sum()
    cols_with_missing = missing_by_col[missing_by_col > 0]
    high_missing_cols = [
        col for col in df.columns if (missing_by_col[col] / total_rows * 100.0 > 50.0)
    ] if total_rows > 0 else []

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Rows", f"{total_rows:,}")
    m2.metric("Total Columns", f"{total_cols}")
    m3.metric("Duplicate Rows", f"{duplicate_rows_count:,}")
    m4.metric("Columns >50% Missing", f"{len(high_missing_cols)}")

    # Missing values chart
    if not cols_with_missing.empty:
        st.markdown("##### Missing Values Count per Column")
        missing_chart_df = pd.DataFrame(
            {
                "Column Name": cols_with_missing.index,
                "Missing Count": cols_with_missing.values,
                "Missing %": [
                    (cnt / total_rows * 100.0) if total_rows > 0 else 0.0
                    for cnt in cols_with_missing.values
                ],
            }
        ).sort_values(by="Missing Count", ascending=False)

        if px is not None:
            fig = px.bar(
                missing_chart_df,
                x="Column Name",
                y="Missing Count",
                hover_data=["Missing %"],
                text="Missing Count",
                color="Missing Count",
                color_continuous_scale="Reds",
                title=f"Missing Value Counts in {selected_filename}",
            )
            fig.update_layout(xaxis_tickangle=-45, showlegend=False, margin=dict(t=40, b=80))
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(missing_chart_df.set_index("Column Name")["Missing Count"])
    else:
        st.success("✅ **Zero Missing Values:** All columns in this file have 100% data completeness.")

    # Detected import and quality issues
    issues: List[str] = []
    if high_missing_cols:
        for col in high_missing_cols:
            pct = (missing_by_col[col] / total_rows) * 100.0
            issues.append(
                f"Column **`{col}`** contains **{pct:.1f}%** missing values ({missing_by_col[col]:,} rows)."
            )

    if duplicate_rows_count > 0:
        issues.append(
            f"Dataset contains **{duplicate_rows_count:,}** duplicate row(s) ({(duplicate_rows_count / total_rows) * 100:.2f}% of total)."
        )

    for col in df.columns:
        if missing_by_col[col] == total_rows and total_rows > 0:
            issues.append(f"Column **`{col}`** is completely empty (100% null).")

    if issues:
        st.markdown("##### ⚠️ Detected Import & Data Quality Notes")
        for issue in issues:
            st.warning(issue)
    else:
        st.success("✅ **Validation Passed:** No duplicate rows or critical missing thresholds (>50%) detected.")

    # ── Section 5 — CSV Preview ───────────────────────────────────────────────
    st.subheader("5. CSV Preview")
    st.markdown("Search, sort, and paginate through records in the selected CSV dataset.")

    # State management for search and pagination
    if "dm_page_num" not in st.session_state:
        st.session_state["dm_page_num"] = 1
    if st.session_state.get("dm_active_file") != selected_filename:
        st.session_state["dm_active_file"] = selected_filename
        st.session_state["dm_page_num"] = 1

    search_query = st.text_input(
        "Search records across all columns",
        value="",
        placeholder="Type keyword, ID, date, or status to filter...",
        key=f"search_input_{selected_filename}",
    )

    if st.session_state.get("dm_last_query") != search_query:
        st.session_state["dm_last_query"] = search_query
        st.session_state["dm_page_num"] = 1

    # Filter dataframe based on search keyword
    if search_query.strip():
        term = search_query.strip().lower()
        mask = pd.Series(False, index=df.index)
        for col in df.columns:
            mask |= df[col].astype(str).str.lower().str.contains(term, regex=False, na=False)
        filtered_df = df[mask]
    else:
        filtered_df = df

    PAGE_SIZE = 25
    total_records = len(filtered_df)
    total_pages = max(1, math.ceil(total_records / PAGE_SIZE))

    current_page = st.session_state.get("dm_page_num", 1)
    if current_page > total_pages:
        current_page = total_pages
        st.session_state["dm_page_num"] = current_page
    if current_page < 1:
        current_page = 1
        st.session_state["dm_page_num"] = current_page

    start_idx = (current_page - 1) * PAGE_SIZE
    end_idx = min(start_idx + PAGE_SIZE, total_records)
    page_slice = filtered_df.iloc[start_idx:end_idx]

    # Show preview table
    st.dataframe(page_slice, use_container_width=True)

    # Pagination controls
    col_prev, col_status, col_next = st.columns([1, 3, 1])

    with col_prev:
        if st.button("⬅️ Previous", disabled=(current_page <= 1), key="dm_prev_button"):
            st.session_state["dm_page_num"] = current_page - 1
            st.rerun()

    with col_status:
        filter_note = f" (filtered from {total_rows:,})" if len(filtered_df) < total_rows else ""
        st.markdown(
            f"<div style='text-align: center; line-height: 2.2rem; font-size: 0.95rem;'>"
            f"Page <b>{current_page}</b> of <b>{total_pages}</b> &nbsp;|&nbsp; "
            f"Showing {start_idx + 1 if total_records > 0 else 0}–{end_idx:,} of {total_records:,} records{filter_note}"
            f"</div>",
            unsafe_allow_html=True,
        )

    with col_next:
        if st.button("Next ➡️", disabled=(current_page >= total_pages), key="dm_next_button"):
            st.session_state["dm_page_num"] = current_page + 1
            st.rerun()
