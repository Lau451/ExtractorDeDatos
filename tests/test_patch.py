"""Tests for PATCH /jobs/{id}/fields endpoint, deep merge, TTL cleanup, and error codes.

Covers requirements: API-03 (structured error codes) and REV-05 (PATCH corrections flow to CSV).
"""
import csv
import io
import uuid
from datetime import datetime, timedelta

import pytest

from src.core.errors import (
    DOCLING_PARSE_ERROR,
    DOCLING_TIMEOUT,
    FILE_TOO_LARGE,
    GEMINI_ERROR,
    INVALID_FILE_TYPE,
)
from src.core.job_store import Job, _deep_merge, job_store


# ---------------------------------------------------------------------------
# Unit tests: _deep_merge
# ---------------------------------------------------------------------------


def test_deep_merge_preserves_untouched_fields():
    result = _deep_merge({"a": "1", "b": "2"}, {"a": "X"})
    assert result == {"a": "X", "b": "2"}


def test_deep_merge_nested_dict():
    result = _deep_merge(
        {"header": {"buyer": "A", "date": "2024-01-01"}},
        {"header": {"buyer": "B"}},
    )
    assert result["header"] == {"buyer": "B", "date": "2024-01-01"}


def test_deep_merge_list_by_index():
    result = _deep_merge(
        {"items": [{"desc": "A", "qty": "1"}, {"desc": "B", "qty": "2"}]},
        {"items": [{"qty": "10"}]},
    )
    assert result["items"][0] == {"desc": "A", "qty": "10"}
    assert result["items"][1] == {"desc": "B", "qty": "2"}


# ---------------------------------------------------------------------------
# Unit tests: cleanup_expired_jobs
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_cleanup_removes_expired_jobs():
    job_id = str(uuid.uuid4())
    await job_store.create(job_id)

    # Manually set created_at to 2 hours ago to simulate expiry
    async with job_store._lock:
        job_store._store[job_id].created_at = datetime.utcnow() - timedelta(hours=2)

    removed = await job_store.cleanup_expired_jobs()
    assert removed == 1

    result = await job_store.get(job_id)
    assert result is None


# ---------------------------------------------------------------------------
# Unit tests: error code constants
# ---------------------------------------------------------------------------


def test_error_codes_defined():
    assert DOCLING_TIMEOUT == "DOCLING_TIMEOUT"
    assert DOCLING_PARSE_ERROR == "DOCLING_PARSE_ERROR"
    assert GEMINI_ERROR == "GEMINI_ERROR"
    assert INVALID_FILE_TYPE == "INVALID_FILE_TYPE"
    assert FILE_TOO_LARGE == "FILE_TOO_LARGE"


# ---------------------------------------------------------------------------
# Integration tests: PATCH /jobs/{id}/fields
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_patch_updates_field(client):
    job_id = str(uuid.uuid4())
    job = Job(
        job_id=job_id,
        status="complete",
        doc_type="purchase_order",
        extraction_result={"reference_number": "PO-001", "buyer": "Acme"},
    )
    async with job_store._lock:
        job_store._store[job_id] = job

    response = await client.patch(
        f"/api/jobs/{job_id}/fields",
        json={"fields": {"buyer": "NewCorp"}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["extraction_result"]["buyer"] == "NewCorp"
    assert body["extraction_result"]["reference_number"] == "PO-001"


@pytest.mark.anyio
async def test_patch_404(client):
    response = await client.patch(
        "/api/jobs/nonexistent-id/fields",
        json={"fields": {"x": "y"}},
    )
    assert response.status_code == 404
    assert response.json()["error"] == "job_not_found"


@pytest.mark.anyio
async def test_patch_409_not_complete(client):
    job_id = str(uuid.uuid4())
    job = Job(job_id=job_id, status="pending", doc_type=None)
    async with job_store._lock:
        job_store._store[job_id] = job

    response = await client.patch(
        f"/api/jobs/{job_id}/fields",
        json={"fields": {"x": "y"}},
    )
    assert response.status_code == 409
    assert response.json()["error"] == "job_not_patchable"


# ---------------------------------------------------------------------------
# End-to-end test: PATCH then export CSV reflects edits (REV-05)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Regression tests: PATCH on complete job with no extraction_result (UAT gap)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_patch_complete_but_no_extraction(client):
    """PATCH on a complete job with extraction_result=None must return 409."""
    job_id = str(uuid.uuid4())
    job = Job(
        job_id=job_id,
        status="complete",
        doc_type="purchase_order",
        extraction_result=None,
    )
    async with job_store._lock:
        job_store._store[job_id] = job

    response = await client.patch(
        f"/api/jobs/{job_id}/fields",
        json={"fields": {"buyer": "NewCorp"}},
    )
    assert response.status_code == 409
    assert response.json()["error"] == "extraction_result_missing"


@pytest.mark.anyio
async def test_patch_extraction_result_returns_none_when_no_extraction():
    """patch_extraction_result() must return None when extraction_result is None."""
    job_id = str(uuid.uuid4())
    job = Job(
        job_id=job_id,
        status="complete",
        doc_type="purchase_order",
        extraction_result=None,
    )
    async with job_store._lock:
        job_store._store[job_id] = job

    result = await job_store.patch_extraction_result(job_id, {"buyer": "X"})
    assert result is None


@pytest.mark.anyio
async def test_set_status_rejects_complete():
    """set_status() must raise ValueError when called with status='complete'."""
    job_id = str(uuid.uuid4())
    await job_store.create(job_id)

    with pytest.raises(ValueError, match="set_extraction_result"):
        await job_store.set_status(job_id, "complete")


# ---------------------------------------------------------------------------
# End-to-end test: PATCH then export CSV reflects edits (REV-05)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_patch_then_export_reflects_edits(client):
    """After PATCH, GET /jobs/{id}/export CSV must contain the corrected value."""
    job_id = str(uuid.uuid4())
    extraction_result = {
        "po_number": "PO-001",
        "issue_date": "2024-01-01",
        "buyer_name": "Acme",
        "supplier_name": "SupplierX",
        "delivery_date": "2024-02-01",
        "currency": "USD",
        "total_amount": "1000",
        "payment_terms": "Net 30",
        "shipping_address": None,
        "notes": None,
        "line_items": [],
    }
    job = Job(
        job_id=job_id,
        status="complete",
        doc_type="purchase_order",
        extraction_result=extraction_result,
    )
    async with job_store._lock:
        job_store._store[job_id] = job

    # Apply PATCH to update buyer_name
    patch_response = await client.patch(
        f"/api/jobs/{job_id}/fields",
        json={"fields": {"buyer_name": "NewCorp"}},
    )
    assert patch_response.status_code == 200

    # Export and verify CSV
    export_response = await client.get(f"/api/jobs/{job_id}/export")
    assert export_response.status_code == 200

    csv_text = export_response.content.decode("utf-8-sig")
    assert "NewCorp" in csv_text, "Patched buyer_name should appear in CSV"
    assert "Acme" not in csv_text, "Original buyer_name should not appear in CSV"
