import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.xfail(reason="Implementation not yet created")
async def test_override_triggers_reextraction(client):
    """CLS-03: PATCH /jobs/{id}/doc_type triggers re-extraction with new schema.

    Flow:
    1. Create a job with doc_type="purchase_order" and an extraction_result
    2. PATCH /jobs/{id}/doc_type with {"doc_type": "invoice"}
    3. Assert response status is 202
    4. Assert job status becomes "extracting"
    5. Assert extraction_result was cleared (null)
    6. Assert re-extraction runs with InvoiceResult schema
    """
    from src.core.job_store import job_store

    # Step 1: Create a job and simulate it having completed PO extraction
    upload_response = await client.post(
        "/jobs",
        files={"file": ("test.pdf", b"%PDF-1.4 fake content", "application/pdf")},
    )
    assert upload_response.status_code == 202
    job_id = upload_response.json()["job_id"]

    # Simulate extraction having completed for purchase_order
    await job_store.set_doc_type(job_id, "purchase_order")
    await job_store.set_extraction_result(
        job_id,
        {
            "po_number": "PO-2024-0847",
            "buyer_name": "Acme Manufacturing Ltd.",
            "line_items": [],
        },
    )

    # Step 2: Override doc_type to invoice — should trigger re-extraction
    with patch(
        "src.extraction.service.run_extraction_pipeline", new_callable=AsyncMock
    ) as mock_pipeline:
        response = await client.patch(
            f"/jobs/{job_id}/doc_type",
            json={"doc_type": "invoice"},
        )

        # Step 3: Response must be 202 Accepted
        assert response.status_code == 202

        # Step 4: Job status must transition to extracting/processing
        job_response = await client.get(f"/jobs/{job_id}")
        body = job_response.json()
        assert body["status"] in ("extracting", "processing")

        # Step 5: extraction_result must be cleared
        assert body.get("extraction_result") is None or body.get("extraction_result") == {}

        # Step 6: Re-extraction pipeline must have been called with job_id
        mock_pipeline.assert_called_once_with(job_id)


@pytest.mark.xfail(reason="Implementation not yet created")
async def test_override_invalid_doc_type_returns_422(client):
    """CLS-03: PATCH with invalid doc_type returns 422."""
    from src.core.job_store import job_store

    # Create a job
    upload_response = await client.post(
        "/jobs",
        files={"file": ("test.pdf", b"%PDF-1.4 fake content", "application/pdf")},
    )
    assert upload_response.status_code == 202
    job_id = upload_response.json()["job_id"]
    await job_store.set_doc_type(job_id, "purchase_order")

    # Send an invalid doc_type string — must return 422 Unprocessable Entity
    response = await client.patch(
        f"/jobs/{job_id}/doc_type",
        json={"doc_type": "not_a_valid_type"},
    )
    assert response.status_code == 422


@pytest.mark.xfail(reason="Implementation not yet created")
async def test_override_unknown_not_allowed(client):
    """CLS-03: PATCH with doc_type='unknown' returns 422."""
    from src.core.job_store import job_store

    # Create a job
    upload_response = await client.post(
        "/jobs",
        files={"file": ("test.pdf", b"%PDF-1.4 fake content", "application/pdf")},
    )
    assert upload_response.status_code == 202
    job_id = upload_response.json()["job_id"]
    await job_store.set_doc_type(job_id, "purchase_order")

    # 'unknown' is a valid internal classification result but must NOT be accepted
    # via the override endpoint — users must choose a real document type
    response = await client.patch(
        f"/jobs/{job_id}/doc_type",
        json={"doc_type": "unknown"},
    )
    assert response.status_code == 422
