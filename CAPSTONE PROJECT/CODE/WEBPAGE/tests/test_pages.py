"""
Unit tests for Streamlit pages
Authors: Monish L (1972260035), Prasannakumar S (1924260253),
         S Hari Surendran (1912260615)
"""

import unittest
from app.pages.sql_explorer import validate_sql
import app.pages.normalization as norm
import app.pages.er_diagram as erd
import app.pages.sql_explorer as sql_exp


class TestStreamlitPages(unittest.TestCase):
    def test_page_renders_exist(self):
        self.assertTrue(callable(getattr(norm, "render", None)))
        self.assertTrue(callable(getattr(erd, "render", None)))
        self.assertTrue(callable(getattr(sql_exp, "render", None)))

    def test_validate_sql_valid_queries(self):
        valid_queries = [
            "SELECT * FROM orders",
            "SELECT customer_id, zip_prefix FROM customers WHERE zip_prefix = '01001'",
            "SELECT * FROM orders LIMIT 10;",
            "WITH cte AS (SELECT * FROM orders) SELECT * FROM cte",
            "SHOW TABLES;",
            "DESCRIBE geolocation",
            "DESC customers",
            "EXPLAIN SELECT * FROM orders",
        ]
        for q in valid_queries:
            valid, msg = validate_sql(q)
            self.assertTrue(valid, f"Expected valid for {q!r}, got msg: {msg}")
            self.assertEqual(msg, "")

    def test_validate_sql_empty(self):
        self.assertFalse(validate_sql("")[0])
        self.assertFalse(validate_sql("   \n\t  ")[0])

    def test_validate_sql_forbidden_keywords(self):
        forbidden = [
            "INSERT INTO orders VALUES (1)",
            "UPDATE customers SET zip_prefix = '01001'",
            "DELETE FROM orders WHERE order_id = '123'",
            "DROP TABLE customers",
            "CREATE TABLE test (id INT)",
            "ALTER TABLE orders ADD COLUMN x INT",
            "TRUNCATE TABLE geolocation",
            "GRANT ALL PRIVILEGES ON *.* TO 'user'@'localhost'",
            "REVOKE ALL PRIVILEGES ON *.* FROM 'user'@'localhost'",
            "EXEC sp_test",
            "EXECUTE sp_test",
            "CALL my_procedure()",
        ]
        for q in forbidden:
            valid, msg = validate_sql(q)
            self.assertFalse(valid, f"Expected invalid for {q!r}")

    def test_validate_sql_multiple_statements(self):
        multi = [
            "SELECT * FROM orders; DROP TABLE orders;",
            "SELECT * FROM customers; SELECT * FROM sellers;",
            "SELECT 1; SELECT 2;",
        ]
        for q in multi:
            valid, msg = validate_sql(q)
            self.assertFalse(valid, f"Expected invalid multi-statement for {q!r}")
            self.assertIn("Multiple statements", msg)


if __name__ == "__main__":
    unittest.main()
