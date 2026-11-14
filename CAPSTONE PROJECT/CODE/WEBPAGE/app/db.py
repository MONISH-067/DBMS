"""
Database Connection Helper
Authors: Monish L (1972260035), Prasannakumar S (1924260253),
         S Hari Surendran (1912260615)
"""

import os
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import mysql.connector
from mysql.connector.connection import MySQLConnection
import pandas as pd
from dotenv import find_dotenv, load_dotenv

# Optional Streamlit import for caching or app-level context
try:
    import streamlit as st
except ImportError:
    st = None

# Locate and load .env file from the current directory or any parent directory
_dotenv_path = find_dotenv(usecwd=True)
if _dotenv_path:
    load_dotenv(_dotenv_path)
else:
    load_dotenv()


def _get_connection_params(role: str = "ro") -> dict:
    """
    Retrieve database connection configuration from environment variables.
    Supports 'ro' (read-only) and 'admin' roles with fallback defaults.
    """
    host = os.getenv("MYSQL_HOST", "localhost")
    port = int(os.getenv("MYSQL_PORT", "3306"))
    database = os.getenv("MYSQL_DATABASE", "olist")

    if role == "admin":
        user = os.getenv("MYSQL_ADMIN_USER", "olist_admin")
        password = os.getenv("MYSQL_ADMIN_PASS", "change_me_admin")
    else:
        user = os.getenv("MYSQL_RO_USER", "olist_ro")
        password = os.getenv("MYSQL_RO_PASS", "change_me_ro")

    return {
        "host": host,
        "port": port,
        "database": database,
        "user": user,
        "password": password,
        "use_pure": True,
    }


def get_ro_connection() -> MySQLConnection:
    """
    Establish and return a MySQL read-only connection using MYSQL_RO_USER and MYSQL_RO_PASS.
    Uses use_pure=True for universal Python compatibility.
    """
    config = _get_connection_params("ro")
    return mysql.connector.connect(**config)


def get_admin_connection() -> MySQLConnection:
    """
    Establish and return a MySQL admin connection using MYSQL_ADMIN_USER and MYSQL_ADMIN_PASS.
    Uses use_pure=True for universal Python compatibility.
    """
    config = _get_connection_params("admin")
    return mysql.connector.connect(**config)


def run_query(
    sql: str,
    params: Optional[Union[Dict[str, Any], Sequence[Any]]] = None,
) -> pd.DataFrame:
    """
    Execute a parameterized SQL query using a read-only MySQL connection.
    Returns a pandas DataFrame. Always closes cursor and connection in a finally block.

    Parameters:
        sql: SQL query string (may use %(name)s or %s placeholders).
        params: Optional dict or sequence of bound parameter values.
    """
    conn = None
    cursor = None
    try:
        conn = get_ro_connection()
        cursor = conn.cursor()
        if params is not None:
            cursor.execute(sql, params)
        else:
            # If no parameters are passed, clean any escaped %% back to %
            clean_sql = sql.replace("%%", "%")
            cursor.execute(clean_sql)

        if cursor.description:
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            return pd.DataFrame(rows, columns=columns)
        return pd.DataFrame()
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def run_query_raw(
    sql: str,
    params: Optional[Union[Dict[str, Any], Sequence[Any]]] = None,
) -> Tuple[List[str], List[Tuple[Any, ...]]]:
    """
    Execute a parameterized SQL query using a read-only MySQL connection.
    Returns a tuple (columns, rows) where columns is a list of column names
    and rows is a list of tuples. Always closes cursor and connection in a finally block.

    Parameters:
        sql: SQL query string (may use %(name)s or %s placeholders).
        params: Optional dict or sequence of bound parameter values.
    """
    conn = None
    cursor = None
    try:
        conn = get_ro_connection()
        cursor = conn.cursor()
        if params is not None:
            cursor.execute(sql, params)
        else:
            clean_sql = sql.replace("%%", "%")
            cursor.execute(clean_sql)

        if cursor.description:
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            return columns, rows
        return [], []
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
