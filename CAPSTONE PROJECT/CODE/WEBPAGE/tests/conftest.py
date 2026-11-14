"""
Shared Test Fixtures
Authors: Monish L (1972260035), Prasannakumar S (1924260253),
         S Hari Surendran (1912260615)
"""

import os
import sys
from pathlib import Path
import pandas as pd
import pytest

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Module-level database availability check
try:
    from app.db import get_ro_connection
    _conn = get_ro_connection()
    _conn.close()
    db_available_flag = True
except Exception:
    db_available_flag = False

# Skip marker for tests requiring live MySQL database
requires_db = pytest.mark.skipif(not db_available_flag, reason="MySQL not available")


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """A small DataFrame with order_month and order_count (5 rows)."""
    return pd.DataFrame({
        "order_month": ["2017-01", "2017-02", "2017-03", "2017-04", "2017-05"],
        "order_count": [750, 1600, 2500, 2300, 3500],
    })


@pytest.fixture
def sample_wide_df() -> pd.DataFrame:
    """A wide DataFrame with 8 columns and 20 rows for testing exports."""
    data = {
        "order_id": [f"ORD_{i:04d}" for i in range(20)],
        "customer_id": [f"CUST_{i:04d}" for i in range(20)],
        "status": ["delivered"] * 20,
        "order_date": [f"2017-01-{(i % 28) + 1:02d}" for i in range(20)],
        "payment_type": ["credit_card"] * 20,
        "payment_value": [100.0 + i * 5 for i in range(20)],
        "state": ["SP"] * 20,
        "category": ["bed_bath_table"] * 20,
    }
    return pd.DataFrame(data)


@pytest.fixture
def db_available() -> bool:
    """Fixture indicating whether MySQL database connection is available."""
    return db_available_flag

sys.path.insert(0, str(PROJECT_ROOT.parent / "SQL"))
