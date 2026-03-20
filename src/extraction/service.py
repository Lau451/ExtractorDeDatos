import asyncio
import logging
from src.core.config import settings
from src.core.job_store import job_store
from src.llm.registry import get_provider
from src.extraction.schemas.registry import SCHEMA_REGISTRY

logger = logging.getLogger(__name__)

RETRY_BACKOFF = 2.0  # seconds between retry attempts


async def _call_with_retry(coro_factory, timeout: float) -> object:
    """Call coro_factory() with timeout. On failure, wait RETRY_BACKOFF seconds and retry once."""
    for attempt in range(2):
        try:
            return await asyncio.wait_for(coro_factory(), timeout=timeout)
        except asyncio.TimeoutError:
            if attempt == 0:
                logger.warning("LLM call timed out (attempt 1/2), retrying after %.1fs backoff", RETRY_BACKOFF)
                await asyncio.sleep(RETRY_BACKOFF)
                continue
            raise
        except Exception:
            if attempt == 0:
                logger.warning("LLM call failed (attempt 1/2), retrying after %.1fs backoff", RETRY_BACKOFF)
                await asyncio.sleep(RETRY_BACKOFF)
                continue
            raise


async def run_extraction_pipeline(job_id: str) -> None:
    """Full pipeline: classify document type, then extract fields using type-specific schema.

    Called after ingestion completes (chained in ingestion service) or after doc_type override.
    """
    job = await job_store.get(job_id)
    if job is None:
        logger.error("run_extraction_pipeline called with unknown job_id: %s", job_id)
        return

    provider = get_provider()

    # Step 1: Classify
    await job_store.set_status(job_id, "classifying")
    try:
        doc_type = await _call_with_retry(
            lambda: provider.classify(job.raw_text),
            timeout=settings.llm_timeout,
        )
    except asyncio.TimeoutError:
        await job_store.set_error(
            job_id, "llm_error",
            "Extraction timed out. The document may be too large or complex. Try again.",
        )
        return
    except Exception as exc:
        logger.exception("Classification failed for job %s", job_id)
        await job_store.set_error(
            job_id, "llm_error",
            "Extraction failed after retry. Check your document and try again.",
        )
        return

    await job_store.set_doc_type(job_id, doc_type)

    if doc_type == "unknown":
        # Job stays in current state with doc_type="unknown", extraction_result=None
        # User must override doc_type via PATCH before extraction proceeds
        # Set status to complete per UI-SPEC: "job completes with doc_type='unknown'"
        await job_store.set_status(job_id, "complete")
        return

    # Step 2: Extract
    await _extract_with_schema(job_id, job.raw_text, doc_type)


async def extract_with_type(job_id: str, doc_type: str) -> None:
    """Extract fields using a specific doc_type (for override/re-extraction).

    Called from PATCH /jobs/{id}/doc_type handler. Skips classification.
    """
    job = await job_store.get(job_id)
    if job is None:
        logger.error("extract_with_type called with unknown job_id: %s", job_id)
        return

    await _extract_with_schema(job_id, job.raw_text, doc_type)


async def _extract_with_schema(job_id: str, raw_text: str, doc_type: str) -> None:
    """Run extraction with a specific schema. Shared by pipeline and override flows."""
    schema = SCHEMA_REGISTRY.get(doc_type)
    if schema is None:
        await job_store.set_error(
            job_id, "llm_error",
            f"No extraction schema for document type: {doc_type}",
        )
        return

    await job_store.set_status(job_id, "extracting")
    provider = get_provider()

    try:
        result = await _call_with_retry(
            lambda: provider.extract(raw_text, schema),
            timeout=settings.llm_timeout,
        )
    except asyncio.TimeoutError:
        await job_store.set_error(
            job_id, "llm_error",
            "Extraction timed out. The document may be too large or complex. Try again.",
        )
        return
    except Exception as exc:
        logger.exception("Extraction failed for job %s (doc_type: %s)", job_id, doc_type)
        await job_store.set_error(
            job_id, "llm_error",
            "Extraction failed after retry. Check your document and try again.",
        )
        return

    await job_store.set_extraction_result(job_id, result.model_dump())
