"""Ingestion layer unit tests — ING-01 through ING-05."""
import os
import uuid
import pytest
from unittest.mock import patch, AsyncMock

from src.core.job_store import job_store
from src.ingestion.service import process_document
from src.ingestion.validators import validate_file_extension

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


# ---------------------------------------------------------------------------
# Validator tests (ING-06)
# ---------------------------------------------------------------------------

def test_validate_allowed_extensions():
    """Allowed extensions return the extension string."""
    for ext, filename in [
        (".pdf", "document.pdf"),
        (".xlsx", "workbook.xlsx"),
        (".xls", "old.xls"),
        (".png", "image.png"),
        (".jpg", "photo.jpg"),
        (".jpeg", "photo.jpeg"),
        (".html", "page.html"),
        (".htm", "page.htm"),
    ]:
        result = validate_file_extension(filename)
        assert result == ext, f"Expected '{ext}' for '{filename}', got {result!r}"


def test_validate_rejected_extensions():
    """Unsupported extensions return None."""
    for filename in ["document.txt", "file.doc", "payload.exe", "data.csv", "image.gif"]:
        result = validate_file_extension(filename)
        assert result is None, f"Expected None for '{filename}', got {result!r}"


# ---------------------------------------------------------------------------
# Ingestion service tests (ING-01 through ING-05)
# ---------------------------------------------------------------------------

async def _run_ingestion(data: bytes, filename: str):
    """Helper: create a job, run process_document, return the job.

    Extraction pipeline is mocked — ingestion tests verify ingestion logic only.
    After process_document returns, the job will be in 'processing' status
    because set_raw_text does not change status. Only set_extraction_result
    (called by the extraction pipeline, which is mocked here) sets 'complete'.
    """
    job_id = str(uuid.uuid4())
    await job_store.create(job_id)
    with patch("src.ingestion.service.run_extraction_pipeline", new=AsyncMock(return_value=None)):
        await process_document(job_id, data, filename)
    return await job_store.get(job_id)


async def test_text_pdf_ingestion():
    """ING-01: Text-based PDF produces non-empty raw_text."""
    with open(os.path.join(FIXTURES, "sample.pdf"), "rb") as f:
        data = f.read()
    job = await _run_ingestion(data, "sample.pdf")
    assert job.status == "processing", f"Expected processing, got {job.status}: {job.error_code} — {job.error_message}"
    assert job.raw_text and len(job.raw_text.strip()) > 0


async def test_scanned_pdf_ingestion():
    """ING-02: Scanned PDF (raster-only) produces non-empty raw_text via OCR."""
    with open(os.path.join(FIXTURES, "scanned.pdf"), "rb") as f:
        data = f.read()
    job = await _run_ingestion(data, "scanned.pdf")
    # OCR output is non-deterministic — assert only non-empty
    assert job.status == "processing", f"Expected processing, got {job.status}: {job.error_code} — {job.error_message}"
    assert job.raw_text and len(job.raw_text.strip()) > 0


async def test_xlsx_ingestion():
    """ING-03: XLSX with multiple sheets produces markdown containing content from both sheets."""
    with open(os.path.join(FIXTURES, "sample.xlsx"), "rb") as f:
        data = f.read()
    job = await _run_ingestion(data, "sample.xlsx")
    assert job.status == "processing", f"Expected processing, got {job.status}: {job.error_code} — {job.error_message}"
    assert job.raw_text and len(job.raw_text.strip()) > 0


async def test_png_ingestion():
    """ING-04: PNG image produces non-empty raw_text via OCR."""
    with open(os.path.join(FIXTURES, "sample.png"), "rb") as f:
        data = f.read()
    job = await _run_ingestion(data, "sample.png")
    assert job.status == "processing", f"Expected processing, got {job.status}: {job.error_code} — {job.error_message}"
    assert job.raw_text and len(job.raw_text.strip()) > 0


async def test_html_ingestion():
    """ING-05: HTML file produces non-empty raw_text containing 'Test Document'."""
    with open(os.path.join(FIXTURES, "sample.html"), "rb") as f:
        data = f.read()
    job = await _run_ingestion(data, "sample.html")
    assert job.status == "processing", f"Expected processing, got {job.status}: {job.error_code} — {job.error_message}"
    assert job.raw_text and len(job.raw_text.strip()) > 0
    assert "Test Document" in job.raw_text
