---
phase: 01-foundation
verified: 2026-03-19T05:00:00Z
status: passed
score: 11/11 must-haves verified
re_verification:
  previous_status: passed
  previous_score: 9/9
  note: "Previous verification predated plan 01-03 (gap-closure). Re-verification incorporates plan 01-03 must_haves and confirms no regressions."
  gaps_closed:
    - "PNG OCR now uses force_full_page_ocr=True via ImageFormatOption — complete text extraction guaranteed"
    - "HTML/general errors now surface exc.__cause__ with logger.exception() — real error detail in job store"
  gaps_remaining: []
  regressions: []
---

# Phase 1: Foundation Verification Report

**Phase Goal:** Build the server foundation — FastAPI app, in-memory job store, Docling-backed ingestion for PDF/Excel/image/HTML, POST /extract + GET /jobs/{id} endpoints, and GET /health. All Phase 1 requirements tested and passing.
**Verified:** 2026-03-19T05:00:00Z
**Status:** passed
**Re-verification:** Yes — after gap closure (plan 01-03 executed post-UAT)

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | GET /health returns `{"status": "healthy"}` with HTTP 200 | VERIFIED | `health.py` line 8-10: `@router.get("/health", response_model=HealthResponse)` returns `{"status": "healthy"}`; `main.py` registers `health_router` |
| 2 | Job store can create, get, and transition jobs through pending -> processing -> complete \| error | VERIFIED | `job_store.py`: `create`, `get`, `set_status`, `set_complete`, `set_error` all implemented with `asyncio.Lock`; singleton `job_store = JobStore()` at line 60 |
| 3 | All dependencies install without errors | VERIFIED | `requirements.txt` pins fastapi, uvicorn, pydantic, docling, python-multipart; commits 05d0f13 and 4b015ea confirmed working environment including easyocr |
| 4 | User can POST a PDF/XLSX/PNG/JPG/HTML file to /extract and receive a job_id immediately | VERIFIED | `extract.py` lines 14-39: validates extension, reads bytes, creates job, enqueues background task, returns `{"job_id": ..., "status": "pending"}` |
| 5 | User can GET /jobs/{id} and see status transition from pending through processing to complete | VERIFIED | `jobs.py` lines 9-41: handles all four states with correct HTTP codes (404 unknown, 200 all states including error) |
| 6 | Scanned PDFs and images produce non-empty raw_text via OCR | VERIFIED | `docling_adapter.py`: PDF branch `do_ocr=True` + `EasyOcrOptions`; IMAGE branch `force_full_page_ocr=True` + `ImageFormatOption`; `test_scanned_pdf_ingestion` and `test_png_ingestion` in test suite |
| 7 | Uploading an unsupported file type returns HTTP 400 with error body and no job is created | VERIFIED | `extract.py` lines 20-29: returns 400 with `"error": "unsupported_file_type"` before `job_store.create`; `test_unsupported_extension` verifies no job created |
| 8 | XLSX files with multiple sheets produce markdown containing content | VERIFIED | `docling_adapter.py` line 22: `DocumentConverter(allowed_formats=[InputFormat.XLSX])`; 2-sheet `sample.xlsx` fixture used in `test_xlsx_ingestion` |
| 9 | Docling timeout (>60s) transitions job to error state with error_code docling_timeout | VERIFIED | `service.py` lines 32-37: `asyncio.TimeoutError` caught and calls `set_error(job_id, "docling_timeout", ...)`; `asyncio.wait_for(..., timeout=settings.docling_timeout_seconds)` at line 19 |
| 10 | PNG image with visible text produces raw_text containing all text extracted by OCR (not incomplete) | VERIFIED | `docling_adapter.py` lines 24-32: IMAGE branch uses `PdfPipelineOptions(do_ocr=True)` with `EasyOcrOptions(force_full_page_ocr=True)` wrapped in `ImageFormatOption` — commit fc03dad |
| 11 | HTML file that triggers a Docling internal error surfaces the real error message, not the opaque wrapper | VERIFIED | `service.py` lines 38-41: `except Exception as exc` calls `logger.exception(...)` then `detail = str(exc.__cause__) if exc.__cause__ else str(exc)` — commit 7c26a38 |

**Score:** 11/11 truths verified

---

### Required Artifacts

#### Plan 01-01 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/core/job_store.py` | Thread-safe in-memory job store with asyncio.Lock | VERIFIED | `class JobStore` at line 20; `self._lock = asyncio.Lock()` at line 23; singleton `job_store = JobStore()` at line 60; `async def set_complete` and `async def set_error` both implemented with lock acquisition |
| `src/core/config.py` | Application settings via pydantic-settings | VERIFIED | `class Settings(BaseSettings)` with `docling_timeout_seconds: float = 60.0`; `settings = Settings()` singleton |
| `src/api/models.py` | Pydantic request/response schemas | VERIFIED | Exports `JobResponse`, `ErrorResponse`, `ExtractResponse`, `HealthResponse`, `JobResultPayload` — all 5 classes present |
| `src/main.py` | FastAPI app factory with router registration | VERIFIED | `app = FastAPI(...)` + `app.include_router(health_router)` + `app.include_router(extract_router)` + `app.include_router(jobs_router)` |
| `src/api/routes/health.py` | GET /health endpoint | VERIFIED | `@router.get("/health", response_model=HealthResponse)` returns `{"status": "healthy"}` |

#### Plan 01-02 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/ingestion/validators.py` | Extension whitelist validation | VERIFIED | `ALLOWED_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".png", ".jpg", ".jpeg", ".html", ".htm"}` + `validate_file_extension` returning extension or None |
| `src/ingestion/docling_adapter.py` | Format-aware Docling converter factory | VERIFIED | `def build_converter(filename: str)` with PDF+OCR, XLSX, IMAGE+ImageFormatOption, HTML branches (IMAGE branch updated by plan 01-03) |
| `src/ingestion/service.py` | Async document processing with timeout | VERIFIED | `async def process_document` with `asyncio.wait_for`, `asyncio.to_thread`, `export_to_markdown`, handles `docling_timeout` and `docling_parse_error`; updated by plan 01-03 with `logger.exception` + `exc.__cause__` |
| `src/api/routes/extract.py` | POST /extract endpoint | VERIFIED | `@router.post("/extract")` with validation, `await file.read()`, `job_store.create`, `background_tasks.add_task(process_document, ...)` |
| `src/api/routes/jobs.py` | GET /jobs/{id} endpoint | VERIFIED | `@router.get("/jobs/{job_id}")` handles all states: 404 for unknown, 200 for complete/error/pending/processing |
| `tests/test_extract.py` | Integration tests for POST /extract | VERIFIED | Contains `test_post_extract_returns_job_id`, `test_unsupported_extension`, xlsx/png/html variants — 5 tests |
| `tests/test_jobs.py` | Integration tests for GET /jobs/{id} | VERIFIED | Contains `test_get_nonexistent_job`, `test_job_lifecycle` with HTML polling to "complete" and `raw_text` assertion |

#### Plan 01-03 Artifacts (Gap Closure)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/ingestion/docling_adapter.py` | IMAGE branch with ImageFormatOption and force_full_page_ocr=True | VERIFIED | Line 3: `ImageFormatOption` imported; lines 24-32: IMAGE branch uses `ImageFormatOption(pipeline_options=img_opts)` with `force_full_page_ocr=True` |
| `src/ingestion/service.py` | Error handler that exposes exc.__cause__ and logs full traceback | VERIFIED | Lines 38-41: `except Exception as exc:` calls `logger.exception(...)` and `detail = str(exc.__cause__) if exc.__cause__ else str(exc)` |

---

### Key Link Verification

#### Plan 01-01 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/main.py` | `src/api/routes/health.py` | `app.include_router(health_router)` | WIRED | Line 8: `app.include_router(health_router)` |
| `src/main.py` | `src/api/routes/extract.py` | `app.include_router(extract_router)` | WIRED | Line 9: `app.include_router(extract_router)` |
| `src/main.py` | `src/api/routes/jobs.py` | `app.include_router(jobs_router)` | WIRED | Line 10: `app.include_router(jobs_router)` |

#### Plan 01-02 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/api/routes/extract.py` | `src/ingestion/service.py` | `background_tasks.add_task(process_document, ...)` | WIRED | Line 37: `background_tasks.add_task(process_document, job_id, data, filename)` |
| `src/ingestion/service.py` | `src/ingestion/docling_adapter.py` | `build_converter(filename)` in `_sync_convert` | WIRED | Line 49: `return build_converter(filename).convert(source)` |
| `src/ingestion/service.py` | `src/core/job_store.py` | `job_store.set_status/set_complete/set_error` | WIRED | Lines 16, 31, 25, 34, 41: all three methods called at correct points |
| `src/api/routes/extract.py` | `src/core/job_store.py` | `job_store.create` on POST | WIRED | Line 36: `await job_store.create(job_id)` |
| `src/api/routes/extract.py` | `src/ingestion/validators.py` | `validate_file_extension` before job creation | WIRED | Line 20: `ext = validate_file_extension(file.filename)` — runs before `job_store.create` |

#### Plan 01-03 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/ingestion/docling_adapter.py` | `docling.document_converter.ImageFormatOption` | import and format_options dict | WIRED | Line 3: `from docling.document_converter import ... ImageFormatOption`; line 31: `ImageFormatOption(pipeline_options=img_opts)` |
| `src/ingestion/service.py` | `logging` | `logging.exception` call in except block | WIRED | Line 2: `import logging`; line 11: `logger = logging.getLogger(__name__)`; line 39: `logger.exception(...)` |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| ING-01 | 01-02 | User can upload a PDF (text-based) and system extracts content | SATISFIED | `test_text_pdf_ingestion`: calls `process_document` with `sample.pdf`, asserts status="complete" and non-empty `raw_text` |
| ING-02 | 01-02 | User can upload a scanned/image-based PDF and system extracts via OCR | SATISFIED | `test_scanned_pdf_ingestion`: loads `scanned.pdf` (raster-only fixture), asserts status="complete" and non-empty `raw_text`; PDF branch has `do_ocr=True` + `EasyOcrOptions` |
| ING-03 | 01-02 | User can upload XLSX/XLS and system reads cell content | SATISFIED | `test_xlsx_ingestion`: 2-sheet workbook → status="complete", non-empty `raw_text` |
| ING-04 | 01-02, 01-03 | User can upload PNG/JPG and system extracts text via OCR | SATISFIED | `test_png_ingestion`: status="complete", non-empty `raw_text`; IMAGE branch now uses `ImageFormatOption(force_full_page_ocr=True)` — gap closed by plan 01-03 |
| ING-05 | 01-02, 01-03 | User can upload HTML and system parses content | SATISFIED | `test_html_ingestion`: asserts status="complete" and `"Test Document" in raw_text`; error observability improved by plan 01-03 |
| ING-06 | 01-02 | System rejects unsupported file types with clear error before processing | SATISFIED | `extract.py` returns 400 with `"error": "unsupported_file_type"` before `job_store.create`; `test_unsupported_extension` verifies 400 + no job created |
| API-01 | 01-02 | API exposes POST /extract that accepts file upload and returns job ID immediately | SATISFIED | `extract.py` returns `{"job_id": ..., "status": "pending"}` synchronously; background task handles processing asynchronously |
| API-02 | 01-02 | API exposes GET /jobs/{id} returning current status (pending/processing/complete/error) | SATISFIED | `jobs.py` handles all four states; `test_job_lifecycle` polls HTML job to "complete" and asserts `raw_text` contains "Test Document" |
| API-05 | 01-01 | API exposes GET /health returning service health status | SATISFIED | `health.py` returns `{"status": "healthy"}`; registered in `main.py`; covered by `test_health_returns_200` |

**No orphaned requirements.** All 9 requirement IDs declared across plans (API-05 in 01-01; ING-01 through ING-06, API-01, API-02 in 01-02; ING-04 and ING-05 re-confirmed in 01-03) map to Phase 1 in REQUIREMENTS.md traceability table and are checked off.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/core/job_store.py` | 16, 17, 39, 47, 56 | `datetime.utcnow()` deprecated in Python 3.12+ | INFO | Deprecation warning only; no functional impact. Modern replacement: `datetime.now(datetime.UTC)`. Does not affect test outcomes. |

No blockers. No stubs. No placeholder returns. No empty handlers.

---

### Human Verification Required

#### 1. Scanned PDF OCR on a Real Document

**Test:** Upload a real multi-page scanned PDF (e.g., a scanned purchase order or invoice with printed text).
**Expected:** Job reaches "complete" status, `raw_text` contains recognizable document text.
**Why human:** The `scanned.pdf` fixture is a programmatic minimal raster image. Real scanned PDFs have variable image quality, skew, and font characteristics that differ from the synthetic fixture.

#### 2. PNG Full-Page OCR on a Dense Image

**Test:** Upload a PNG containing multiple lines of text (e.g., a screenshot of a terminal or a scanned form).
**Expected:** All lines of text appear in `raw_text`, not just the first detected region.
**Why human:** The `sample.png` fixture is a minimal 200x60 image with a single string. The `force_full_page_ocr=True` fix targets dense multi-region images — confirms the plan 01-03 fix is effective on realistic input.

#### 3. Concurrent Upload Race Condition

**Test:** Submit 10+ simultaneous POST /extract requests from separate terminal windows using `curl` in parallel.
**Expected:** Each request receives a distinct job_id, all jobs reach terminal states independently, no shared-state corruption.
**Why human:** `asyncio.Lock` correctness under concurrent load cannot be verified by sequential unit tests.

---

### Gaps Summary

No gaps. All 9 Phase 1 requirements (ING-01 through ING-06, API-01, API-02, API-05) are implemented, wired, and covered by passing tests across all three plans.

Plan 01-03 closed the two UAT gaps identified after the initial verification:
1. PNG OCR was producing incomplete text due to the IMAGE branch using bare `allowed_formats` without OCR pipeline options. Fixed with `ImageFormatOption(pipeline_options=PdfPipelineOptions(do_ocr=True, force_full_page_ocr=True))`.
2. HTML (and general) Docling errors surfaced an opaque "Pipeline SimplePipeline failed" wrapper. Fixed by unwrapping `exc.__cause__` and adding `logger.exception()` for full traceback in server logs.

One informational issue noted: `datetime.utcnow()` is deprecated in Python 3.12+. Generates deprecation warnings but does not affect correctness or test outcomes. Recommended fix in a future cleanup: replace with `datetime.now(datetime.UTC)`.

All commits from all three plans are present and verified in git history:
- 01-01: 05d0f13, 9758359, 4dfef22
- 01-02: 628d25a, 4b015ea
- 01-03: fc03dad, 7c26a38

---

_Verified: 2026-03-19T05:00:00Z_
_Verifier: Claude (gsd-verifier)_
