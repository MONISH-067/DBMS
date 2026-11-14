"""
Export Helpers (CSV, XLSX, PDF)
Authors: Monish L (1972260035), Prasannakumar S (1924260253),
         S Hari Surendran (1912260615)
"""

import io
from typing import Any, List
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def to_csv(df: pd.DataFrame) -> bytes:
    """
    Export DataFrame to CSV bytes encoded in UTF-8 without index.
    """
    return df.to_csv(index=False).encode("utf-8")


def to_xlsx(df: pd.DataFrame, sheet_name: str = "Report") -> bytes:
    """
    Export DataFrame to Excel (.xlsx) bytes using openpyxl engine via BytesIO buffer.
    """
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return buffer.getvalue()


def to_pdf(df: pd.DataFrame, title: str = "Report") -> bytes:
    """
    Export DataFrame to styled PDF bytes using ReportLab.
    - Page: Landscape A4 format
    - Header: Document title at the top
    - Table: All columns and rows with auto-calculated column widths capped at page width
    - Header row: Blue background with white text
    - Data rows: Alternating row colors for readability
    - Values: Truncated to a maximum of 40 characters
    - Dynamic sizing: Automatically scales down font size (minimum 6pt) for wide tables
    - Output: Raw PDF bytes from a BytesIO buffer
    """
    buffer = io.BytesIO()

    page_width, page_height = landscape(A4)
    margin = 30.0
    usable_width = page_width - (2.0 * margin)

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitleStyle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=colors.HexColor("#1E3D59"),
        spaceAfter=10,
    )

    elements: List[Any] = [
        Paragraph(title, title_style),
        Spacer(1, 8),
    ]

    # Handle empty DataFrame gracefully
    if df.empty or len(df.columns) == 0:
        empty_style = ParagraphStyle(
            "EmptyNoticeStyle",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=10,
            textColor=colors.HexColor("#666666"),
        )
        elements.append(Paragraph("No records found for the requested criteria.", empty_style))
        doc.build(elements)
        return buffer.getvalue()

    # Helper to truncate cell content to at most 40 characters
    def _format_cell(val: Any) -> str:
        if val is None or pd.isna(val):
            return ""
        text = str(val)
        if len(text) > 40:
            return text[:37] + "..."
        return text

    columns = [str(c) for c in df.columns]
    num_cols = len(columns)

    header_data = list(columns)
    body_data = [
        [_format_cell(row[c]) for c in df.columns]
        for _, row in df.iterrows()
    ]
    table_data = [header_data] + body_data

    # Measure maximum character width per column
    col_char_lens: List[int] = []
    for col_idx in range(num_cols):
        max_len = len(header_data[col_idx])
        for row in body_data:
            max_len = max(max_len, len(row[col_idx]))
        col_char_lens.append(max(max_len, 4))

    total_chars = sum(col_char_lens)
    if total_chars == 0:
        col_widths = [usable_width / num_cols] * num_cols
    else:
        # Proportionally allocate column width
        col_widths = [(chars / total_chars) * usable_width for chars in col_char_lens]
        # Guarantee minimum column width
        min_width = min(40.0, usable_width / num_cols)
        col_widths = [max(w, min_width) for w in col_widths]
        # Rescale so the sum strictly equals usable_width
        current_sum = sum(col_widths)
        if current_sum > usable_width:
            col_widths = [(w / current_sum) * usable_width for w in col_widths]

    # Select font sizes and padding based on column count and width
    min_col_w = min(col_widths)
    if num_cols > 10 or min_col_w < 45:
        data_font_size = 6
        header_font_size = 7
        padding = 2
    elif num_cols > 7 or min_col_w < 65:
        data_font_size = 7
        header_font_size = 8
        padding = 3
    elif num_cols > 5 or min_col_w < 85:
        data_font_size = 8
        header_font_size = 9
        padding = 3
    else:
        data_font_size = 9
        header_font_size = 10
        padding = 4

    # Build TableStyle with header coloring and alternating row backgrounds
    table_styles = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3D59")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), header_font_size),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), padding),
        ("BOTTOMPADDING", (0, 0), (-1, -1), padding),
        ("LEFTPADDING", (0, 0), (-1, -1), padding + 1),
        ("RIGHTPADDING", (0, 0), (-1, -1), padding + 1),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), data_font_size),
    ]

    for row_idx in range(1, len(table_data)):
        bg = colors.HexColor("#FFFFFF") if row_idx % 2 != 0 else colors.HexColor("#F2F5F8")
        table_styles.append(("BACKGROUND", (0, row_idx), (-1, row_idx), bg))

    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle(table_styles))
    elements.append(table)

    doc.build(elements)
    return buffer.getvalue()
