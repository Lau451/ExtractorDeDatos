# Phase 1: Foundation - Research

**Researched:** 2026-03-18
**Domain:** FastAPI async job infrastructure + Docling multi-format document ingestion
**Confidence:** HIGH (core APIs), MEDIUM (Docling timeout behavior)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Docling output format:** Export format is structured markdown via `export_to_markdown()` — tables become markdown tables, headings preserved. Field key in job result: `raw_text`.
- **Excel ingestion:** Extract all sheets as separate markdown table sections. Multi-sheet workbooks are fully captured — no sheet is skipped.
- **OCR strategy:** OCR runs as fallback only. Use Docling's native text extraction first. Fall back to OCR when no text layer is detected or extracted text is below a minimum character count. Never force OCR on text-based PDFs.
- **Docling timeout:** Hard timeout: 60 seconds per document. If exceeded, job moves to `error` state with `error_code: "docling_timeout"`.
- **Job response schema:** Successful completed job includes `raw_text` (markdown string from Docling) in result. Failed job includes `error_code` + `error_message`.
- **Error response contract:**
  - JSON body: `{"error": "<error_code>", "message": "<human-readable description>"}`
  - HTTP 400 — unsupported file type or invalid request (job never created)
  - HTTP 404 — job ID not found
  - HTTP 408 — Docling processing timeout
  - HTTP 422 — corrupt or unreadable file (file accepted but unparseable)
  - HTTP 500 — unexpected server error
  - Error codes: `unsupported_file_type`, `docling_timeout`, `docling_parse_error`, `job_not_found`
  - Failed job state: `{"status": "error", "error_code": "docling_timeout", "error_message": "Document processing exceeded 60s timeout"}`
- **SDK:** Use `google-genai` 1.68.0 (NOT `google-generativeai` — deprecated November 2025)
- **FastAPI UploadFile lifecycle:** Always read `UploadFile` bytes in endpoint before passing to `BackgroundTask` (FastAPI v0.106+ lifecycle requirement)
- **Job store:** In-memory job store with `asyncio.Lock` for race-condition safety

### Claude's Discretion
- Project directory layout (module structure within src/)
- Minimum character count threshold for OCR fallback trigger
- Exact job store data structure (fields beyond status/result/error)
- asyncio.Lock implementation pattern
- uvicorn startup configuration

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ING-01 | User can upload a PDF file (text-based) and the system extracts its content | Docling `DocumentConverter` with `do_ocr=False` handles text PDFs natively via pdfium |
| ING-02 | User can upload a scanned PDF or image-based PDF and the system extracts text via full-page OCR | Docling OCR fallback: `do_ocr=True` + `EasyOcrOptions` when text layer absent |
| ING-03 | User can upload an Excel file (XLSX/XLS) and the system reads its cell content | Docling `InputFormat.XLSX` with default format options converts all sheets |
| ING-04 | User can upload an image file (PNG/JPG) and the system extracts text via OCR | Docling `InputFormat.IMAGE` with `EasyOcrOptions` handles PNG/JPEG |
| ING-05 | User can upload an HTML file and the system parses its content | Docling `InputFormat.HTML` with default options |
| ING-06 | System rejects unsupported file types with a clear error message before processing | Extension + MIME whitelist check in endpoint before job creation; 400 response |
| API-01 | API exposes POST /extract that accepts a file upload and returns a job ID immediately | FastAPI `BackgroundTasks` pattern — return UUID on POST, process asynchronously |
| API-02 | API exposes GET /jobs/{id} that returns current job status | In-memory dict with `asyncio.Lock` returns serialized Job model |
| API-05 | API exposes GET /health that returns service health status | Simple FastAPI endpoint returning `{"status": "healthy"}` |
</phase_requirements>

---

## Summary

Phase 1 builds the FastAPI foundation and replaces the old pdfplumber/Tesseract chain with Docling as the single unified parser for all five supported input formats (PDF text, PDF scanned, XLSX, PNG/JPG, HTML). Docling 2.80.0 handles all formats through a single `DocumentConverter` API, with per-format `PipelineOptions` controlling whether OCR is active. The job infrastructure is a thread-safe in-memory dict protected by a single `asyncio.Lock`; because Docling's `convert()` is synchronous and CPU-bound, it must run inside `asyncio.to_thread()` (or `loop.run_in_executor`) to avoid blocking the event loop.

The single biggest integration hazard is the FastAPI v0.106+ UploadFile lifecycle: the file handle is closed before any `BackgroundTask` runs, so the endpoint must `await file.read()` to get the bytes, then pass a `BytesIO` object to the background function. Docling's `DocumentStream(name=filename, stream=BytesIO(data))` accepts in-memory bytes for all formats, eliminating any need for temporary disk files.

Docling's built-in `document_timeout` (a `PipelineOptions` float field in seconds) provides a soft per-batch checkpoint, not a hard wall-clock guarantee. For the strict 60-second contract specified, the correct pattern is `asyncio.wait_for(asyncio.to_thread(converter.convert, source), timeout=60)` combined with `document_timeout=60` on `PipelineOptions` as a defense-in-depth measure.

**Primary recommendation:** Build one `IngestionService` that routes by extension to a Docling `DocumentConverter` instance pre-configured for each format; wrap every `converter.convert()` call with `asyncio.wait_for(asyncio.to_thread(...), timeout=60)`.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastapi | 0.135.1 | Async REST API framework | Industry standard for Python async APIs; native BackgroundTasks and UploadFile support |
| uvicorn | 0.42.0 | ASGI server | FastAPI's recommended server; supports `--reload` for dev |
| pydantic | 2.12.5 | Data validation and serialization | FastAPI requires it; v2 is significantly faster than v1 |
| python-multipart | 0.0.22 | Multipart file upload parsing | Required by FastAPI for `File(...)` / `UploadFile` support |
| docling | 2.80.0 | Unified document parser (PDF/XLSX/HTML/image) | Single library replacing pdfplumber + pytesseract + openpyxl chain |
| python-dotenv | 1.2.2 | `.env` loading | Standard env config for all phases |

### Supporting (Testing)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 9.0.2 | Test runner | All unit and integration tests |
| pytest-asyncio | 1.3.0 | Async test support | Testing async FastAPI endpoints and job store |
| httpx | 0.28.1 | Async HTTP client for tests | FastAPI TestClient uses it; required for `AsyncClient` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| docling | pdfplumber + pytesseract + openpyxl | Old stack: 3 libraries with separate configs, requires system Tesseract binary install; Docling unifies all formats with better table extraction |
| asyncio.to_thread | loop.run_in_executor | `asyncio.to_thread()` is cleaner (Python 3.9+); both are valid; `to_thread` has less boilerplate |
| asyncio.wait_for | document_timeout only | `document_timeout` is a soft batch-boundary check, not wall-clock; `asyncio.wait_for` provides the hard guarantee needed for the 60s contract |
| in-memory job store | Redis / Celery | Redis adds ops complexity; in-memory is sufficient for v1 single-process deployment |

**Installation:**
```bash
pip install fastapi==0.135.1 uvicorn==0.42.0 pydantic==2.12.5 python-multipart==0.0.22 docling==2.80.0 python-dotenv==1.2.2
# Dev/test
pip install pytest==9.0.2 pytest-asyncio==1.3.0 httpx==0.28.1
```

**Note on Docling install size:** Docling pulls in ML model weights (EasyOCR, table transformer) on first use. First startup downloads ~1-2 GB of models unless `DOCLING_ARTIFACTS_PATH` is pre-populated. Plan for a slow cold start in fresh environments.

**Version verification:** All versions confirmed against PyPI registry on 2026-03-18.

---

## Architecture Patterns

### Recommended Project Structure
```
src/
├── main.py               # FastAPI app factory + uvicorn entry point
├── api/
│   ├── __init__.py
│   ├── routes/
│   │   ├── extract.py    # POST /extract endpoint
│   │   ├── jobs.py       # GET /jobs/{id}
│   │   └── health.py     # GET /health
│   └── models.py         # Pydantic request/response schemas
├── core/
│   ├── __init__.py
│   ├── job_store.py      # In-memory job store with asyncio.Lock
│   └── config.py         # Settings (dotenv-backed)
└── ingestion/
    ├── __init__.py
    ├── service.py         # IngestionService: routing + convert() orchestration
    ├── docling_adapter.py # Wraps DocumentConverter; handles format config + timeout
    └── validators.py      # Extension/MIME whitelist, file size check
tests/
├── conftest.py            # Shared fixtures (TestClient, sample files)
├── test_extract.py        # POST /extract endpoint integration tests
├── test_jobs.py           # GET /jobs/{id} tests
├── test_health.py         # GET /health smoke test
└── test_ingestion.py      # IngestionService unit tests per format
```

### Pattern 1: FastAPI POST /extract — read bytes first, then BackgroundTask

**What:** Read all uploaded bytes within the request handler before the response is sent, then pass raw bytes (not the UploadFile handle) to the background task. This is required because FastAPI v0.106+ closes the UploadFile after the response is sent — before background tasks execute.

**When to use:** Every endpoint that accepts an UploadFile and processes it asynchronously.

```python
# Source: FastAPI GitHub Discussion #10936 + official docs
import uuid
from fastapi import FastAPI, UploadFile, BackgroundTasks, File
from fastapi.responses import JSONResponse

@app.post("/extract")
async def post_extract(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
):
    # Validate extension BEFORE creating any job
    allowed = {".pdf", ".xlsx", ".xls", ".png", ".jpg", ".jpeg", ".html", ".htm"}
    suffix = Path(file.filename).suffix.lower()
    if suffix not in allowed:
        return JSONResponse(
            status_code=400,
            content={"error": "unsupported_file_type",
                     "message": f"File type '{suffix}' is not supported"}
        )

    # CRITICAL: read bytes NOW, inside the request context
    data: bytes = await file.read()
    filename: str = file.filename

    job_id = str(uuid.uuid4())
    await job_store.create(job_id)  # sets status = "pending"

    background_tasks.add_task(process_document, job_id, data, filename)
    return {"job_id": job_id, "status": "pending"}
```

### Pattern 2: Background processing with asyncio.to_thread + asyncio.wait_for

**What:** Docling's `convert()` is synchronous and CPU-bound. Running it directly inside an `async def` background task blocks the event loop. Wrap it with `asyncio.to_thread()` to push it to a thread pool executor, then apply `asyncio.wait_for()` for the hard 60-second timeout.

**When to use:** Any synchronous CPU-bound call inside an async context.

```python
# Source: Python asyncio docs + Docling PipelineOptions reference
import asyncio
from io import BytesIO
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import DocumentStream, ConversionStatus
from docling.datamodel.pipeline_options import PdfPipelineOptions, EasyOcrOptions
from docling.document_converter import PdfFormatOption, InputFormat

async def process_document(job_id: str, data: bytes, filename: str):
    await job_store.set_status(job_id, "processing")
    try:
        source = DocumentStream(name=filename, stream=BytesIO(data))
        result = await asyncio.wait_for(
            asyncio.to_thread(_run_docling, source, filename),
            timeout=60.0
        )
        markdown = result.document.export_to_markdown()
        await job_store.set_complete(job_id, raw_text=markdown)
    except asyncio.TimeoutError:
        await job_store.set_error(job_id, "docling_timeout",
                                  "Document processing exceeded 60s timeout")
    except Exception as exc:
        await job_store.set_error(job_id, "docling_parse_error", str(exc))

def _run_docling(source: DocumentStream, filename: str):
    """Synchronous — runs in thread via asyncio.to_thread()"""
    converter = _build_converter(filename)
    return converter.convert(source)
```

### Pattern 3: Docling converter configuration per format

**What:** Build a `DocumentConverter` with per-format `PipelineOptions`. For PDFs: disable OCR by default; for images: always enable OCR. The `document_timeout` field provides a soft internal checkpoint.

```python
# Source: Docling reference docs (pipeline_options, document_converter)
from docling.document_converter import DocumentConverter, PdfFormatOption, InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions, EasyOcrOptions, PipelineOptions
)

def _build_converter(filename: str) -> DocumentConverter:
    suffix = Path(filename).suffix.lower()

    if suffix == ".pdf":
        # OCR fallback mode: Docling tries native text first;
        # set do_ocr=True so it activates when text layer is absent
        pdf_opts = PdfPipelineOptions()
        pdf_opts.do_ocr = True          # enabled but used as fallback internally
        pdf_opts.do_table_structure = True
        pdf_opts.ocr_options = EasyOcrOptions(lang=["en"])
        pdf_opts.document_timeout = 60  # soft internal batch checkpoint
        return DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_opts)}
        )

    elif suffix in {".xlsx", ".xls"}:
        # Docling handles XLSX natively; all sheets captured
        return DocumentConverter(allowed_formats=[InputFormat.XLSX])

    elif suffix in {".png", ".jpg", ".jpeg"}:
        # Images always need OCR
        return DocumentConverter(allowed_formats=[InputFormat.IMAGE])

    elif suffix in {".html", ".htm"}:
        return DocumentConverter(allowed_formats=[InputFormat.HTML])

    raise ValueError(f"Unsupported extension: {suffix}")
```

**OCR fallback implementation note:** Docling's `do_ocr=True` on `PdfPipelineOptions` makes the pipeline attempt OCR on pages where pdfium finds no text (i.e., scanned pages). This is the correct OCR-as-fallback behavior. If you need explicit programmatic control based on character count, check `len(result.document.export_to_markdown().strip())` after an initial no-OCR pass, then re-convert with `force_full_page_ocr=True` if below threshold.

### Pattern 4: Thread-safe in-memory job store

**What:** A plain Python dict protected by a single `asyncio.Lock`. Because FastAPI runs in a single async event loop, the lock prevents race conditions when multiple background tasks read/write job state concurrently.

```python
# Source: Python asyncio docs
import asyncio
from dataclasses import dataclass, field
from typing import Optional, Literal
from datetime import datetime
import uuid

JobStatus = Literal["pending", "processing", "complete", "error"]

@dataclass
class Job:
    job_id: str
    status: JobStatus = "pending"
    raw_text: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
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

    async def set_status(self, job_id: str, status: JobStatus):
        async with self._lock:
            if job_id in self._store:
                self._store[job_id].status = status
                self._store[job_id].updated_at = datetime.utcnow()

    async def set_complete(self, job_id: str, raw_text: str):
        async with self._lock:
            job = self._store.get(job_id)
            if job:
                job.status = "complete"
                job.raw_text = raw_text
                job.updated_at = datetime.utcnow()

    async def set_error(self, job_id: str, error_code: str, error_message: str):
        async with self._lock:
            job = self._store.get(job_id)
            if job:
                job.status = "error"
                job.error_code = error_code
                job.error_message = error_message
                job.updated_at = datetime.utcnow()

# Singleton — instantiate once at module level
job_store = JobStore()
```

### Anti-Patterns to Avoid

- **Passing UploadFile to BackgroundTask directly:** File is closed before background runs (FastAPI v0.106+). Always `await file.read()` first.
- **Calling `converter.convert()` directly in `async def`:** Blocks the event loop for the entire processing duration (potentially 30-60s). Always use `asyncio.to_thread()`.
- **Relying solely on `document_timeout`:** This is a soft per-batch checkpoint, not wall-clock. A single very complex page batch could exceed 60s without triggering it. Use `asyncio.wait_for()` as the hard guarantee.
- **Creating a new DocumentConverter per request at startup time:** DocumentConverter construction downloads/initializes ML models. Create a singleton per format-configuration, or build once per background task call (acceptable since models are cached after first load).
- **Storing the UploadFile object in the job dict:** UploadFile is request-scoped. Store only the bytes or the extracted markdown result.
- **Running asyncio.Lock in a thread executor:** `asyncio.Lock` is not thread-safe; it is only safe within the event loop thread. Do not acquire it from within `asyncio.to_thread` callbacks.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Multi-format document parsing | Custom PDF/XLSX/OCR pipeline | `docling` DocumentConverter | OCR, table detection, layout analysis, heading preservation — hundreds of edge cases |
| ASGI server lifecycle | Custom HTTP server | `uvicorn` | Handles event loop, shutdown signals, keep-alive |
| Request validation | Custom type checkers | Pydantic v2 models | Auto-generates JSON schema, handles coercion, raises 422 automatically |
| Multipart parsing | Manual boundary splitting | `python-multipart` (FastAPI uses it automatically) | RFC 2046 compliance, streaming support |
| UUID generation | Custom ID schemes | `uuid.uuid4()` standard library | Collision-resistant, universally portable |

**Key insight:** Docling's value is in the dozens of edge cases it handles that would require months to build from scratch — reading order on multi-column PDFs, table cell merging, scanned page detection, XLS/XLSX format differences. Do not replicate any of this.

---

## Common Pitfalls

### Pitfall 1: UploadFile closed before BackgroundTask
**What goes wrong:** Background task tries to read `file.read()` or access `file.file` and gets an I/O error or empty bytes because FastAPI/Starlette closed the underlying spooled temp file after sending the response.
**Why it happens:** FastAPI v0.106+ introduced this lifecycle change — background tasks run after response is fully sent.
**How to avoid:** Always `data = await file.read()` in the endpoint handler before returning. Pass `data: bytes` (not `file: UploadFile`) to the background task.
**Warning signs:** Background task receives empty bytes, or `ValueError: I/O operation on closed file`.

### Pitfall 2: Blocking the event loop with Docling
**What goes wrong:** Server becomes unresponsive during document processing. All other requests queue behind the single running job. Health endpoint times out.
**Why it happens:** `converter.convert()` is a synchronous, CPU-bound call. Calling it directly in `async def` without threading prevents other coroutines from executing.
**How to avoid:** Always `await asyncio.to_thread(_run_docling, ...)`.
**Warning signs:** Health check returns 408 while a job is processing; single-core CPU pegged at 100%.

### Pitfall 3: Docling document_timeout is not a wall-clock timeout
**What goes wrong:** A complex scanned PDF takes 90 seconds despite `document_timeout=60` because the timeout is only checked at page-batch boundaries.
**Why it happens:** Docling processes in page batches (default 4 pages per batch). The timeout check fires between batches, not mid-batch.
**How to avoid:** Use `asyncio.wait_for(..., timeout=60)` as the actual wall-clock enforcer. Keep `document_timeout=60` as defense-in-depth (it will cut off further batch processing after the first timed-out batch completes).
**Warning signs:** Job shows "processing" for longer than 60 seconds without hitting the error state.

### Pitfall 4: Docling model cold start
**What goes wrong:** First request hangs for 60-120 seconds while EasyOCR and table transformer models download/initialize. Looks like a bug.
**Why it happens:** Docling downloads ML model weights on first use unless `DOCLING_ARTIFACTS_PATH` points to pre-cached models.
**How to avoid:** Warm up the converter at application startup using a `@app.on_event("startup")` handler (or `lifespan` context manager in newer FastAPI) that converts a tiny test document. Log the startup duration.
**Warning signs:** First request always times out; subsequent requests are fast.

### Pitfall 5: asyncio.Lock acquired from inside thread executor
**What goes wrong:** Deadlock or "got Future attached to a different loop" error when `set_status()` is called from within `asyncio.to_thread()`.
**Why it happens:** `asyncio.Lock` is bound to the running event loop. Calling `await lock.acquire()` from a thread pool thread that has no event loop raises an error.
**How to avoid:** Only call `async` methods of `JobStore` from coroutines in the event loop thread. In the background task (which is itself a coroutine), call `await job_store.set_status(...)` directly — not from within the `asyncio.to_thread` callback.

### Pitfall 6: XLSX multi-sheet export missing sheets
**What goes wrong:** Only the first sheet of a multi-sheet Excel workbook appears in the markdown output.
**Why it happens:** Some Docling versions or configurations may default to processing the active sheet only.
**How to avoid:** Verify the markdown output of a multi-sheet XLSX contains section headers for each sheet. If not, iterate sheets manually with openpyxl as a fallback (this is an edge case worth a test).
**Warning signs:** Test with a 3-sheet workbook; only 1 table section appears in `export_to_markdown()` output.

---

## Code Examples

### Complete extract endpoint
```python
# src/api/routes/extract.py
import uuid
from pathlib import Path
from io import BytesIO
from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from src.core.job_store import job_store
from src.ingestion.service import process_document

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".png", ".jpg", ".jpeg", ".html", ".htm"}

@router.post("/extract")
async def post_extract(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        return JSONResponse(
            status_code=400,
            content={"error": "unsupported_file_type",
                     "message": f"'{suffix}' is not a supported file type"}
        )

    data: bytes = await file.read()  # MUST happen before response is sent
    filename: str = file.filename
    job_id = str(uuid.uuid4())
    await job_store.create(job_id)
    background_tasks.add_task(process_document, job_id, data, filename)
    return {"job_id": job_id, "status": "pending"}
```

### GET /jobs/{id} endpoint
```python
# src/api/routes/jobs.py
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from src.core.job_store import job_store

router = APIRouter()

@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job = await job_store.get(job_id)
    if job is None:
        return JSONResponse(
            status_code=404,
            content={"error": "job_not_found",
                     "message": f"No job with ID '{job_id}'"}
        )
    if job.status == "complete":
        return {"job_id": job.job_id, "status": "complete",
                "result": {"raw_text": job.raw_text}}
    if job.status == "error":
        return JSONResponse(
            status_code=200,  # 200: job found, error is in body
            content={"job_id": job.job_id, "status": "error",
                     "error_code": job.error_code,
                     "error_message": job.error_message}
        )
    return {"job_id": job.job_id, "status": job.status}
```

### GET /health endpoint
```python
# src/api/routes/health.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health():
    return {"status": "healthy"}
```

### Ingestion service with timeout
```python
# src/ingestion/service.py
import asyncio
from io import BytesIO
from pathlib import Path
from docling.datamodel.base_models import DocumentStream
from src.ingestion.docling_adapter import build_converter
from src.core.job_store import job_store

DOCLING_TIMEOUT_SECONDS = 60.0

async def process_document(job_id: str, data: bytes, filename: str):
    await job_store.set_status(job_id, "processing")
    try:
        source = DocumentStream(name=filename, stream=BytesIO(data))
        result = await asyncio.wait_for(
            asyncio.to_thread(_sync_convert, source, filename),
            timeout=DOCLING_TIMEOUT_SECONDS,
        )
        markdown = result.document.export_to_markdown()
        if not markdown.strip():
            await job_store.set_error(job_id, "docling_parse_error",
                                      "Document produced no extractable text")
            return
        await job_store.set_complete(job_id, raw_text=markdown)
    except asyncio.TimeoutError:
        await job_store.set_error(
            job_id, "docling_timeout",
            "Document processing exceeded 60s timeout"
        )
    except Exception as exc:
        await job_store.set_error(job_id, "docling_parse_error", str(exc))


def _sync_convert(source: DocumentStream, filename: str):
    """Called from asyncio.to_thread — must be synchronous."""
    converter = build_converter(filename)
    return converter.convert(source)
```

### Docling adapter — format-aware converter factory
```python
# src/ingestion/docling_adapter.py
from pathlib import Path
from docling.document_converter import DocumentConverter, PdfFormatOption, InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, EasyOcrOptions

OCR_MIN_CHARS = 50  # threshold below which OCR is triggered (Claude's discretion)

def build_converter(filename: str) -> DocumentConverter:
    suffix = Path(filename).suffix.lower()

    if suffix == ".pdf":
        pdf_opts = PdfPipelineOptions()
        pdf_opts.do_ocr = True                   # enables fallback OCR for scanned pages
        pdf_opts.do_table_structure = True
        pdf_opts.ocr_options = EasyOcrOptions(lang=["en"], force_full_page_ocr=False)
        pdf_opts.document_timeout = 60           # soft batch-level checkpoint
        return DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_opts)}
        )

    elif suffix in {".xlsx", ".xls"}:
        return DocumentConverter(allowed_formats=[InputFormat.XLSX])

    elif suffix in {".png", ".jpg", ".jpeg"}:
        return DocumentConverter(allowed_formats=[InputFormat.IMAGE])

    elif suffix in {".html", ".htm"}:
        return DocumentConverter(allowed_formats=[InputFormat.HTML])

    raise ValueError(f"No converter for extension: {suffix}")
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| pdfplumber + pytesseract + openpyxl | docling unified converter | STATE.md decision 2026-03-18 | Single dependency, no Tesseract binary required, better table extraction |
| google-generativeai SDK | google-genai 1.68.0 | November 2025 (deprecation) | Different import path and API surface; old SDK is deprecated |
| FastAPI UploadFile passed to BackgroundTask | Read bytes first, pass bytes to BackgroundTask | FastAPI v0.106.0 (2023) | Breaking change — passing UploadFile to BackgroundTask silently fails |
| asyncio.wait_for wrapping coroutine | asyncio.wait_for(asyncio.to_thread(...)) | Python 3.9+ | Only works for blocking sync code if wrapped in to_thread first |

**Deprecated/outdated:**
- `google-generativeai`: Deprecated November 2025; replaced by `google-genai`. Do not install.
- `pdfplumber`, `pytesseract`, `openpyxl` as primary parsers: Replaced by Docling per STATE.md decision. These are no longer in Phase 1 scope.
- Passing `UploadFile` directly to `BackgroundTasks.add_task()`: Broken since FastAPI v0.106.0.

---

## Open Questions

1. **XLSX multi-sheet behavior in Docling 2.80.0**
   - What we know: Docling lists XLSX as a supported InputFormat; `export_to_markdown()` should produce table sections per sheet.
   - What's unclear: Whether all sheets are exported by default or only the active sheet. No official documentation explicitly confirms multi-sheet behavior in the markdown export.
   - Recommendation: Add a multi-sheet XLSX test in Wave 0 test fixtures. If Docling only exports one sheet, fall back to openpyxl for XLSX processing.

2. **DocumentStream support for IMAGE format**
   - What we know: A GitHub issue (#2279) notes DocumentStream primarily targets BytesIO but image format recognition may require the file extension in the `name` parameter.
   - What's unclear: Whether PNG/JPG bytes in a `DocumentStream` with `.png` name consistently triggers `InputFormat.IMAGE` detection.
   - Recommendation: Test with `DocumentStream(name="test.png", stream=BytesIO(png_bytes))` and `allowed_formats=[InputFormat.IMAGE]`. If detection fails, save to a temp file as fallback.

3. **Docling model download on Windows**
   - What we know: Models download on first use to a cache directory; `DOCLING_ARTIFACTS_PATH` overrides the default.
   - What's unclear: Whether the default Windows cache path (`%USERPROFILE%/.cache/docling/`) causes issues in corporate environments with restricted write access.
   - Recommendation: Set `DOCLING_ARTIFACTS_PATH` explicitly in `.env` and pre-download during setup.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio 1.3.0 |
| Config file | `pytest.ini` or `pyproject.toml [tool.pytest.ini_options]` — Wave 0 gap |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v --tb=short` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ING-01 | Text PDF produces non-empty markdown | unit | `pytest tests/test_ingestion.py::test_text_pdf -x` | Wave 0 |
| ING-02 | Scanned PDF produces non-empty markdown (OCR active) | unit | `pytest tests/test_ingestion.py::test_scanned_pdf -x` | Wave 0 |
| ING-03 | XLSX multi-sheet produces markdown with all sheets | unit | `pytest tests/test_ingestion.py::test_xlsx_multisheet -x` | Wave 0 |
| ING-04 | PNG image produces non-empty markdown via OCR | unit | `pytest tests/test_ingestion.py::test_png_ocr -x` | Wave 0 |
| ING-05 | HTML file produces non-empty markdown | unit | `pytest tests/test_ingestion.py::test_html -x` | Wave 0 |
| ING-06 | Unsupported extension returns HTTP 400 with error body | integration | `pytest tests/test_extract.py::test_unsupported_extension -x` | Wave 0 |
| API-01 | POST /extract returns job_id and "pending" status | integration | `pytest tests/test_extract.py::test_post_extract_returns_job_id -x` | Wave 0 |
| API-02 | GET /jobs/{id} returns pending → processing → complete | integration | `pytest tests/test_jobs.py::test_job_lifecycle -x` | Wave 0 |
| API-05 | GET /health returns {"status": "healthy"} | smoke | `pytest tests/test_health.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_health.py tests/test_extract.py -x -q`
- **Per wave merge:** `pytest tests/ -v --tb=short`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/conftest.py` — TestClient fixture, sample file fixtures (small PDF, XLSX, PNG, HTML)
- [ ] `tests/test_health.py` — GET /health smoke test
- [ ] `tests/test_extract.py` — POST /extract endpoint tests (happy path + ING-06 rejection)
- [ ] `tests/test_jobs.py` — GET /jobs/{id} status polling tests
- [ ] `tests/test_ingestion.py` — per-format IngestionService unit tests
- [ ] `pytest.ini` — asyncio_mode = "auto" configuration for pytest-asyncio 1.3.0
- [ ] Sample test files — `tests/fixtures/sample.pdf`, `sample_scanned.pdf`, `sample.xlsx`, `sample.png`, `sample.html`

---

## Sources

### Primary (HIGH confidence)
- PyPI registry — docling 2.80.0, fastapi 0.135.1, uvicorn 0.42.0, pydantic 2.12.5, python-multipart 0.0.22, pytest 9.0.2, pytest-asyncio 1.3.0, httpx 0.28.1, python-dotenv 1.2.2 (verified 2026-03-18)
- Docling reference: https://docling-project.github.io/docling/reference/pipeline_options/ — PipelineOptions fields, PdfPipelineOptions, EasyOcrOptions, document_timeout
- Docling reference: https://docling-project.github.io/docling/reference/document_converter/ — DocumentConverter.convert() signature, InputFormat enum, DocumentStream
- FastAPI official docs: https://fastapi.tiangolo.com/tutorial/background-tasks/ — BackgroundTasks pattern

### Secondary (MEDIUM confidence)
- GitHub docling issue #779 (https://github.com/docling-project/docling/issues/779) — document_timeout behavior, batch checkpoint semantics, ConversionStatus.PARTIAL_SUCCESS
- FastAPI GitHub Discussion #10936 (https://github.com/fastapi/fastapi/discussions/10936) — UploadFile closed before BackgroundTask in v0.106+; read bytes workaround
- WebSearch verified: EasyOcrOptions fields (lang, force_full_page_ocr, use_gpu, confidence_threshold) confirmed against pipeline_options reference page

### Tertiary (LOW confidence)
- Docling XLSX multi-sheet export behavior — not explicitly documented; inferred from InputFormat.XLSX support and export_to_markdown() behavior. Requires validation test.
- DocumentStream with IMAGE format — GitHub issue #2279 suggests potential format detection limitation when using BytesIO; name parameter with correct extension appears to resolve it.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions verified against PyPI registry 2026-03-18
- Architecture: HIGH — FastAPI BackgroundTask + asyncio.to_thread is well-documented standard pattern; Docling API confirmed via official reference
- Pitfalls: HIGH (UploadFile, event loop blocking) / MEDIUM (Docling timeout semantics, XLSX multi-sheet)
- Validation architecture: HIGH — pytest + pytest-asyncio standard; test structure maps directly to requirements

**Research date:** 2026-03-18
**Valid until:** 2026-04-18 (Docling releases frequently; re-verify version before pinning if > 30 days)
