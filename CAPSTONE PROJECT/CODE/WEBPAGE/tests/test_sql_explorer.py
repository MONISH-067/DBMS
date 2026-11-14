"""
SQL Explorer Guard Tests
Authors: Monish L (1972260035), Prasannakumar S (1924260253),
         S Hari Surendran (1912260615)
"""

import pytest
from app.pages.sql_explorer import validate_sql


def test_valid_select():
    """Verify simple SELECT statement passes validation."""
    valid, msg = validate_sql("SELECT * FROM orders")
    assert valid is True
    assert msg == ""


def test_valid_select_with_joins():
    """Verify SELECT statement with JOIN syntax passes validation."""
    valid, msg = validate_sql(
        "SELECT o.order_id FROM orders o JOIN customers c ON c.customer_id = o.customer_id"
    )
    assert valid is True
    assert msg == ""


def test_valid_with_cte():
    """Verify Common Table Expression (WITH ... SELECT) query passes validation."""
    valid, msg = validate_sql("WITH cte AS (SELECT * FROM orders) SELECT * FROM cte")
    assert valid is True
    assert msg == ""


def test_valid_show():
    """Verify SHOW TABLES command passes validation."""
    valid, msg = validate_sql("SHOW TABLES")
    assert valid is True
    assert msg == ""


def test_valid_describe():
    """Verify DESCRIBE table command passes validation."""
    valid, msg = validate_sql("DESCRIBE orders")
    assert valid is True
    assert msg == ""


def test_valid_explain():
    """Verify EXPLAIN query plan command passes validation."""
    valid, msg = validate_sql("EXPLAIN SELECT * FROM orders")
    assert valid is True
    assert msg == ""


def test_reject_empty():
    """Verify empty query string is rejected."""
    valid, msg = validate_sql("")
    assert valid is False
    assert len(msg) > 0


def test_reject_insert():
    """Verify INSERT DML statement is rejected."""
    valid, msg = validate_sql("INSERT INTO orders VALUES (1)")
    assert valid is False
    assert len(msg) > 0


def test_reject_update():
    """Verify UPDATE DML statement is rejected."""
    valid, msg = validate_sql("UPDATE orders SET status = 1")
    assert valid is False
    assert len(msg) > 0


def test_reject_delete():
    """Verify DELETE DML statement is rejected."""
    valid, msg = validate_sql("DELETE FROM orders")
    assert valid is False
    assert len(msg) > 0


def test_reject_drop():
    """Verify DROP DDL statement is rejected."""
    valid, msg = validate_sql("DROP TABLE orders")
    assert valid is False
    assert len(msg) > 0


def test_reject_create():
    """Verify CREATE DDL statement is rejected."""
    valid, msg = validate_sql("CREATE TABLE evil (id INT)")
    assert valid is False
    assert len(msg) > 0


def test_reject_alter():
    """Verify ALTER DDL statement is rejected."""
    valid, msg = validate_sql("ALTER TABLE orders ADD col INT")
    assert valid is False
    assert len(msg) > 0


def test_reject_truncate():
    """Verify TRUNCATE DDL statement is rejected."""
    valid, msg = validate_sql("TRUNCATE TABLE orders")
    assert valid is False
    assert len(msg) > 0


def test_reject_grant():
    """Verify GRANT DCL statement is rejected."""
    valid, msg = validate_sql("GRANT ALL ON olist.* TO user")
    assert valid is False
    assert len(msg) > 0


def test_reject_multi_statement():
    """Verify multiple statements separated by semicolon are rejected."""
    valid, msg = validate_sql("SELECT 1; DROP TABLE orders")
    assert valid is False
    assert len(msg) > 0


def test_allow_trailing_semicolon():
    """Verify a valid SELECT with trailing semicolon is accepted."""
    valid, msg = validate_sql("SELECT * FROM orders;")
    assert valid is True
    assert msg == ""


def test_case_insensitive_rejection():
    """Verify forbidden keywords are rejected regardless of casing."""
    valid, msg = validate_sql("select * from orders; DROP table orders")
    assert valid is False
    assert len(msg) > 0


def test_reject_whitespace_only():
    """Verify whitespace-only query string is rejected."""
    valid, msg = validate_sql("   ")
    assert valid is False
    assert len(msg) > 0
