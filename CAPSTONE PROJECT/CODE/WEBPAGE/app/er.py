"""
ER Diagram Generator
Authors: Monish L (1972260035), Prasannakumar S (1924260253),
         S Hari Surendran (1912260615)
"""

import html
import os
import shutil
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from app import db
except ImportError:
    import db

try:
    import graphviz

    # Check whether the Graphviz 'dot' binary is executable on the system PATH
    GRAPHVIZ_AVAILABLE = shutil.which("dot") is not None
except ImportError:
    graphviz = None
    GRAPHVIZ_AVAILABLE = False


# Canonical 3NF metadata used as fallback if database is offline or unpopulated
STATIC_SCHEMA: Dict[str, Dict[str, Any]] = {
    "geolocation": {
        "columns": [
            ("zip_prefix", "VARCHAR(5)", True),
            ("city", "VARCHAR(100)", False),
            ("state", "CHAR(2)", False),
            ("avg_lat", "DECIMAL(10,6)", False),
            ("avg_lng", "DECIMAL(10,6)", False),
        ],
    },
    "customers": {
        "columns": [
            ("customer_id", "CHAR(32)", True),
            ("customer_unique_id", "CHAR(32)", False),
            ("zip_prefix", "VARCHAR(5)", False),
        ],
    },
    "sellers": {
        "columns": [
            ("seller_id", "CHAR(32)", True),
            ("zip_prefix", "VARCHAR(5)", False),
        ],
    },
    "product_categories": {
        "columns": [
            ("category_name", "VARCHAR(100)", True),
            ("category_name_en", "VARCHAR(100)", False),
        ],
    },
    "products": {
        "columns": [
            ("product_id", "CHAR(32)", True),
            ("category_name", "VARCHAR(100)", False),
            ("weight_g", "INT", False),
            ("length_cm", "INT", False),
            ("height_cm", "INT", False),
            ("width_cm", "INT", False),
            ("photos_qty", "INT", False),
        ],
    },
    "orders": {
        "columns": [
            ("order_id", "CHAR(32)", True),
            ("customer_id", "CHAR(32)", False),
            ("order_status", "VARCHAR(20)", False),
            ("order_purchase_timestamp", "DATETIME", False),
            ("order_approved_at", "DATETIME", False),
            ("order_delivered_carrier_date", "DATETIME", False),
            ("order_delivered_customer_date", "DATETIME", False),
            ("order_estimated_delivery_date", "DATETIME", False),
        ],
    },
    "order_items": {
        "columns": [
            ("order_id", "CHAR(32)", True),
            ("order_item_id", "INT", True),
            ("product_id", "CHAR(32)", False),
            ("seller_id", "CHAR(32)", False),
            ("shipping_limit_date", "DATETIME", False),
            ("price", "DECIMAL(10,2)", False),
            ("freight_value", "DECIMAL(10,2)", False),
        ],
    },
    "order_payments": {
        "columns": [
            ("order_id", "CHAR(32)", True),
            ("payment_sequential", "INT", True),
            ("payment_type", "VARCHAR(30)", False),
            ("installments", "INT", False),
            ("payment_value", "DECIMAL(10,2)", False),
        ],
    },
    "order_reviews": {
        "columns": [
            ("review_id", "CHAR(32)", True),
            ("order_id", "CHAR(32)", True),
            ("review_score", "TINYINT", False),
            ("review_comment_title", "TEXT", False),
            ("review_comment_message", "TEXT", False),
            ("review_creation_date", "DATETIME", False),
            ("review_answer_timestamp", "DATETIME", False),
        ],
    },
}

STATIC_FOREIGN_KEYS: List[Dict[str, str]] = [
    {"fk_table": "customers", "fk_column": "zip_prefix", "pk_table": "geolocation", "pk_column": "zip_prefix"},
    {"fk_table": "sellers", "fk_column": "zip_prefix", "pk_table": "geolocation", "pk_column": "zip_prefix"},
    {"fk_table": "products", "fk_column": "category_name", "pk_table": "product_categories", "pk_column": "category_name"},
    {"fk_table": "orders", "fk_column": "customer_id", "pk_table": "customers", "pk_column": "customer_id"},
    {"fk_table": "order_items", "fk_column": "order_id", "pk_table": "orders", "pk_column": "order_id"},
    {"fk_table": "order_items", "fk_column": "product_id", "pk_table": "products", "pk_column": "product_id"},
    {"fk_table": "order_items", "fk_column": "seller_id", "pk_table": "sellers", "pk_column": "seller_id"},
    {"fk_table": "order_payments", "fk_column": "order_id", "pk_table": "orders", "pk_column": "order_id"},
    {"fk_table": "order_reviews", "fk_column": "order_id", "pk_table": "orders", "pk_column": "order_id"},
]


def _fetch_schema_from_db() -> Tuple[Dict[str, List[Tuple[str, str, bool]]], List[Dict[str, str]]]:
    """
    Query information_schema for tables, columns, primary keys, and foreign keys.
    Returns (tables_dict, foreign_keys_list).
    """
    db_name = os.getenv("MYSQL_DATABASE", "olist")
    schema_params = {"schema": db_name}

    conn = None
    cursor = None
    try:
        conn = db.get_ro_connection()
        cursor = conn.cursor()

        # 1. Fetch PK columns via TABLE_CONSTRAINTS & KEY_COLUMN_USAGE
        pk_sql = """
        SELECT tc.TABLE_NAME, kcu.COLUMN_NAME
        FROM information_schema.TABLE_CONSTRAINTS tc
        JOIN information_schema.KEY_COLUMN_USAGE kcu
          ON tc.CONSTRAINT_SCHEMA = kcu.CONSTRAINT_SCHEMA
         AND tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
         AND tc.TABLE_NAME = kcu.TABLE_NAME
        WHERE tc.CONSTRAINT_SCHEMA = %(schema)s
          AND tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
        ORDER BY tc.TABLE_NAME, kcu.ORDINAL_POSITION
        """
        cursor.execute(pk_sql, schema_params)
        pk_set: Set[Tuple[str, str]] = set()
        for tbl, col in cursor.fetchall():
            pk_set.add((tbl, col))

        # Cross-reference with STATISTICS for primary keys
        stat_sql = """
        SELECT TABLE_NAME, COLUMN_NAME
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = %(schema)s
          AND INDEX_NAME = 'PRIMARY'
        ORDER BY TABLE_NAME, SEQ_IN_INDEX
        """
        cursor.execute(stat_sql, schema_params)
        for tbl, col in cursor.fetchall():
            pk_set.add((tbl, col))

        # 2. Fetch all columns for BASE TABLEs
        col_sql = """
        SELECT c.TABLE_NAME, c.COLUMN_NAME, c.COLUMN_TYPE
        FROM information_schema.COLUMNS c
        JOIN information_schema.TABLES t
          ON c.TABLE_SCHEMA = t.TABLE_SCHEMA AND c.TABLE_NAME = t.TABLE_NAME
        WHERE c.TABLE_SCHEMA = %(schema)s
          AND t.TABLE_TYPE = 'BASE TABLE'
        ORDER BY c.TABLE_NAME, c.ORDINAL_POSITION
        """
        cursor.execute(col_sql, schema_params)
        tables: Dict[str, List[Tuple[str, str, bool]]] = {}
        for tbl, col, col_type in cursor.fetchall():
            is_pk = (tbl, col) in pk_set
            if tbl not in tables:
                tables[tbl] = []
            tables[tbl].append((col, col_type, is_pk))

        # 3. Fetch foreign key relationships
        fk_sql = """
        SELECT
            kcu.TABLE_NAME AS fk_table,
            kcu.COLUMN_NAME AS fk_column,
            kcu.REFERENCED_TABLE_NAME AS pk_table,
            kcu.REFERENCED_COLUMN_NAME AS pk_column
        FROM information_schema.KEY_COLUMN_USAGE kcu
        WHERE kcu.TABLE_SCHEMA = %(schema)s
          AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
        ORDER BY kcu.TABLE_NAME, kcu.ORDINAL_POSITION
        """
        cursor.execute(fk_sql, schema_params)
        fks: List[Dict[str, str]] = []
        for fk_tbl, fk_col, pk_tbl, pk_col in cursor.fetchall():
            fks.append({
                "fk_table": fk_tbl,
                "fk_column": fk_col,
                "pk_table": pk_tbl,
                "pk_column": pk_col,
            })

        if tables:
            return tables, fks

    except Exception:
        pass
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

    # Fallback to static schema metadata if DB query fails or returned no tables
    static_tables = {
        tbl: meta["columns"]
        for tbl, meta in STATIC_SCHEMA.items()
    }
    return static_tables, STATIC_FOREIGN_KEYS


def generate_er_diagram() -> Optional[Any]:
    """
    Generate an Entity-Relationship (ER) diagram using Graphviz Digraph.
    Queries information_schema for tables, columns, PKs, and FKs.
    Constructs HTML-like node records with primary keys highlighted.
    Connects foreign keys with 1-to-many cardinality notation.
    Uses engine='dot' and rankdir='LR'.
    Returns the Digraph object, or None if graphviz library is not installed.
    """
    if graphviz is None:
        return None

    tables, fks = _fetch_schema_from_db()

    dot = graphviz.Digraph(
        name="Olist_ERD",
        engine="dot",
        graph_attr={
            "rankdir": "LR",
            "nodesep": "0.6",
            "ranksep": "1.0",
            "bgcolor": "#FAFAFA",
            "fontsize": "11",
            "fontname": "Helvetica",
        },
        node_attr={
            "shape": "none",
            "fontsize": "10",
            "fontname": "Helvetica",
        },
        edge_attr={
            "fontsize": "9",
            "fontname": "Helvetica",
            "color": "#4A5568",
            "arrowsize": "0.8",
        },
    )

    # Add each table as an HTML-like record node
    for table_name, columns in tables.items():
        rows_html = [
            f'<tr><td bgcolor="#1E3D59" colspan="2" align="center">'
            f'<font color="white"><b>{html.escape(table_name)}</b></font></td></tr>'
        ]
        for col_name, col_type, is_pk in columns:
            if is_pk:
                col_display = f"<b>[PK] {html.escape(col_name)}</b>"
            else:
                col_display = html.escape(col_name)
            type_display = f'<font color="#555555">{html.escape(str(col_type).upper())}</font>'
            rows_html.append(
                f'<tr><td align="left">{col_display}</td><td align="right">{type_display}</td></tr>'
            )

        html_label = (
            '<<table border="1" cellborder="0" cellspacing="0" cellpadding="4" '
            'bgcolor="#FFFFFF" color="#CCCCCC">'
            + "".join(rows_html)
            + "</table>>"
        )
        dot.node(table_name, label=html_label, shape="none")

    # Add foreign key relationships as edges with 1-to-many cardinality notation
    for fk in fks:
        pk_tbl = fk["pk_table"]
        fk_tbl = fk["fk_table"]
        fk_col = fk["fk_column"]
        dot.edge(
            pk_tbl,
            fk_tbl,
            label=f" {fk_col} ",
            taillabel="1",
            headlabel="*",
            arrowhead="crow",
            arrowtail="none",
            dir="both",
            fontsize="8",
            fontcolor="#333333",
        )

    return dot


def er_to_png(dot: Any) -> bytes:
    """
    Render a Graphviz Digraph to PNG image bytes using dot.pipe(format='png').
    """
    return dot.pipe(format="png")


def er_to_pdf(dot: Any) -> bytes:
    """
    Render a Graphviz Digraph to PDF document bytes using dot.pipe(format='pdf').
    """
    return dot.pipe(format="pdf")


def generate_er_fallback() -> str:
    """
    Generate a text-based representation of the 3NF schema relationships.
    Returns a formatted string detailing tables, primary keys, data types,
    and foreign key links. Used when Graphviz binaries are unavailable.
    """
    tables, fks = _fetch_schema_from_db()

    lines = [
        "=" * 80,
        "OLIST E-COMMERCE DATABASE  -  ENTITY RELATIONSHIP SCHEMA (3NF)",
        "=" * 80,
        "",
        "TABLES & COLUMNS:",
        "-" * 80,
    ]

    for table_name, columns in sorted(tables.items()):
        lines.append(f"[{table_name}]")
        for col_name, col_type, is_pk in columns:
            pk_badge = "[PK]" if is_pk else "    "
            lines.append(f"    {pk_badge} {col_name:<28} {col_type}")
        lines.append("")

    lines.append("-" * 80)
    lines.append("FOREIGN KEY RELATIONSHIPS (1 : N):")
    lines.append("-" * 80)

    for fk in fks:
        rel_str = f"  {fk['pk_table']}.{fk['pk_column']} (1) ---> (N) {fk['fk_table']}.{fk['fk_column']}"
        lines.append(rel_str)

    lines.append("=" * 80)
    return "\n".join(lines)
