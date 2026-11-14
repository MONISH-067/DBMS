"""
Page 7: Dashboard
Authors: Monish L (1972260035), Prasannakumar S (1924260253),
         S Hari Surendran (1912260615)
"""

from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.db import run_query
from app.reports import get_all_reports, get_report, run_report


@st.cache_data(ttl=600)
def _load_filter_states() -> List[str]:
    """
    Fetch distinct Brazilian states from the geolocation table for the drill-down selector.
    Falls back to standard 27 Brazilian states if the database is unavailable.
    """
    try:
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


@st.cache_data(ttl=300)
def cached_run_report(report_id: str, params: Dict[str, Any]) -> pd.DataFrame:
    """
    Cached wrapper around run_report with a 5-minute (300-second) TTL.
    """
    return run_report(report_id, params)


@st.cache_data(ttl=300)
def _fetch_kpis(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute queries for the 4 dashboard KPI metrics with caching (5-minute TTL).
    """
    results: Dict[str, Any] = {
        "total_orders": None,
        "total_revenue": None,
        "avg_delivery_days": None,
        "avg_review_score": None,
    }

    # 1. Total Orders: SELECT COUNT(*) FROM orders (with date filter if set)
    try:
        sql_orders = """SELECT COUNT(*) AS total_orders
FROM orders o
WHERE (%(start_date)s IS NULL OR o.order_purchase_timestamp >= %(start_date)s)
  AND (%(end_date)s IS NULL OR o.order_purchase_timestamp < %(end_date)s)
  AND (%(state)s IS NULL OR EXISTS (
      SELECT 1 FROM customers c
      JOIN geolocation g ON g.zip_prefix = c.zip_prefix
      WHERE c.customer_id = o.customer_id AND g.state = %(state)s
  ))"""
        df_orders = run_query(sql_orders, params)
        if not df_orders.empty and df_orders.iloc[0, 0] is not None:
            results["total_orders"] = df_orders.iloc[0, 0]
    except Exception:
        pass

    # 2. Total Revenue: SELECT SUM(price) FROM order_items oi JOIN orders o ON o.order_id = oi.order_id (with date filter)
    try:
        sql_revenue = """SELECT SUM(oi.price) AS total_revenue
FROM order_items oi
JOIN orders o ON o.order_id = oi.order_id
WHERE (%(start_date)s IS NULL OR o.order_purchase_timestamp >= %(start_date)s)
  AND (%(end_date)s IS NULL OR o.order_purchase_timestamp < %(end_date)s)
  AND (%(state)s IS NULL OR EXISTS (
      SELECT 1 FROM customers c
      JOIN geolocation g ON g.zip_prefix = c.zip_prefix
      WHERE c.customer_id = o.customer_id AND g.state = %(state)s
  ))"""
        df_rev = run_query(sql_revenue, params)
        if not df_rev.empty and df_rev.iloc[0, 0] is not None:
            results["total_revenue"] = df_rev.iloc[0, 0]
    except Exception:
        pass

    # 3. Avg Delivery Days: SELECT ROUND(AVG(delivery_days), 1) FROM v_delivery_performance WHERE delivery_days IS NOT NULL (with date/state filter)
    try:
        sql_delivery = """SELECT ROUND(AVG(vdp.delivery_days), 1) AS avg_delivery_days
FROM v_delivery_performance vdp
WHERE vdp.delivery_days IS NOT NULL
  AND (%(start_date)s IS NULL OR vdp.order_purchase_timestamp >= %(start_date)s)
  AND (%(end_date)s IS NULL OR vdp.order_purchase_timestamp < %(end_date)s)
  AND (%(state)s IS NULL OR vdp.state = %(state)s)"""
        df_del = run_query(sql_delivery, params)
        if not df_del.empty and df_del.iloc[0, 0] is not None:
            results["avg_delivery_days"] = df_del.iloc[0, 0]
    except Exception:
        pass

    # 4. Avg Review Score: SELECT ROUND(AVG(review_score), 1) FROM order_reviews r JOIN orders o ON o.order_id = r.order_id (with date filter)
    try:
        sql_reviews = """SELECT ROUND(AVG(r.review_score), 1) AS avg_review_score
FROM order_reviews r
JOIN orders o ON o.order_id = r.order_id
WHERE (%(start_date)s IS NULL OR o.order_purchase_timestamp >= %(start_date)s)
  AND (%(end_date)s IS NULL OR o.order_purchase_timestamp < %(end_date)s)
  AND (%(state)s IS NULL OR EXISTS (
      SELECT 1 FROM customers c
      JOIN geolocation g ON g.zip_prefix = c.zip_prefix
      WHERE c.customer_id = o.customer_id AND g.state = %(state)s
  ))"""
        df_revw = run_query(sql_reviews, params)
        if not df_revw.empty and df_revw.iloc[0, 0] is not None:
            results["avg_review_score"] = df_revw.iloc[0, 0]
    except Exception:
        pass

    return results


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


def _render_dashboard_card(report_id: str, base_params: Dict[str, Any]) -> None:
    """
    Render a single report container in the dashboard grid.
    """
    report = get_report(report_id)
    with st.container():
        show_table = st.toggle(
            "📋 Table view",
            key=f"dash_toggle_{report_id}",
            value=False,
        )

        try:
            df = cached_run_report(report_id, base_params)
        except Exception as e:
            st.error(f"Error loading {report['title']}: {e}")
            df = pd.DataFrame()

        if df is None or df.empty:
            st.info(f"No data available for {report['title']}.")
        elif show_table:
            st.markdown(f"**{report['title']}**")
            st.dataframe(df, use_container_width=True, height=350)
        else:
            fig = render_chart(report, df, height=350)
            st.plotly_chart(fig, use_container_width=True)


def render() -> None:
    """
    Render Page 7: Dashboard view in Streamlit.
    """
    st.title("Dashboard")

    # ── 1. Global Filters (Sidebar) ─────────────────────────────────
    st.sidebar.header("Dashboard Filters")

    # Session state initialization for filters
    if "dash_start_date" not in st.session_state:
        st.session_state["dash_start_date"] = None
    if "dash_end_date" not in st.session_state:
        st.session_state["dash_end_date"] = None
    if "dash_state" not in st.session_state:
        st.session_state["dash_state"] = "All"

    def _reset_filters() -> None:
        st.session_state["dash_start_date"] = None
        st.session_state["dash_end_date"] = None
        st.session_state["dash_state"] = "All"

    start_date_val = st.sidebar.date_input(
        "Start Date",
        key="dash_start_date",
    )
    end_date_val = st.sidebar.date_input(
        "End Date",
        key="dash_end_date",
    )

    states = ["All"] + _load_filter_states()
    selected_state = st.sidebar.selectbox(
        "State Drill-down",
        options=states,
        key="dash_state",
        help="Selecting a state re-runs all state-supporting reports and KPI metrics filtered to that state",
    )

    st.sidebar.button(
        "🔄 Clear Filters",
        on_click=_reset_filters,
        use_container_width=True,
    )

    # Build base params dictionary
    start_date_str = start_date_val.strftime("%Y-%m-%d") if start_date_val else None
    end_date_str = end_date_val.strftime("%Y-%m-%d") if end_date_val else None
    state_filter = None if selected_state == "All" else selected_state

    base_params: Dict[str, Any] = {
        "start_date": start_date_str,
        "end_date": end_date_str,
        "state": state_filter,
        "status": None,
        "category": None,
    }

    # ── 2. Row 1: KPI Cards ─────────────────────────────────────────
    kpi_data = _fetch_kpis(base_params)

    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    with kpi_col1:
        total_orders = kpi_data.get("total_orders")
        orders_disp = f"{int(total_orders):,}" if total_orders is not None and not pd.isna(total_orders) else "N/A"
        st.metric("Total Orders", orders_disp)

    with kpi_col2:
        total_revenue = kpi_data.get("total_revenue")
        rev_disp = f"R$ {float(total_revenue):,.2f}" if total_revenue is not None and not pd.isna(total_revenue) else "N/A"
        st.metric("Total Revenue", rev_disp)

    with kpi_col3:
        avg_days = kpi_data.get("avg_delivery_days")
        days_disp = f"{float(avg_days):.1f}" if avg_days is not None and not pd.isna(avg_days) else "N/A"
        st.metric("Avg Delivery Days", days_disp)

    with kpi_col4:
        avg_score = kpi_data.get("avg_review_score")
        score_disp = f"{float(avg_score):.1f}" if avg_score is not None and not pd.isna(avg_score) else "N/A"
        st.metric("Avg Review Score", score_disp)

    st.divider()

    # ── 3. Row 2+: Charts in 2-Column Grid ──────────────────────────
    # 5 rows × 2 columns: R01-R02, R03-R04, R05-R06, R07-R08, R09-R10
    report_pairs = [
        ("R01", "R02"),
        ("R03", "R04"),
        ("R05", "R06"),
        ("R07", "R08"),
        ("R09", "R10"),
    ]

    with st.spinner("Loading dashboard reports..."):
        for id_a, id_b in report_pairs:
            c1, c2 = st.columns(2)
            with c1:
                _render_dashboard_card(id_a, base_params)
            with c2:
                _render_dashboard_card(id_b, base_params)
            st.write("")
