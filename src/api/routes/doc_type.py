from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse

from src.api.models import DocTypeOverrideRequest
from src.core.job_store import job_store
from src.extraction.schemas.registry import VALID_DOC_TYPES
from src.extraction.service import extract_with_type

router = APIRouter()


@router.patch("/jobs/{job_id}/doc_type")
async def patch_doc_type(
    job_id: str,
    body: DocTypeOverrideRequest,
    background_tasks: BackgroundTasks,
):
    """Override document type and trigger re-extraction.

    Behavior (from UI-SPEC):
    1. Validate doc_type is one of 5 known values (not "unknown"). Return 422 if invalid.
    2. Update doc_type in job store.
    3. Clear extraction_result (set to None).
    4. Set status to "extracting".
    5. Enqueue extract_with_type background task.
    6. Return 202 Accepted with updated job snapshot.
    """
    job = await job_store.get(job_id)
    if job is None:
        return JSONResponse(
            status_code=404,
            content={
                "error": "job_not_found",
                "message": f"No job with ID '{job_id}'",
            },
        )

    if body.doc_type not in VALID_DOC_TYPES:
        return JSONResponse(
            status_code=422,
            content={
                "error": "invalid_doc_type",
                "message": "Invalid document type. Must be one of: purchase_order, tender_rfq, quotation, invoice, supplier_comparison.",
            },
        )

    # Update job state
    await job_store.set_doc_type(job_id, body.doc_type)

    # Clear previous extraction result
    async with job_store._lock:
        job_obj = job_store._store.get(job_id)
        if job_obj:
            job_obj.extraction_result = None

    # Set status to extracting
    await job_store.set_status(job_id, "extracting")

    # Enqueue re-extraction as background task
    background_tasks.add_task(extract_with_type, job_id, body.doc_type)

    # Return 202 with snapshot
    return JSONResponse(
        status_code=202,
        content={
            "job_id": job_id,
            "status": "extracting",
            "doc_type": body.doc_type,
            "extraction_result": None,
        },
    )
