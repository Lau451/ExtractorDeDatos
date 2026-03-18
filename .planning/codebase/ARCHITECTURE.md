# Architecture

**Analysis Date:** 2026-03-18

## Pattern Overview

**Overall:** Layered Pipeline Architecture with Async Job Processing

DocExtract implements a four-layer pipeline that processes business documents through ingestion, interpretation, comparison, and export, exposed via an async FastAPI service. Each layer builds on the previous layer and can be independently tested. The system follows a request-response pattern with background job processing for long-running extractions.

**Key Characteristics:**
- Sequential data transformation through distinct phases (ingestion → extraction → comparison → export)
- Async job-based processing with status polling (FastAPI background tasks)
- Pluggable provider abstraction for LLM integration (swappable GPT/Claude/Gemini)
- Multi-format input support (PDF, Excel, PNG) converging to normalized text representation
- Structured output in three CSV formats (summary, line items, supplier comparison)

## Layers

**Layer 1: File Ingestion & Text Extraction**
- Purpose: Accept multiple file formats and produce normalized raw text output
- Location: `src/ingestion/` (Phase 1 implementation)
- Contains: File type routing, PDF text extraction (direct + OCR), Excel cell reading, image OCR processing
- Depends on: External OCR library (Tesseract or similar), PDF parsing library (pypdf2, pdfplumber), openpyxl
- Used by: LLM Extraction Pipeline layer
- Output: Normalized text documents with source metadata

**Layer 2: LLM Extraction Pipeline**
- Purpose: Interpret raw text and extract structured business fields with confidence scores
- Location: `src/extraction/` (Phase 2 implementation)
- Contains: LLM provider adapters, extraction prompts, field schema definitions, confidence scoring
- Depends on: Layer 1 (Ingestion), LLM APIs (OpenAI, Anthropic, Google), configuration system
- Used by: Comparison & CSV Output layer
- Output: Structured extraction records with field-level confidence scores and document type classification

**Layer 3: Comparison & CSV Output**
- Purpose: Synthesize supplier comparisons and generate three CSV export formats
- Location: `src/comparison/` and `src/export/` (Phase 3 implementation)
- Contains: Supplier extraction logic, comparison synthesis, CSV formatter (summary/line-items/comparison)
- Depends on: Layer 2 (Extraction), Python csv module, Pandas
- Used by: FastAPI Service layer
- Output: Three CSV files (summary, line items, supplier comparison) with best-price flagging

**Layer 4: FastAPI Service**
- Purpose: Expose the full pipeline as async REST API with job tracking and health monitoring
- Location: `src/api/` (Phase 4 implementation)
- Contains: FastAPI app initialization, endpoint handlers (/extract, /health, /export), job queue, async worker pool
- Depends on: All previous layers (1-3), FastAPI, background task queue (Celery or asyncio)
- Used by: External clients (web UI, command-line tools, procurement systems)
- Output: JSON responses (job IDs, health status, downloadable CSV files)

## Data Flow

**End-to-End Extraction Flow:**

1. **User uploads files** → POST /extract endpoint receives one or more files (PDF, Excel, PNG)
2. **Job creation** → API assigns unique job ID, queues extraction task, returns job ID immediately
3. **File ingestion** → Worker processes each file: routes by type → extracts raw text (OCR for scanned docs)
4. **LLM extraction** → Normalized text flows through LLM with structured prompts → outputs field extractions with confidence scores
5. **Document classification** → LLM detects document type (invoice, PO, tender, quotation, comparison) during extraction
6. **Comparison synthesis** → If supplier comparison documents detected, synthesize combined comparison from quotes
7. **CSV generation** → Three CSV formats produced: summary (1 row/doc), line items (1 row/item), comparison (suppliers vs items)
8. **Results storage** → Extraction results held in memory/session; job marked complete
9. **User polls status** → GET /job/{job_id} returns status (pending/processing/complete/error)
10. **User downloads CSV** → GET /export/{job_id} returns requested CSV file format (summary/line-items/comparison)

**State Management:**
- Job state stored in memory-resident job queue (dict or Celery result backend)
- File uploads accepted as multipart/form-data
- Extraction results cached per job ID until export or timeout
- No persistent storage in v1; results live for job session only

## Key Abstractions

**LLM Provider Adapter:**
- Purpose: Enable swappable LLM backends without changing extraction logic
- Examples: `src/extraction/providers/openai_provider.py`, `src/extraction/providers/claude_provider.py`, `src/extraction/providers/gemini_provider.py`
- Pattern: Abstract base class `LLMProvider` with concrete implementations; provider selected via `LLM_PROVIDER` config var
- Interface: `extract_fields(text: str, doc_type: Optional[str]) -> ExtractionResult`

**File Ingestion Router:**
- Purpose: Route incoming files to correct extraction handler based on MIME type
- Examples: `src/ingestion/router.py` dispatches to PDF, Excel, or Image handlers
- Pattern: Factory pattern with handler registry (`.pdf` → PDFHandler, `.xlsx` → ExcelHandler, `.png` → ImageHandler)
- Interface: `ingest(file: UploadFile) -> RawTextDocument`

**Extraction Schema:**
- Purpose: Define normalized fields extracted from all document types
- Examples: `src/extraction/schema.py` contains `ExtractionResult`, `LineItem`, `SupplierEntry` dataclasses
- Pattern: Pydantic models for validation + serialization
- Fields: `client_name`, `supplier_name`, `line_items[]`, `total_amount`, `date`, `reference_number`, `document_type`, `extraction_confidence`

**CSV Formatter:**
- Purpose: Generate three distinct CSV output formats from extraction results
- Examples: `src/export/formatters/summary_formatter.py`, `src/export/formatters/line_items_formatter.py`, `src/export/formatters/comparison_formatter.py`
- Pattern: Strategy pattern with pluggable formatters; each implements `to_csv() -> str`
- Interface: `format(extraction_results: List[ExtractionResult], format_type: str) -> str`

## Entry Points

**FastAPI Application:**
- Location: `src/api/app.py` or `src/main.py`
- Triggers: Server startup via `uvicorn src.main:app --reload` or Docker container start
- Responsibilities: Initialize FastAPI app, register all endpoints, initialize job queue, start background worker pool

**POST /extract Endpoint:**
- Location: `src/api/endpoints/extract.py`
- Triggers: HTTP POST with multipart file upload
- Responsibilities: Validate file types, create job ID, queue extraction task, return job ID to client

**Background Worker/Task Queue:**
- Location: `src/api/worker.py` or similar
- Triggers: Job queued by /extract endpoint
- Responsibilities: Orchestrate ingestion → extraction → comparison → CSV formatting pipeline

**GET /health Endpoint:**
- Location: `src/api/endpoints/health.py`
- Triggers: HTTP GET request
- Responsibilities: Check API readiness, verify background worker is running, return status

**GET /export Endpoint:**
- Location: `src/api/endpoints/export.py`
- Triggers: HTTP GET with job_id and format query params
- Responsibilities: Retrieve cached extraction results for job, serialize to requested CSV format, return downloadable file

## Error Handling

**Strategy:** Layered error handling with specific exception types per layer; client receives structured error responses with correlation IDs.

**Patterns:**

**Ingestion Layer:**
- File validation errors return 400 Bad Request (invalid file type, corrupt file)
- OCR failures logged but don't fail extraction (graceful degradation)
- Excel reading errors return 422 Unprocessable Entity (unreadable format)

**Extraction Layer:**
- LLM timeout/rate limit → retry with exponential backoff (up to 3 retries)
- LLM API key invalid → return 401 Unauthorized with configuration error message
- Partial extraction (missing required fields) → log warning, return confidence score < 0.5 for missing fields

**Comparison Layer:**
- Comparison synthesis failures → fallback to per-document results (no synthesis, skip comparison CSV)

**API Layer:**
- Job ID not found → 404 Not Found
- File upload too large → 413 Payload Too Large
- Extraction in progress → 202 Accepted (polling status endpoint)
- All errors include request correlation ID for debugging

## Cross-Cutting Concerns

**Logging:**
- Framework: Python `logging` module
- Approach: Structured logs with job_id, file_name, layer_name, timestamp included in every log entry
- Destinations: stdout (container logs) in v1; file logging optional in v2

**Validation:**
- File type validation: MIME type check + file signature verification (magic bytes)
- Field validation: Pydantic models validate extraction results (price = numeric, date = ISO-8601, etc.)
- Confidence threshold enforcement: Fields below 0.5 confidence flagged for human review (v2 feature)

**Authentication:**
- v1: None (internal tool, no multi-tenant access control)
- v2: Stateless API key validation via Authorization header

---

*Architecture analysis: 2026-03-18*
