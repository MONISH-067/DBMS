"""
Export Tests
Authors: Monish L (1972260035), Prasannakumar S (1924260253),
         S Hari Surendran (1912260615)
"""

from io import BytesIO
import pandas as pd
import pytest

from app.exports import to_csv, to_pdf, to_xlsx


def test_to_csv_returns_bytes(sample_df):
    """Verify to_csv outputs bytes."""
    res = to_csv(sample_df)
    assert isinstance(res, bytes)
    assert len(res) > 0


def test_to_csv_roundtrip(sample_df):
    """Export to CSV, read back into DataFrame, and assert equality."""
    csv_bytes = to_csv(sample_df)
    df_read = pd.read_csv(BytesIO(csv_bytes))
    pd.testing.assert_frame_equal(df_read, sample_df)


def test_to_xlsx_returns_bytes(sample_df):
    """Verify to_xlsx outputs bytes."""
    res = to_xlsx(sample_df)
    assert isinstance(res, bytes)
    assert len(res) > 0


def test_to_xlsx_roundtrip(sample_df):
    """Export to Excel XLSX, read back into DataFrame, and assert equality."""
    xlsx_bytes = to_xlsx(sample_df)
    df_read = pd.read_excel(BytesIO(xlsx_bytes))
    pd.testing.assert_frame_equal(df_read, sample_df)


def test_to_pdf_returns_bytes(sample_df):
    """Verify to_pdf outputs bytes."""
    pdf_bytes = to_pdf(sample_df, "Test")
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0


def test_to_pdf_header(sample_df):
    """Assert PDF output starts with the standard %PDF header magic bytes."""
    pdf_bytes = to_pdf(sample_df, "Test")
    assert pdf_bytes.startswith(b"%PDF")


def test_to_pdf_wide_table(sample_wide_df):
    """Export wide DataFrame (many columns) to PDF and assert valid PDF bytes."""
    pdf_bytes = to_pdf(sample_wide_df, "Wide Table Test")
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")


def test_to_csv_empty_df():
    """Export an empty DataFrame to CSV and verify byte output containing header."""
    empty_df = pd.DataFrame(columns=["order_month", "order_count"])
    csv_bytes = to_csv(empty_df)
    assert isinstance(csv_bytes, bytes)
    assert b"order_month,order_count" in csv_bytes
