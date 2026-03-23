import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional

JobStatus = Literal["pending", "processing", "classifying", "extracting", "complete", "error"]


@dataclass
class Job:
    job_id: str
    status: JobStatus = "pending"
    raw_text: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    doc_type: Optional[str] = None        # set after classification
    extraction_result: Optional[dict] = None  # set after extraction, stored as dict via .model_dump()
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class JobStore:
    def __init__(self):
        self._store: dict[str, Job] = {}
        self._lock = asyncio.Lock()

    async def create(self, job_id: str) -> Job:
        async with self._lock:
            job = Job(job_id=job_id)
            self._store[job_id] = job
            return job

    async def get(self, job_id: str) -> Optional[Job]:
        async with self._lock:
            return self._store.get(job_id)

    async def set_status(self, job_id: str, status: JobStatus) -> None:
        async with self._lock:
            if job_id in self._store:
                self._store[job_id].status = status
                self._store[job_id].updated_at = datetime.utcnow()

    async def set_raw_text(self, job_id: str, raw_text: str) -> None:
        async with self._lock:
            job = self._store.get(job_id)
            if job:
                job.raw_text = raw_text
                job.updated_at = datetime.utcnow()

    async def set_complete(self, job_id: str, raw_text: str) -> None:
        async with self._lock:
            job = self._store.get(job_id)
            if job:
                job.status = "complete"
                job.raw_text = raw_text
                job.updated_at = datetime.utcnow()

    async def set_error(self, job_id: str, error_code: str, error_message: str) -> None:
        async with self._lock:
            job = self._store.get(job_id)
            if job:
                job.status = "error"
                job.error_code = error_code
                job.error_message = error_message
                job.updated_at = datetime.utcnow()

    async def set_doc_type(self, job_id: str, doc_type: str) -> None:
        async with self._lock:
            job = self._store.get(job_id)
            if job:
                job.doc_type = doc_type
                job.updated_at = datetime.utcnow()

    async def set_extraction_result(self, job_id: str, result: dict) -> None:
        async with self._lock:
            job = self._store.get(job_id)
            if job:
                job.extraction_result = result
                job.status = "complete"
                job.updated_at = datetime.utcnow()


# Module-level singleton
job_store = JobStore()
