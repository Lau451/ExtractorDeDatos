from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response
from src.core.job_store import job_store
from src.export.formatters import FORMATTER_REGISTRY

router = APIRouter()

EXPORTABLE_STATUSES = {"complete"}
EXPORTABLE_DOC_TYPES = set(FORMATTER_REGISTRY.keys())


@router.get("/jobs/{job_id}/export")
async def export_job(job_id: str):
    job = await job_store.get(job_id)

    if job is None:
        return JSONResponse(
            status_code=404,
            content={"error": "job_not_found", "message": f"No job with ID '{job_id}'"},
        )

    if job.status not in EXPORTABLE_STATUSES:
        return JSONResponse(
            status_code=409,
            content={
                "error": "job_not_exportable",
                "message": f"Job is not complete (status: {job.status})",
            },
        )

    if job.doc_type not in EXPORTABLE_DOC_TYPES:
        return JSONResponse(
            status_code=409,
            content={
                "error": "job_not_exportable",
                "message": f"Cannot export job with doc_type '{job.doc_type}'",
            },
        )

    formatter = FORMATTER_REGISTRY[job.doc_type]
    csv_bytes = formatter(job.extraction_result)
    filename = f"job_{job_id}_{job.doc_type}.csv"

    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
