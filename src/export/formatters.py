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
from typing import Callable

from src.extraction.schemas.invoice import InvoiceLineItem, InvoiceResult
from src.extraction.schemas.purchase_order import POLineItem, PurchaseOrderResult
from src.extraction.schemas.quotation import QuotationLineItem, QuotationResult
from src.extraction.schemas.supplier_comparison import SupplierComparisonResult, SupplierRow
from src.extraction.schemas.tender_rfq import TenderLineItem, TenderRFQResult


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

    # Replace None with "" in every cell
    clean_rows = [
        [("" if v is None else v) for v in row]
        for row in raw_rows
    ]

    return _make_csv_bytes(columns, clean_rows)


def _format_header_only_type(model_class, extraction_result: dict) -> bytes:
    """Format a document type that has no line items (header fields only).

    Always produces exactly one data row.
    """
    result = model_class.model_validate(extraction_result)
    fields = list(model_class.model_fields.keys())
    row = [("" if getattr(result, f) is None else getattr(result, f)) for f in fields]
    return _make_csv_bytes(fields, [row])


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
    """Format a TenderRFQ extraction result as CSV bytes."""
    return _format_line_item_type(TenderRFQResult, TenderLineItem, extraction_result)


def format_quotation(extraction_result: dict) -> bytes:
    """Format a Quotation extraction result as CSV bytes."""
    return _format_line_item_type(QuotationResult, QuotationLineItem, extraction_result)


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
