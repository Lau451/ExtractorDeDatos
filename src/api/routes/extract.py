import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, UploadFile
from fastapi.responses import JSONResponse

from src.core.job_store import job_store
from src.ingestion.service import process_document
from src.ingestion.validators import validate_file_extension

router = APIRouter()


@router.post("/extract")
async def post_extract(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
):
    """Accept a file upload, validate extension, create a job, and process in background."""
    ext = validate_file_extension(file.filename)
    if ext is None:
        suffix = Path(file.filename).suffix.lower()
        return JSONResponse(
            status_code=400,
            content={
                "error": "unsupported_file_type",
                "message": f"File type '{suffix}' is not supported",
            },
        )

    # CRITICAL: read bytes inside the request context (FastAPI v0.106+ lifecycle)
    data: bytes = await file.read()
    filename: str = file.filename

    job_id = str(uuid.uuid4())
    await job_store.create(job_id)
    background_tasks.add_task(process_document, job_id, data, filename)

    return {"job_id": job_id, "status": "pending"}
