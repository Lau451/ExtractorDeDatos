"""CSV formatters for all five document types.

Each formatter accepts an extraction_result dict (as returned by
model.model_dump()) and returns UTF-8-with-BOM CSV bytes.

Column order matches the Pydantic model field declaration order.
None values are rendered as empty cells (never as the string "None").
Line-item document types produce one row per line item, with header
fields repeated on every row. Header-only document types produce a
single data row.
"""
import csv
import io
import re
from datetime import datetime
from typing import Callable

from src.extraction.schemas.invoice import InvoiceLineItem, InvoiceResult
from src.extraction.schemas.purchase_order import POLineItem, PurchaseOrderResult
from src.extraction.schemas.quotation import QuotationLineItem
from src.extraction.schemas.supplier_comparison import SupplierComparisonResult, SupplierRow
from src.extraction.schemas.tender_rfq import TenderLineItem


# ---------------------------------------------------------------------------
# Value normalization
# ---------------------------------------------------------------------------

_AMOUNT_KEYWORDS = ("amount", "price", "total", "subtotal", "tax")
_DATE_KEYWORDS = ("date",)
_DATE_SUFFIXES = ("_at",)
_QUANTITY_FIELD_NAMES = ("quantity",)


def _is_amount_field(name: str) -> bool:
    return any(kw in name for kw in _AMOUNT_KEYWORDS)


def _is_date_field(name: str) -> bool:
    return any(kw in name for kw in _DATE_KEYWORDS) or any(
        name.endswith(s) for s in _DATE_SUFFIXES
    )


def _is_quantity_field(name: str) -> bool:
    return name in _QUANTITY_FIELD_NAMES


_DATE_FORMATS = [
    "%d/%m/%Y", "%d-%m-%Y",
    "%Y-%m-%d", "%Y/%m/%d",
    "%d %B %Y", "%d %b %Y",
    "%B %d, %Y", "%b %d, %Y",
    "%m/%d/%Y",
]


def _normalize_amount(value: str) -> str:
    cleaned = re.sub(r"[^\d.,-]", "", value).replace(",", "")
    try:
        float(cleaned)
        return cleaned
    except ValueError:
        return value


def _normalize_date(value: str) -> str:
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    return value


def _normalize_text(value: str) -> str:
    return re.sub(r" +", " ", value.strip())


def normalize_quantity(value: str) -> str:
    m = re.match(r"^(\d+(?:\.\d+)?)", value.strip())
    if not m:
        return value
    numeric_part = m.group(1)
    try:
        as_float = float(numeric_part)
        if as_float == int(as_float):
            return str(int(as_float))
        return numeric_part
    except ValueError:
        return value


def normalize_cell(field_name: str, value) -> str:
    if value is None:
        return "Not found"
    s = str(value)
    if not s.strip():
        return "Not found"
    if _is_amount_field(field_name):
        return _normalize_amount(s)
    if _is_date_field(field_name):
        return _normalize_date(s)
    if _is_quantity_field(field_name):
        return normalize_quantity(s)
    return _normalize_text(s)


# ---------------------------------------------------------------------------
# Mandatory field enforcement
# ---------------------------------------------------------------------------

MANDATORY_FIELDS: dict[str, list[str]] = {
    "purchase_order": ["po_number", "issue_date", "buyer_name", "supplier_name"],
    "tender_rfq": [],
    "quotation": [],
    "invoice": ["invoice_number", "invoice_date", "issuer_name"],
    "supplier_comparison": ["project_name", "comparison_date", "rfq_reference"],
}


def check_mandatory_fields(doc_type: str, extraction_result: dict) -> list[str]:
    required = MANDATORY_FIELDS.get(doc_type, [])
    missing = []
    for field in required:
        val = extraction_result.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            missing.append(field)
    return missing


# ---------------------------------------------------------------------------
# Shared helper: write CSV bytes with UTF-8 BOM
# ---------------------------------------------------------------------------


def _make_csv_bytes(headers: list[str], rows: list[list]) -> bytes:
    """Encode *headers* and *rows* as UTF-8-with-BOM CSV bytes.

    The BOM (\ufeff) is written as the very first character of the text
    buffer so that the resulting bytes begin with b'\\xef\\xbb\\xbf'.
    """
    buf = io.StringIO()
    buf.write("\ufeff")
    writer = csv.writer(buf, lineterminator="\r\n")
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return buf.getvalue().encode("utf-8")


# ---------------------------------------------------------------------------
# Private helpers: line-item and header-only formatters
# ---------------------------------------------------------------------------


def _format_line_item_type(model_class, item_model_class, extraction_result: dict) -> bytes:
    """Format a document type that has a ``line_items`` list.

    One CSV row is emitted per line item, with the header-level field values
    repeated on every row. If the document contains zero line items, a single
    data row is emitted with empty cells for all line-item columns.
    """
    result = model_class.model_validate(extraction_result)

    # Header-level column names (excluding the line_items list field itself)
    header_fields = [f for f in model_class.model_fields if f != "line_items"]
    # Line-item column names
    item_fields = list(item_model_class.model_fields.keys())
    columns = header_fields + item_fields

    # Values for the header-level fields (same for every row)
    header_values = [getattr(result, f) for f in header_fields]

    if not result.line_items:
        # Zero line items → single row with empty line-item cells
        raw_rows = [header_values + [None] * len(item_fields)]
    else:
        raw_rows = [
            header_values + [getattr(item, f) for f in item_fields]
            for item in result.line_items
        ]

    all_fields = header_fields + item_fields
    clean_rows = [
        [normalize_cell(all_fields[i], v) for i, v in enumerate(row)]
        for row in raw_rows
    ]

    return _make_csv_bytes(columns, clean_rows)


def _format_header_only_type(model_class, extraction_result: dict) -> bytes:
    """Format a document type that has no line items (header fields only).

    Always produces exactly one data row.
    """
    result = model_class.model_validate(extraction_result)
    fields = list(model_class.model_fields.keys())
    row = [normalize_cell(f, getattr(result, f)) for f in fields]
    return _make_csv_bytes(fields, [row])


def _format_line_items_only(item_model_class, extraction_result: dict) -> bytes:
    """Format a document type that only exposes its line_items list (no header fields).

    One CSV row is emitted per line item. If the document contains zero line
    items, a single data row is emitted with 'Not found' in all cells.
    """
    item_fields = list(item_model_class.model_fields.keys())
    raw_line_items = extraction_result.get("line_items") or []
    if not raw_line_items:
        rows = [[normalize_cell(f, None) for f in item_fields]]
    else:
        rows = [
            [normalize_cell(item_fields[i], item.get(item_fields[i]))
             for i in range(len(item_fields))]
            for item in raw_line_items
        ]
    return _make_csv_bytes(item_fields, rows)


# ---------------------------------------------------------------------------
# Public formatter functions
# ---------------------------------------------------------------------------


def format_purchase_order(extraction_result: dict) -> bytes:
    """Format a PurchaseOrder extraction result as CSV bytes."""
    return _format_line_item_type(PurchaseOrderResult, POLineItem, extraction_result)


def format_invoice(extraction_result: dict) -> bytes:
    """Format an Invoice extraction result as CSV bytes."""
    return _format_line_item_type(InvoiceResult, InvoiceLineItem, extraction_result)


def format_supplier_comparison(extraction_result: dict) -> bytes:
    """Format a SupplierComparison extraction result as CSV bytes."""
    return _format_line_item_type(SupplierComparisonResult, SupplierRow, extraction_result)


def format_tender_rfq(extraction_result: dict) -> bytes:
    """Format a TenderRFQ extraction result as CSV bytes -- 3 columns only."""
    return _format_line_items_only(TenderLineItem, extraction_result)


def format_quotation(extraction_result: dict) -> bytes:
    """Format a Quotation extraction result as CSV bytes -- 3 columns only."""
    return _format_line_items_only(QuotationLineItem, extraction_result)


# ---------------------------------------------------------------------------
# Formatter registry — keys MUST match SCHEMA_REGISTRY keys exactly
# ---------------------------------------------------------------------------

FORMATTER_REGISTRY: dict[str, Callable[[dict], bytes]] = {
    "purchase_order": format_purchase_order,
    "tender_rfq": format_tender_rfq,
    "quotation": format_quotation,
    "invoice": format_invoice,
    "supplier_comparison": format_supplier_comparison,
}
