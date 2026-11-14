"""
Page 6: Reports
Authors: Monish L (1972260035), Prasannakumar S (1924260253),
         S Hari Surendran (1912260615)
"""

import math
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.exports import to_csv, to_pdf, to_xlsx
from app.reports import get_all_reports, get_report, run_report


@st.cache_data(ttl=600)
def _load_filter_states() -> List[str]:
    """
    Fetch distinct Brazilian states from the geolocation table.
    Falls back to the standard list of 27 federative units if the database query fails.
    """
    try:
        from app.db import run_query
        df = run_query("SELECT DISTINCT state FROM geolocation ORDER BY state")
        if not df.empty and "state" in df.columns:
            return [str(s) for s in df["state"].dropna().tolist()]
    except Exception:
        pass
    return [
        "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA",
        "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN",
        "RO", "RR", "RS", "SC", "SE", "SP", "TO",
    ]


@st.cache_data(ttl=600)
def _load_filter_categories() -> List[str]:
    """
    Fetch distinct category names from product_categories table.
    """
    try:
        from app.db import run_query
        df = run_query("SELECT DISTINCT category_name FROM product_categories ORDER BY category_name")
        if not df.empty and "category_name" in df.columns:
            return [str(c) for c in df["category_name"].dropna().tolist()]
    except Exception:
        pass
    return []


@st.cache_data(ttl=600)
def _load_filter_statuses() -> List[str]:
    """
    Fetch distinct order status values from orders table.
    """
    try:
        from app.db import run_query
        df = run_query("SELECT DISTINCT order_status FROM orders ORDER BY order_status")
        if not df.empty and "order_status" in df.columns:
            return [str(s) for s in df["order_status"].dropna().tolist()]
    except Exception:
        pass
    return [
        "approved", "canceled", "created", "delivered",
        "invoiced", "processing", "shipped", "unavailable",
    ]


def render_chart(report: dict, df: pd.DataFrame, height: int = 400) -> go.Figure:
    """
    Render a Plotly figure based on the report configuration and DataFrame.

    Parameters:
        report: Report definition dictionary containing 'chart_type' and 'title'.
        df: Query results DataFrame.
        height: Height of the chart in pixels (default 400).
    """
    if df is None or df.empty or len(df.columns) < 2:
        fig = go.Figure()
        fig.update_layout(
            title=report.get("title", ""),
            height=height,
            annotations=[{
                "text": "No data available to chart",
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {"size": 14},
            }],
            template="plotly_white",
        )
        return fig

    chart_type = report.get("chart_type", "bar")
    title = report.get("title", "")
    first_col = df.columns[0]
    second_col = df.columns[1]

    if chart_type == "line":
        fig = px.line(df, x=first_col, y=second_col, markers=True, title=title)
    elif chart_type == "donut":
        fig = px.pie(df, names=first_col, values=second_col, hole=0.4, title=title)
    elif chart_type == "hbar":
        fig = px.bar(df, x=second_col, y=first_col, orientation="h", title=title)
        fig.update_layout(yaxis={"autorange": "reversed"})
    elif chart_type in ("bar", "column"):
        fig = px.bar(df, x=first_col, y=second_col, title=title)
    elif chart_type == "grouped_bar":
        if "state" in df.columns and "cnt" in df.columns and "delivery_outcome" in df.columns:
            fig = px.bar(
                df,
                x="state",
                y="cnt",
                color="delivery_outcome",
                barmode="group",
                title=title,
            )
        else:
            fig = px.bar(df, x=first_col, y=second_col, title=title)
    elif chart_type == "histogram":
        fig = px.bar(df, x=first_col, y=second_col, title=title)
    else:
        fig = px.bar(df, x=first_col, y=second_col, title=title)

    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=50, b=20),
        template="plotly_white",
    )
    return fig


def render() -> None:
    """
    Render Page 6: Reports view in Streamlit.
    """
    st.title("Reports")

    # ── 1. Report Selection ─────────────────────────────────────────
    reports = get_all_reports()
    report_map = {f"{r['id']}: {r['title']}": r for r in reports}
    report_labels = list(report_map.keys())

    selected_label = st.selectbox(
        "Select Report",
        options=report_labels,
        help="Select a predefined report to analyze",
    )
    report = report_map[selected_label]
    report_id = report["id"]

    # Show report description below selector
    if report.get("description"):
        st.caption(f"ℹ️ {report['description']}")

    # ── 2. Filters (Sidebar) ───────────────────────────────────────
    # Only show filters relevant to the selected report
    report_filters = report.get("filters", [])
    params: Dict[str, Any] = {}

    st.sidebar.header(f"Filters — {report_id}")

    if "start_date" in report_filters:
        start_val = st.sidebar.date_input(
            "Start Date",
            value=None,
            key=f"rep_start_{report_id}",
        )
        params["start_date"] = start_val.strftime("%Y-%m-%d") if start_val else None
    else:
        params["start_date"] = None

    if "end_date" in report_filters:
        end_val = st.sidebar.date_input(
            "End Date",
            value=None,
            key=f"rep_end_{report_id}",
        )
        params["end_date"] = end_val.strftime("%Y-%m-%d") if end_val else None
    else:
        params["end_date"] = None

    if "state" in report_filters:
        state_options = ["All"] + _load_filter_states()
        state_choice = st.sidebar.selectbox(
            "State",
            options=state_options,
            index=0,
            key=f"rep_state_{report_id}",
        )
        params["state"] = None if state_choice == "All" else state_choice
    else:
        params["state"] = None

    if "category" in report_filters:
        cat_options = ["All"] + _load_filter_categories()
        cat_choice = st.sidebar.selectbox(
            "Product Category",
            options=cat_options,
            index=0,
            key=f"rep_cat_{report_id}",
        )
        params["category"] = None if cat_choice == "All" else cat_choice
    else:
        params["category"] = None

    if "status" in report_filters:
        status_options = ["All"] + _load_filter_statuses()
        status_choice = st.sidebar.selectbox(
            "Order Status",
            options=status_options,
            index=0,
            key=f"rep_status_{report_id}",
        )
        params["status"] = None if status_choice == "All" else status_choice
    else:
        params["status"] = None

    # ── 3. Execute Report ───────────────────────────────────────────
    try:
        df = run_report(report_id, params)
    except Exception as e:
        st.error(f"Failed to execute report {report_id}: {e}")
        return

    # ── 4. Export Buttons (Always Visible) ───────────────────────────
    # All 3 export formats and the visual views derive from the SAME DataFrame
    st.write("")
    col_csv, col_xlsx, col_pdf, _ = st.columns([1, 1, 1, 3])

    with col_csv:
        st.download_button(
            label="📥 CSV",
            data=to_csv(df),
            file_name=f"{report_id}.csv",
            mime="text/csv",
            key=f"dl_csv_{report_id}",
            use_container_width=True,
        )

    with col_xlsx:
        st.download_button(
            label="📥 Excel",
            data=to_xlsx(df),
            file_name=f"{report_id}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"dl_xlsx_{report_id}",
            use_container_width=True,
        )

    with col_pdf:
        st.download_button(
            label="📥 PDF",
            data=to_pdf(df, report["title"]),
            file_name=f"{report_id}.pdf",
            mime="application/pdf",
            key=f"dl_pdf_{report_id}",
            use_container_width=True,
        )

    st.divider()

    # ── 5. Empty State Check ────────────────────────────────────────
    if df is None or df.empty:
        st.info("No data found for the selected filters.")
        return

    # ── 6. Display Mode Toggle ──────────────────────────────────────
    display_mode = st.radio(
        "Display Mode",
        options=["📊 Chart", "📋 Table"],
        horizontal=True,
        key=f"mode_{report_id}",
    )

    # ── 7. Chart Rendering ──────────────────────────────────────────
    if display_mode == "📊 Chart":
        fig = render_chart(report, df, height=480)
        st.plotly_chart(fig, use_container_width=True)

    # ── 8. Table Rendering ──────────────────────────────────────────
    else:
        # Search across all columns
        search_query = st.text_input(
            "🔍 Search Table",
            placeholder="Search across all columns...",
            key=f"search_{report_id}",
        )

        if search_query:
            mask = df.astype(str).apply(
                lambda row: row.str.contains(search_query, case=False, na=False).any(),
                axis=1,
            )
            filtered_df = df[mask]
        else:
            filtered_df = df

        page_size = 25
        total_rows = len(filtered_df)
        total_pages = max(1, math.ceil(total_rows / page_size))

        page_key = f"page_idx_{report_id}"
        if page_key not in st.session_state:
            st.session_state[page_key] = 1

        # Keep current page within bounds
        if st.session_state[page_key] > total_pages:
            st.session_state[page_key] = total_pages
        if st.session_state[page_key] < 1:
            st.session_state[page_key] = 1

        current_page = st.session_state[page_key]
        start_idx = (current_page - 1) * page_size
        end_idx = min(start_idx + page_size, total_rows)

        # Show row count and slice info
        count_msg = f"Showing {start_idx + 1 if total_rows > 0 else 0}–{end_idx} of {total_rows} rows"
        if len(filtered_df) != len(df):
            count_msg += f" (filtered from {len(df)} total records)"
        st.caption(count_msg)

        # Sortable paginated table
        page_slice = filtered_df.iloc[start_idx:end_idx]
        st.dataframe(page_slice, use_container_width=True)

        # Prev / Next navigation
        p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
        with p_col1:
            if st.button("⬅️ Previous", disabled=(current_page <= 1), key=f"prev_{report_id}", use_container_width=True):
                st.session_state[page_key] -= 1
                st.rerun()
        with p_col2:
            st.markdown(
                f"<div style='text-align: center; color: #666; padding-top: 6px;'>"
                f"Page <b>{current_page}</b> of <b>{total_pages}</b>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with p_col3:
            if st.button("Next ➡️", disabled=(current_page >= total_pages), key=f"next_{report_id}", use_container_width=True):
                st.session_state[page_key] += 1
                st.rerun()
