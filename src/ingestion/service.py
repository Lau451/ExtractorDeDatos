import asyncio
import logging
from io import BytesIO

from docling.datamodel.base_models import DocumentStream

from src.core.config import settings
from src.core.job_store import job_store
from src.extraction.service import run_extraction_pipeline
from src.ingestion.docling_adapter import build_converter

logger = logging.getLogger(__name__)


async def process_document(job_id: str, data: bytes, filename: str) -> None:
    """Async entry point: sets job to processing, runs Docling in a thread, stores result."""
    await job_store.set_status(job_id, "processing")
    try:
        source = DocumentStream(name=filename, stream=BytesIO(data))
        result = await asyncio.wait_for(
            asyncio.to_thread(_sync_convert, source, filename),
            timeout=settings.docling_timeout_seconds,
        )
        markdown = result.document.export_to_markdown()
        if not markdown.strip():
            await job_store.set_error(
                job_id,
                "docling_parse_error",
                "Document produced no extractable text",
            )
            return
        await job_store.set_complete(job_id, raw_text=markdown)
        await run_extraction_pipeline(job_id)
    except asyncio.TimeoutError:
        await job_store.set_error(
            job_id,
            "docling_timeout",
            "Document processing exceeded 60s timeout",
        )
    except Exception as exc:
        logger.exception("Docling conversion failed for job %s (file: %s)", job_id, filename)
        detail = str(exc.__cause__) if exc.__cause__ else str(exc)
        await job_store.set_error(job_id, "docling_parse_error", detail)


def _sync_convert(source: DocumentStream, filename: str):
    """Synchronous Docling conversion — called via asyncio.to_thread.

    MUST NOT call any async functions or acquire asyncio.Lock.
    """
    return build_converter(filename).convert(source)
