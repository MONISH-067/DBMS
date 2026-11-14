"""
Report Tests
Authors: Monish L (1972260035), Prasannakumar S (1924260253),
         S Hari Surendran (1912260615)
"""

import re
import pandas as pd
import pytest

from app.reports import get_all_reports, get_report, run_report

try:
    from conftest import requires_db
except ImportError:
    from tests.conftest import requires_db

ALLOWED_CHART_TYPES = {
    "line",
    "donut",
    "hbar",
    "bar",
    "column",
    "grouped_bar",
    "histogram",
}

EXPECTED_REPORT_KEYS = {
    "id",
    "title",
    "description",
    "chart_type",
    "sql",
    "default_params",
    "filters",
}


def test_report_registry_completeness():
    """Assert 10 registered reports and each contains all required schema keys."""
    reports = get_all_reports()
    assert len(reports) == 10

    for r in reports:
        for key in EXPECTED_REPORT_KEYS:
            assert key in r, f"Report {r.get('id')} missing key '{key}'"


def test_report_ids_unique():
    """Assert all report IDs in the registry are unique."""
    reports = get_all_reports()
    ids = [r["id"] for r in reports]
    assert len(ids) == len(set(ids)), f"Duplicate report IDs found: {ids}"


def test_report_ids_format():
    """Assert each report ID conforms to the R01-R10 naming pattern."""
    reports = get_all_reports()
    pattern = re.compile(r"^R(0[1-9]|10)$")
    for r in reports:
        assert pattern.match(r["id"]), f"Report ID '{r['id']}' does not match R01-R10"


def test_get_report_valid():
    """Assert get_report with valid ID returns the report definition."""
    rep = get_report("R01")
    assert isinstance(rep, dict)
    assert rep["id"] == "R01"
    assert "Monthly Orders" in rep["title"]


def test_get_report_invalid():
    """Assert get_report with unknown ID raises an error or returns None."""
    try:
        res = get_report("R99")
        assert res is None
    except Exception as exc:
        assert isinstance(exc, (KeyError, ValueError, LookupError))


def test_report_sql_has_bound_params():
    """Verify each report SQL uses parameterized binding syntax."""
    reports = get_all_reports()
    for r in reports:
        sql = r["sql"]
        has_bound = "%(start_date)s" in sql or "%(end_date)s" in sql
        assert has_bound, f"Report {r['id']} SQL does not contain bound date parameters"


def test_report_chart_types():
    """Assert each report's chart_type belongs to the allowed visualization types."""
    reports = get_all_reports()
    for r in reports:
        assert r["chart_type"] in ALLOWED_CHART_TYPES, (
            f"Report {r['id']} has invalid chart_type: {r['chart_type']}"
        )


def test_default_params_keys():
    """Verify default_params dictionary matches filter keys with None defaults."""
    reports = get_all_reports()
    for r in reports:
        defaults = r["default_params"]
        filters = r["filters"]
        for f in filters:
            assert f in defaults, f"Filter '{f}' missing from default_params in report {r['id']}"
            assert defaults[f] is None, f"Default value for filter '{f}' in {r['id']} should be None"


@requires_db
def test_run_report_r01():
    """Execute report R01 against a live MySQL database and assert DataFrame return."""
    df = run_report("R01", {})
    assert isinstance(df, pd.DataFrame)


@requires_db
def test_run_all_reports():
    """Execute all 10 reports with default parameters against live database."""
    reports = get_all_reports()
    for r in reports:
        df = run_report(r["id"], r["default_params"])
        assert isinstance(df, pd.DataFrame), f"Report {r['id']} did not return a DataFrame"


@requires_db
def test_monthly_reports_return_calendar_months():
    from app.reports import run_report
    for report_id in ("R01", "R05"):
        frame = run_report(report_id, {})
        assert len(frame) > 1
        assert frame["order_month"].str.fullmatch(r"\d{4}-\d{2}").all()
