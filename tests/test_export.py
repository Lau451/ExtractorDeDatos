"""Unit tests for the CSV export formatters (src/export/formatters.py).

Tests cover: BOM, column order, None-to-empty-cell, line-item expansion,
header-only single-row, and FORMATTER_REGISTRY completeness.
"""
import csv
import io

import pytest

from src.export.formatters import (
    FORMATTER_REGISTRY,
    format_invoice,
    format_purchase_order,
    format_quotation,
    format_supplier_comparison,
    format_tender_rfq,
)

# ---------------------------------------------------------------------------
# Sample extraction-result dicts (one per doc type)
# ---------------------------------------------------------------------------

SAMPLE_PO = {
    "po_number": "PO-001",
    "issue_date": "2024-01-15",
    "buyer_name": "Acme Corp",
    "supplier_name": "Widget Inc",
    "delivery_date": "2024-02-01",
    "currency": "USD",
    "total_amount": "1500.00",
    "payment_terms": "Net 30",
    "shipping_address": "123 Main St",
    "notes": None,
    "line_items": [
        {
            "item_number": "1",
            "description": "Widget A",
            "sku": "WA-100",
            "quantity": "10",
            "unit": "each",
            "unit_price": "50.00",
            "extended_price": "500.00",
        },
        {
            "item_number": "2",
            "description": "Widget B",
            "sku": "WB-200",
            "quantity": "20",
            "unit": "each",
            "unit_price": "50.00",
            "extended_price": "1000.00",
        },
    ],
}

SAMPLE_INVOICE = {
    "invoice_number": "INV-001",
    "invoice_date": "2024-01-20",
    "due_date": "2024-02-20",
    "issuer_name": "Widget Inc",
    "issuer_address": "456 Oak Ave",
    "recipient_name": "Acme Corp",
    "recipient_address": "123 Main St",
    "currency": "USD",
    "subtotal": "1500.00",
    "tax_total": "150.00",
    "total_amount": "1650.00",
    "payment_terms": "Net 30",
    "po_reference": "PO-001",
    "line_items": [
        {
            "item_number": "1",
            "description": "Consulting",
            "quantity": "10",
            "unit": "hours",
            "unit_price": "150.00",
            "extended_price": "1500.00",
        }
    ],
}

SAMPLE_SUPPLIER = {
    "project_name": "Office Supplies",
    "comparison_date": "2024-01-10",
    "rfq_reference": "RFQ-001",
    "evaluation_criteria": "price, quality",
    "recommended_supplier": "Vendor A",
    "notes": None,
    "line_items": [
        {
            "supplier_name": "Vendor A",
            "item_description": "Paper",
            "unit_price": "5.00",
            "total_price": "500.00",
            "lead_time": "7 days",
            "payment_terms": "Net 30",
            "delivery_terms": "FOB",
            "warranty": "N/A",
            "compliance_notes": None,
            "overall_score": "95",
        }
    ],
}

SAMPLE_TENDER = {
    "tender_reference": "TND-001",
    "issue_date": "2024-01-05",
    "issuing_organization": "Gov Agency",
    "submission_deadline": "2024-02-05",
    "contact_person": "John Doe",
    "project_title": "Road Repair",
    "currency": "USD",
    "notes": "Urgent",
}

SAMPLE_QUOTATION = {
    "quote_number": "QT-001",
    "quote_date": "2024-01-12",
    "vendor_name": "Supplier X",
    "vendor_address": "789 Pine Rd",
    "buyer_name": "Acme Corp",
    "valid_until": "2024-02-12",
    "currency": "EUR",
    "subtotal": "1000.00",
    "tax_total": "100.00",
    "grand_total": "1100.00",
    "payment_terms": "Net 60",
    "delivery_terms": "CIF",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_csv(csv_bytes: bytes) -> list[list[str]]:
    """Decode UTF-8 (stripping BOM), return list of rows as string lists."""
    text = csv_bytes.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))
    return list(reader)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_csv_has_bom():
    result = format_purchase_order(SAMPLE_PO)
    assert result[:3] == b"\xef\xbb\xbf", "CSV output must start with UTF-8 BOM"


def test_column_order_purchase_order():
    result = format_purchase_order(SAMPLE_PO)
    rows = _parse_csv(result)
    expected = [
        "po_number",
        "issue_date",
        "buyer_name",
        "supplier_name",
        "delivery_date",
        "currency",
        "total_amount",
        "payment_terms",
        "shipping_address",
        "notes",
        "item_number",
        "description",
        "sku",
        "quantity",
        "unit",
        "unit_price",
        "extended_price",
    ]
    assert rows[0] == expected, f"Column order mismatch: {rows[0]}"
    assert len(rows[0]) == 17


def test_column_order_invoice():
    result = format_invoice(SAMPLE_INVOICE)
    rows = _parse_csv(result)
    expected = [
        "invoice_number",
        "invoice_date",
        "due_date",
        "issuer_name",
        "issuer_address",
        "recipient_name",
        "recipient_address",
        "currency",
        "subtotal",
        "tax_total",
        "total_amount",
        "payment_terms",
        "po_reference",
        "item_number",
        "description",
        "quantity",
        "unit",
        "unit_price",
        "extended_price",
    ]
    assert rows[0] == expected, f"Column order mismatch: {rows[0]}"
    assert len(rows[0]) == 19


def test_column_order_supplier_comparison():
    result = format_supplier_comparison(SAMPLE_SUPPLIER)
    rows = _parse_csv(result)
    expected = [
        "project_name",
        "comparison_date",
        "rfq_reference",
        "evaluation_criteria",
        "recommended_supplier",
        "notes",
        "supplier_name",
        "item_description",
        "unit_price",
        "total_price",
        "lead_time",
        "payment_terms",
        "delivery_terms",
        "warranty",
        "compliance_notes",
        "overall_score",
    ]
    assert rows[0] == expected, f"Column order mismatch: {rows[0]}"
    assert len(rows[0]) == 16


def test_column_order_tender_rfq():
    result = format_tender_rfq(SAMPLE_TENDER)
    rows = _parse_csv(result)
    expected = [
        "tender_reference",
        "issue_date",
        "issuing_organization",
        "submission_deadline",
        "contact_person",
        "project_title",
        "currency",
        "notes",
    ]
    assert rows[0] == expected, f"Column order mismatch: {rows[0]}"
    assert len(rows[0]) == 8


def test_column_order_quotation():
    result = format_quotation(SAMPLE_QUOTATION)
    rows = _parse_csv(result)
    expected = [
        "quote_number",
        "quote_date",
        "vendor_name",
        "vendor_address",
        "buyer_name",
        "valid_until",
        "currency",
        "subtotal",
        "tax_total",
        "grand_total",
        "payment_terms",
        "delivery_terms",
    ]
    assert rows[0] == expected, f"Column order mismatch: {rows[0]}"
    assert len(rows[0]) == 12


def test_distinct_schemas():
    """All five formatters must produce different column counts."""
    counts = {
        "purchase_order": len(_parse_csv(format_purchase_order(SAMPLE_PO))[0]),
        "invoice": len(_parse_csv(format_invoice(SAMPLE_INVOICE))[0]),
        "supplier_comparison": len(_parse_csv(format_supplier_comparison(SAMPLE_SUPPLIER))[0]),
        "tender_rfq": len(_parse_csv(format_tender_rfq(SAMPLE_TENDER))[0]),
        "quotation": len(_parse_csv(format_quotation(SAMPLE_QUOTATION))[0]),
    }
    assert counts["purchase_order"] == 17
    assert counts["invoice"] == 19
    assert counts["supplier_comparison"] == 16
    assert counts["tender_rfq"] == 8
    assert counts["quotation"] == 12
    assert len(set(counts.values())) == 5, "All five doc types must have distinct column counts"


def test_none_values_are_empty_cells():
    """None fields in extraction_result must render as '' not 'None'."""
    result = format_purchase_order(SAMPLE_PO)
    rows = _parse_csv(result)
    # SAMPLE_PO has notes=None; notes is column index 9 (0-based)
    notes_col_idx = rows[0].index("notes")
    for data_row in rows[1:]:
        assert data_row[notes_col_idx] != "None", (
            f"notes column should be empty string, got 'None' in row: {data_row}"
        )


def test_line_item_rows_repeat_headers():
    """PO with 2 line items must produce 3 rows (header + 2 data) with header fields repeated."""
    result = format_purchase_order(SAMPLE_PO)
    rows = _parse_csv(result)
    assert len(rows) == 3, f"Expected 3 rows (1 header + 2 data), got {len(rows)}"
    # Verify header fields are repeated in each data row
    header = rows[0]
    po_number_idx = header.index("po_number")
    for data_row in rows[1:]:
        assert data_row[po_number_idx] == "PO-001", (
            f"Header field po_number should be repeated, got: {data_row[po_number_idx]}"
        )


def test_zero_line_items_single_row():
    """PO with empty line_items must produce 2 rows (header + 1 data with empty line-item cells)."""
    po_no_items = {**SAMPLE_PO, "line_items": []}
    result = format_purchase_order(po_no_items)
    rows = _parse_csv(result)
    assert len(rows) == 2, f"Expected 2 rows (header + 1 data), got {len(rows)}"
    # Line-item columns should be empty
    header = rows[0]
    item_number_idx = header.index("item_number")
    assert rows[1][item_number_idx] == "", (
        f"item_number should be empty for zero-line-item doc, got: {rows[1][item_number_idx]}"
    )


def test_header_only_single_row():
    """TenderRFQ (no line items) must always produce exactly 2 rows (header + 1 data)."""
    result = format_tender_rfq(SAMPLE_TENDER)
    rows = _parse_csv(result)
    assert len(rows) == 2, f"Expected 2 rows (header + 1 data), got {len(rows)}"


def test_formatter_registry_has_all_types():
    """FORMATTER_REGISTRY must have exactly 5 keys matching SCHEMA_REGISTRY keys."""
    from src.extraction.schemas.registry import SCHEMA_REGISTRY

    assert set(FORMATTER_REGISTRY.keys()) == set(SCHEMA_REGISTRY.keys()), (
        f"FORMATTER_REGISTRY keys {set(FORMATTER_REGISTRY.keys())} != "
        f"SCHEMA_REGISTRY keys {set(SCHEMA_REGISTRY.keys())}"
    )
    assert len(FORMATTER_REGISTRY) == 5
