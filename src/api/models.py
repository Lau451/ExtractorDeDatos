from typing import Optional

from pydantic import BaseModel


class ExtractResponse(BaseModel):
    job_id: str
    status: str  # always "pending" on POST /extract


class JobResultPayload(BaseModel):
    raw_text: str


class JobResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[JobResultPayload] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    message: str


class HealthResponse(BaseModel):
    status: str
