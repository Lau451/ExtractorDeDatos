from fastapi import APIRouter
from fastapi.responses import JSONResponse
from typing import Any, Optional

from src.core.job_store import job_store

router = APIRouter()


def _serialize_extraction(result: Optional[dict]) -> Optional[dict]:
    """Replace None values with 'Not found' for API response. Satisfies REV-03."""
    if result is None:
        return None

    def _replace(v: Any) -> Any:
        if v is None:
            return "Not found"
        if isinstance(v, list):
            return [
                {k: _replace(vv) for k, vv in item.items()} if isinstance(item, dict) else _replace(item)
                for item in v
            ]
        if isinstance(v, dict):
            return {k: _replace(vv) for k, vv in v.items()}
        return v

    return {k: _replace(v) for k, v in result.items()}


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

    response = {
        "job_id": job.job_id,
        "status": job.status,
        "doc_type": job.doc_type,
    }

    if job.status == "complete":
        response["extraction_result"] = _serialize_extraction(job.extraction_result)

    if job.status == "error":
        response["error_code"] = job.error_code
        response["error_message"] = job.error_message

    return response
