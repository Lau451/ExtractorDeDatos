import asyncio
import copy
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Literal, Optional

JobStatus = Literal["pending", "processing", "classifying", "extracting", "complete", "error"]

JOB_TTL = timedelta(hours=1)


def _deep_merge(base: dict, patch: dict) -> dict:
    """Return base with patch applied recursively. Does not mutate either argument."""
    result = copy.deepcopy(base)
    for key, patch_val in patch.items():
        base_val = result.get(key)
        if isinstance(base_val, dict) and isinstance(patch_val, dict):
            result[key] = _deep_merge(base_val, patch_val)
        elif isinstance(base_val, list) and isinstance(patch_val, list):
            merged_list = list(base_val)
            for i, patch_item in enumerate(patch_val):
                if i < len(merged_list) and isinstance(merged_list[i], dict) and isinstance(patch_item, dict):
                    merged_list[i] = _deep_merge(merged_list[i], patch_item)
                elif i < len(merged_list):
                    merged_list[i] = patch_item
                else:
                    merged_list.append(patch_item)
            result[key] = merged_list
        else:
            result[key] = patch_val
    return result


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
        if status == "complete":
            raise ValueError(
                "Cannot set status to 'complete' directly; use set_extraction_result()"
            )
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

    async def patch_extraction_result(self, job_id: str, patch: dict) -> Optional["Job"]:
        """Deep-merge patch into extraction_result. Returns updated Job or None if not found."""
        async with self._lock:
            job = self._store.get(job_id)
            if job is None:
                return None
            if job.extraction_result is None:
                return None
            current = job.extraction_result
            job.extraction_result = _deep_merge(current, patch)
            job.updated_at = datetime.utcnow()
            return job

    async def cleanup_expired_jobs(self) -> int:
        """Remove jobs older than JOB_TTL. Returns count of removed jobs."""
        cutoff = datetime.utcnow() - JOB_TTL
        async with self._lock:
            expired = [jid for jid, job in self._store.items() if job.created_at < cutoff]
            for jid in expired:
                del self._store[jid]
            return len(expired)


# Module-level singleton
job_store = JobStore()
