import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.api.models import PatchFieldsRequest
from src.api.routes.jobs import _serialize_extraction
from src.core.job_store import job_store

logger = logging.getLogger(__name__)

router = APIRouter()


@router.patch("/jobs/{job_id}/fields")
async def patch_job_fields(job_id: str, body: PatchFieldsRequest):
    """Apply user corrections to a completed job's extraction result via deep merge."""
    job = await job_store.get(job_id)

    if job is None:
        return JSONResponse(
            status_code=404,
            content={"error": "job_not_found", "message": f"No job with ID '{job_id}'"},
        )

    if job.status != "complete":
        return JSONResponse(
            status_code=409,
            content={
                "error": "job_not_patchable",
                "message": f"Job is not complete (status: {job.status})",
            },
        )

    if job.extraction_result is None:
        return JSONResponse(
            status_code=409,
            content={
                "error": "extraction_result_missing",
                "message": "Job is complete but has no extraction result to patch",
            },
        )

    updated_job = await job_store.patch_extraction_result(job_id, body.fields)
    if updated_job is None:
        # Job was removed between get() and patch() — unlikely but safe
        return JSONResponse(
            status_code=404,
            content={"error": "job_not_found", "message": f"No job with ID '{job_id}'"},
        )

    return {
        "job_id": updated_job.job_id,
        "status": updated_job.status,
        "doc_type": updated_job.doc_type,
        "extraction_result": _serialize_extraction(updated_job.extraction_result),
        "error_code": updated_job.error_code,
        "error_message": updated_job.error_message,
    }
