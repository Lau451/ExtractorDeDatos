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
    normalize_cell,
    check_mandatory_fields,
    MANDATORY_FIELDS,
    _is_amount_field,
    _is_date_field,
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
    "line_items": [
        {
            "item_number": "1",
            "quantity": "100",
            "description": "Asphalt mix",
        }
    ],
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
    "line_items": [
        {
            "item_number": "1",
            "quantity": "50",
            "description": "Office chairs",
        }
    ],
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
        "tender_reference", "issue_date", "issuing_organization",
        "submission_deadline", "contact_person", "project_title",
        "currency", "notes",
        "item_number", "quantity", "description",
    ]
    assert rows[0] == expected, f"Column order mismatch: {rows[0]}"
    assert len(rows[0]) == 11


def test_column_order_quotation():
    result = format_quotation(SAMPLE_QUOTATION)
    rows = _parse_csv(result)
    expected = [
        "quote_number", "quote_date", "vendor_name", "vendor_address",
        "buyer_name", "valid_until", "currency", "subtotal", "tax_total",
        "grand_total", "payment_terms", "delivery_terms",
        "item_number", "quantity", "description",
    ]
    assert rows[0] == expected, f"Column order mismatch: {rows[0]}"
    assert len(rows[0]) == 15


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
    assert counts["tender_rfq"] == 11
    assert counts["quotation"] == 15
    assert len(set(counts.values())) == 5, "All five doc types must have distinct column counts"


def test_none_values_are_not_found():
    """None fields in extraction_result must render as 'Not found'."""
    result = format_purchase_order(SAMPLE_PO)
    rows = _parse_csv(result)
    notes_col_idx = rows[0].index("notes")
    for data_row in rows[1:]:
        assert data_row[notes_col_idx] == "Not found", (
            f"notes column should be 'Not found', got '{data_row[notes_col_idx]}'"
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
    assert rows[1][item_number_idx] == "Not found", (
        f"item_number should be 'Not found' for zero-line-item doc, got: {rows[1][item_number_idx]}"
    )


def test_zero_line_items_produces_single_row_tender():
    """TenderRFQ with zero line items must produce exactly 2 rows (header + 1 data)."""
    tender_no_items = {**SAMPLE_TENDER, "line_items": []}
    result = format_tender_rfq(tender_no_items)
    rows = _parse_csv(result)
    assert len(rows) == 2, f"Expected 2 rows (header + 1 data), got {len(rows)}"


def test_tender_line_item_rows():
    """Tender with 1 line item must produce 2 rows (header + 1 data) with header repeated."""
    result = format_tender_rfq(SAMPLE_TENDER)
    rows = _parse_csv(result)
    assert len(rows) == 2, f"Expected 2 rows, got {len(rows)}"
    ref_idx = rows[0].index("tender_reference")
    assert rows[1][ref_idx] == "TND-001"


def test_quotation_line_item_rows():
    """Quotation with 1 line item must produce 2 rows (header + 1 data) with header repeated."""
    result = format_quotation(SAMPLE_QUOTATION)
    rows = _parse_csv(result)
    assert len(rows) == 2, f"Expected 2 rows, got {len(rows)}"
    num_idx = rows[0].index("quote_number")
    assert rows[1][num_idx] == "QT-001"


def test_formatter_registry_has_all_types():
    """FORMATTER_REGISTRY must have exactly 5 keys matching SCHEMA_REGISTRY keys."""
    from src.extraction.schemas.registry import SCHEMA_REGISTRY

    assert set(FORMATTER_REGISTRY.keys()) == set(SCHEMA_REGISTRY.keys()), (
        f"FORMATTER_REGISTRY keys {set(FORMATTER_REGISTRY.keys())} != "
        f"SCHEMA_REGISTRY keys {set(SCHEMA_REGISTRY.keys())}"
    )
    assert len(FORMATTER_REGISTRY) == 5


# ---------------------------------------------------------------------------
# Unit tests for normalize_cell
# ---------------------------------------------------------------------------


def test_normalize_cell_none_returns_not_found():
    assert normalize_cell("any_field", None) == "Not found"


def test_normalize_cell_empty_string_returns_not_found():
    assert normalize_cell("any_field", "") == "Not found"
    assert normalize_cell("any_field", "   ") == "Not found"


def test_normalize_amount_fields():
    assert normalize_cell("total_amount", "$1,234.50") == "1234.50"
    assert normalize_cell("unit_price", "EUR 50.00") == "50.00"
    assert normalize_cell("extended_price", "1500") == "1500"
    assert normalize_cell("subtotal", "100.00") == "100.00"
    assert normalize_cell("tax_total", "150.00") == "150.00"


def test_normalize_amount_fallback():
    assert normalize_cell("total_amount", "N/A") == "N/A"
    assert normalize_cell("unit_price", "TBD") == "TBD"


def test_normalize_date_fields():
    assert normalize_cell("issue_date", "2024-01-15") == "15/01/2024"
    assert normalize_cell("quote_date", "January 15, 2024") == "15/01/2024"
    assert normalize_cell("invoice_date", "15/01/2024") == "15/01/2024"
    assert normalize_cell("due_date", "2024/01/15") == "15/01/2024"


def test_normalize_date_fallback():
    assert normalize_cell("issue_date", "unparseable") == "unparseable"


def test_normalize_text_whitespace():
    assert normalize_cell("buyer_name", "  Acme  Corp  ") == "Acme Corp"
    assert normalize_cell("notes", "hello   world") == "hello world"


def test_submission_deadline_not_date_normalized():
    """submission_deadline does not match date pattern — text normalization only."""
    assert normalize_cell("submission_deadline", "2024-02-05") == "2024-02-05"


def test_valid_until_not_date_normalized():
    """valid_until does not match date pattern — text normalization only."""
    assert normalize_cell("valid_until", "2024-02-12") == "2024-02-12"


def test_is_amount_field():
    assert _is_amount_field("total_amount") is True
    assert _is_amount_field("unit_price") is True
    assert _is_amount_field("extended_price") is True
    assert _is_amount_field("subtotal") is True
    assert _is_amount_field("tax_total") is True
    assert _is_amount_field("po_number") is False
    assert _is_amount_field("buyer_name") is False


def test_is_date_field():
    assert _is_date_field("issue_date") is True
    assert _is_date_field("quote_date") is True
    assert _is_date_field("invoice_date") is True
    assert _is_date_field("due_date") is True
    assert _is_date_field("submission_deadline") is False
    assert _is_date_field("valid_until") is False


def test_check_mandatory_fields_missing():
    data = {"po_number": None, "issue_date": "2024-01-15", "buyer_name": "Acme", "supplier_name": "Widget"}
    result = check_mandatory_fields("purchase_order", data)
    assert result == ["po_number"]


def test_check_mandatory_fields_all_present():
    data = {"po_number": "PO-001", "issue_date": "2024-01-15", "buyer_name": "Acme", "supplier_name": "Widget"}
    result = check_mandatory_fields("purchase_order", data)
    assert result == []


def test_check_mandatory_fields_empty_string():
    data = {"po_number": "  ", "issue_date": "2024-01-15", "buyer_name": "Acme", "supplier_name": "Widget"}
    result = check_mandatory_fields("purchase_order", data)
    assert result == ["po_number"]


def test_formatter_normalization_applied():
    """PO formatter must apply normalization — amount fields stripped, None becomes 'Not found'."""
    po = {**SAMPLE_PO, "total_amount": "$1,500.00", "notes": None}
    result = format_purchase_order(po)
    rows = _parse_csv(result)
    header = rows[0]
    total_idx = header.index("total_amount")
    notes_idx = header.index("notes")
    assert rows[1][total_idx] == "1500.00"
    assert rows[1][notes_idx] == "Not found"


# ---------------------------------------------------------------------------
# Integration tests for GET /jobs/{id}/export endpoint
# ---------------------------------------------------------------------------

import pytest
from src.core.job_store import Job, job_store


@pytest.mark.anyio
async def test_export_complete_job(client):
    job_id = "test-export-po-001"
    job = Job(job_id=job_id, status="complete", doc_type="purchase_order", extraction_result=SAMPLE_PO)
    async with job_store._lock:
        job_store._store[job_id] = job

    response = await client.get(f"/api/jobs/{job_id}/export")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]
    assert f"job_{job_id}_purchase_order.csv" in response.headers["content-disposition"]
    assert response.content.startswith(b"\xef\xbb\xbf")


@pytest.mark.anyio
async def test_export_404(client):
    response = await client.get("/api/jobs/nonexistent-id/export")

    assert response.status_code == 404
    assert response.json()["error"] == "job_not_found"


@pytest.mark.anyio
async def test_export_409_not_complete(client):
    job_id = "test-export-409-processing"
    job = Job(job_id=job_id, status="processing", doc_type="purchase_order")
    async with job_store._lock:
        job_store._store[job_id] = job

    response = await client.get(f"/api/jobs/{job_id}/export")

    assert response.status_code == 409
    assert response.json()["error"] == "job_not_exportable"
    assert "not complete" in response.json()["message"]


@pytest.mark.anyio
async def test_export_409_unknown_doc_type(client):
    job_id = "test-export-409-unknown"
    job = Job(job_id=job_id, status="complete", doc_type="unknown", extraction_result=None)
    async with job_store._lock:
        job_store._store[job_id] = job

    response = await client.get(f"/api/jobs/{job_id}/export")

    assert response.status_code == 409
    assert response.json()["error"] == "job_not_exportable"
    assert "unknown" in response.json()["message"]


@pytest.mark.anyio
async def test_export_content_type(client):
    job_id = "test-export-ct-tender"
    job = Job(job_id=job_id, status="complete", doc_type="tender_rfq", extraction_result=SAMPLE_TENDER)
    async with job_store._lock:
        job_store._store[job_id] = job

    response = await client.get(f"/api/jobs/{job_id}/export")

    assert response.headers["content-type"] == "text/csv; charset=utf-8"


@pytest.mark.anyio
async def test_export_filename(client):
    job_id = "test-export-fn-invoice"
    job = Job(job_id=job_id, status="complete", doc_type="invoice", extraction_result=SAMPLE_INVOICE)
    async with job_store._lock:
        job_store._store[job_id] = job

    response = await client.get(f"/api/jobs/{job_id}/export")

    assert f'filename="job_{job_id}_invoice.csv"' in response.headers["content-disposition"]
