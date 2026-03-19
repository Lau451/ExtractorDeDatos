import asyncio
from io import BytesIO

from docling.datamodel.base_models import DocumentStream

from src.core.config import settings
from src.core.job_store import job_store
from src.ingestion.docling_adapter import build_converter


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
    except asyncio.TimeoutError:
        await job_store.set_error(
            job_id,
            "docling_timeout",
            "Document processing exceeded 60s timeout",
        )
    except Exception as exc:
        await job_store.set_error(job_id, "docling_parse_error", str(exc))


def _sync_convert(source: DocumentStream, filename: str):
    """Synchronous Docling conversion — called via asyncio.to_thread.

    MUST NOT call any async functions or acquire asyncio.Lock.
    """
    return build_converter(filename).convert(source)
