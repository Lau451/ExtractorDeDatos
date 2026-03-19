from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.core.job_store import job_store

router = APIRouter()


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """Return the current status and result for a job."""
    job = await job_store.get(job_id)
    if job is None:
        return JSONResponse(
            status_code=404,
            content={
                "error": "job_not_found",
                "message": f"No job with ID '{job_id}'",
            },
        )

    if job.status == "complete":
        return {
            "job_id": job.job_id,
            "status": "complete",
            "result": {"raw_text": job.raw_text},
        }

    if job.status == "error":
        return JSONResponse(
            status_code=200,
            content={
                "job_id": job.job_id,
                "status": "error",
                "error_code": job.error_code,
                "error_message": job.error_message,
            },
        )

    # pending or processing
    return {"job_id": job.job_id, "status": job.status}
