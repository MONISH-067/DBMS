"""
ETL Tests
Authors: Monish L (1972260035), Prasannakumar S (1924260253),
         S Hari Surendran (1912260615)
"""

import numpy as np
import pandas as pd
import pytest


def test_geolocation_dedup():
    """Simulate raw geolocation CSV grouping by zip prefix with avg lat/lng and first city/state."""
    raw_geo = pd.DataFrame({
        "geolocation_zip_code_prefix": ["01001", "01001", "02002", "02002", "02002"],
        "geolocation_lat": [-23.55, -23.57, -22.90, -22.92, -22.94],
        "geolocation_lng": [-46.63, -46.65, -43.18, -43.20, -43.22],
        "geolocation_city": ["sao paulo", "sao paulo", "rio de janeiro", "rio", "rio"],
        "geolocation_state": ["SP", "SP", "RJ", "RJ", "RJ"],
    })

    agg_df = raw_geo.groupby("geolocation_zip_code_prefix", as_index=False).agg({
        "geolocation_city": "first",
        "geolocation_state": "first",
        "geolocation_lat": "mean",
        "geolocation_lng": "mean",
    })

    assert len(agg_df) == 2
    assert set(agg_df["geolocation_zip_code_prefix"]) == {"01001", "02002"}

    row_01001 = agg_df[agg_df["geolocation_zip_code_prefix"] == "01001"].iloc[0]
    assert abs(row_01001["geolocation_lat"] - (-23.56)) < 1e-4
    assert abs(row_01001["geolocation_lng"] - (-46.64)) < 1e-4
    assert row_01001["geolocation_city"] == "sao paulo"
    assert row_01001["geolocation_state"] == "SP"

    row_02002 = agg_df[agg_df["geolocation_zip_code_prefix"] == "02002"].iloc[0]
    assert abs(row_02002["geolocation_lat"] - (-22.92)) < 1e-4
    assert abs(row_02002["geolocation_lng"] - (-43.20)) < 1e-4
    assert row_02002["geolocation_city"] == "rio de janeiro"
    assert row_02002["geolocation_state"] == "RJ"


def test_stub_zip_creation():
    """Verify difference between customer zip set and geolocation zip set yields stub rows."""
    geo_zips = {"01001", "01002", "01003"}
    customer_zips = {"01001", "01002", "99999", "88888"}

    missing_zips = sorted(customer_zips - geo_zips)
    assert missing_zips == ["88888", "99999"]

    # Generate stub records as performed by import_olist.py
    stub_records = [(z, "UNKNOWN", "XX", 0.0, 0.0) for z in missing_zips]
    assert len(stub_records) == 2
    assert stub_records[0] == ("88888", "UNKNOWN", "XX", 0.0, 0.0)
    assert stub_records[1] == ("99999", "UNKNOWN", "XX", 0.0, 0.0)


def test_nan_to_none_conversion():
    """Verify conversion of NaN, NaT, and pd.NA values to Python None using df.where."""
    df = pd.DataFrame({
        "col_float": [1.5, np.nan],
        "col_ts": [pd.Timestamp("2021-01-01"), pd.NaT],
        "col_str": ["valid_string", pd.NA],
    }, dtype=object)

    cleaned = df.where(df.notna(), None)

    assert cleaned.loc[0, "col_float"] == 1.5
    assert cleaned.loc[1, "col_float"] is None

    assert cleaned.loc[0, "col_ts"] == pd.Timestamp("2021-01-01")
    assert cleaned.loc[1, "col_ts"] is None

    assert cleaned.loc[0, "col_str"] == "valid_string"
    assert cleaned.loc[1, "col_str"] is None

    # Assert None values are present
    assert None in cleaned.values


def test_timestamp_parsing():
    """Verify timestamp parsing using pd.to_datetime produces valid datetime objects."""
    ts_str = "2017-10-02 10:56:33"
    dt = pd.to_datetime(ts_str)

    assert isinstance(dt, pd.Timestamp)
    assert dt.year == 2017
    assert dt.month == 10
    assert dt.day == 2
    assert dt.hour == 10
    assert dt.minute == 56
    assert dt.second == 33


def test_category_merge():
    """Verify translation merge assigns None for untranslated categories."""
    products_df = pd.DataFrame({
        "product_id": ["p1", "p2", "p3"],
        "category_name": ["beleza_saude", "informatica_acessorios", "categoria_desconhecida"],
    })

    translation_df = pd.DataFrame({
        "category_name": ["beleza_saude", "informatica_acessorios"],
        "category_name_en": ["health_beauty", "computers_accessories"],
    })

    merged = pd.merge(products_df, translation_df, on="category_name", how="left")
    merged = merged.astype(object).where(merged.notna(), None)

    assert len(merged) == 3

    row_p1 = merged[merged["product_id"] == "p1"].iloc[0]
    assert row_p1["category_name_en"] == "health_beauty"

    row_p2 = merged[merged["product_id"] == "p2"].iloc[0]
    assert row_p2["category_name_en"] == "computers_accessories"

    row_p3 = merged[merged["product_id"] == "p3"].iloc[0]
    assert row_p3["category_name_en"] is None
