# Architecture Research

**Domain:** LLM-based document data extraction system
**Researched:** 2026-03-18
**Confidence:** HIGH (core patterns verified via official docs and multiple sources)

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Web Browser (React SPA)                  │
│  ┌───────────────┐  ┌─────────────────┐  ┌───────────────────┐  │
│  │  Upload Form  │  │  Review/Edit UI  │  │   CSV Download    │  │
│  └───────┬───────┘  └────────┬────────┘  └─────────┬─────────┘  │
└──────────┼───────────────────┼────────────────────────┼──────────┘
           │ POST /upload      │ PATCH /jobs/{id}       │ GET /export
           │                   │  (edited fields)       │
┌──────────▼───────────────────▼────────────────────────▼──────────┐
│                        FastAPI Service Layer                      │
│  ┌────────────┐  ┌─────────────┐  ┌────────────┐  ┌───────────┐  │
│  │  /upload   │  │  /jobs/{id} │  │  /export   │  │  /health  │  │
│  └─────┬──────┘  └──────┬──────┘  └─────┬──────┘  └───────────┘  │
│        │ enqueue         │ read          │ read                    │
│  ┌─────▼─────────────────▼──────────────▼─────┐                  │
│  │          In-Memory Job Store (dict)          │                  │
│  │  { job_id → { status, result, edited_data }} │                  │
│  └─────────────────────────────────────────────┘                  │
│                      ↑ asyncio BackgroundTask                     │
└───────────────────────┬───────────────────────────────────────────┘
                        │
┌───────────────────────▼───────────────────────────────────────────┐
│                     Extraction Pipeline                            │
│                                                                    │
│  ┌──────────────────┐    ┌──────────────────┐                     │
│  │  Docling Ingestion│    │  Document         │                     │
│  │  (Layer 1)        │───►│  Classifier       │                     │
│  │                  │    │  (Layer 2a)        │                     │
│  │  PDF → Markdown  │    │  (LLM or rules)    │                     │
│  │  Excel → Text    │    └────────┬───────────┘                     │
│  │  Image → OCR+Txt │             │ doc_type                        │
│  └──────────────────┘             │                                │
│                          ┌────────▼───────────┐                    │
│                          │  Field Extractor    │                    │
│                          │  (Layer 2b)         │                    │
│                          │                     │                    │
│                          │  LLM Provider       │────► Gemini API    │
│                          │  (pluggable)        │      (external)    │
│                          │                     │                    │
│                          │  Schema: Pydantic   │                    │
│                          └────────┬────────────┘                    │
│                                   │ ExtractionResult               │
│                          ┌────────▼────────────┐                   │
│                          │  CSV Formatter       │                   │
│                          │  (Layer 3)           │                   │
│                          │  Per-doc-type schema │                   │
│                          └─────────────────────┘                   │
└────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Communicates With |
|-----------|----------------|-------------------|
| React SPA | File upload, status polling, inline field editing, CSV trigger | FastAPI REST API only |
| FastAPI endpoints | Accept uploads, return job IDs, serve job status and results, serve CSV | React SPA (HTTP), Job Store (read/write), Pipeline (enqueue) |
| In-Memory Job Store | Track job lifecycle (pending → processing → complete → error), hold extraction results | FastAPI endpoints (read), Background worker (write) |
| Docling Ingestion | Convert PDF/Excel/Image/HTML to normalized Markdown+JSON representation | Pipeline worker (called directly) |
| Document Classifier | Detect document type (PO, tender, quotation, invoice, supplier comparison) from Docling output | Field Extractor (passes doc_type) |
| LLM Provider (Gemini) | Run structured field extraction using Pydantic schemas via Gemini response_json_schema | Docling output (receives text), ExtractionResult (returns) |
| LLM Provider Abstraction | Abstract base class enabling provider swap without changing extractors | Gemini provider (concrete), future OpenAI/Claude providers |
| CSV Formatter | Serialize ExtractionResult to per-document-type CSV column schema | Job Store (reads result), FastAPI export endpoint (returns bytes) |

## Recommended Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app init, CORS, startup
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── upload.py        # POST /upload — receive file, create job
│   │   │   │   ├── jobs.py          # GET /jobs/{id} — poll status
│   │   │   │   ├── export.py        # GET /jobs/{id}/export — download CSV
│   │   │   │   └── health.py        # GET /health
│   │   │   └── deps.py              # FastAPI dependency injection (job store)
│   │   ├── core/
│   │   │   ├── config.py            # Settings (Gemini API key, file size limits)
│   │   │   ├── job_store.py         # In-memory dict with thread-safe access
│   │   │   └── models.py            # Pydantic models: Job, JobStatus, ExtractionResult
│   │   ├── ingestion/
│   │   │   ├── router.py            # Route file by MIME type to correct handler
│   │   │   ├── docling_handler.py   # DocumentConverter wrapper; returns DoclingDocument
│   │   │   └── normalizer.py        # DoclingDocument → normalized text/markdown string
│   │   ├── extraction/
│   │   │   ├── classifier.py        # Detect document type from normalized text
│   │   │   ├── schemas/
│   │   │   │   ├── base.py          # ExtractionResult base Pydantic model
│   │   │   │   ├── purchase_order.py
│   │   │   │   ├── tender.py
│   │   │   │   ├── quotation.py
│   │   │   │   ├── invoice.py
│   │   │   │   └── supplier_comparison.py
│   │   │   ├── providers/
│   │   │   │   ├── base.py          # Abstract LLMProvider base class
│   │   │   │   └── gemini.py        # GeminiProvider: response_json_schema + Pydantic
│   │   │   └── extractor.py         # Orchestrate: pick schema + provider → ExtractionResult
│   │   ├── export/
│   │   │   ├── formatters/
│   │   │   │   ├── base.py          # Abstract CSVFormatter
│   │   │   │   ├── purchase_order.py
│   │   │   │   ├── tender.py
│   │   │   │   ├── quotation.py
│   │   │   │   ├── invoice.py
│   │   │   │   └── supplier_comparison.py
│   │   │   └── csv_export.py        # Dispatch to correct formatter, return CSV bytes
│   │   └── pipeline/
│   │       └── worker.py            # Orchestrate ingestion → classify → extract → store
│   ├── tests/
│   └── pyproject.toml
└── frontend/
    ├── src/
    │   ├── main.tsx                 # React entry point
    │   ├── App.tsx                  # Top-level routing/state
    │   ├── api/
    │   │   └── client.ts            # Typed fetch wrapper (upload, poll, patch, download)
    │   ├── components/
    │   │   ├── UploadZone.tsx       # Drag-and-drop file upload
    │   │   ├── StatusPoller.tsx     # Poll GET /jobs/{id} until complete
    │   │   ├── ExtractionTable.tsx  # Inline-editable table of extracted fields
    │   │   ├── FieldCell.tsx        # Single editable cell (click-to-edit pattern)
    │   │   └── DownloadButton.tsx   # Trigger GET /jobs/{id}/export
    │   ├── hooks/
    │   │   ├── useJobPolling.ts     # Encapsulate polling interval + abort
    │   │   └── useExtraction.ts     # State: fields, edits, status
    │   └── types/
    │       └── extraction.ts        # TypeScript mirrors of backend Pydantic schemas
    ├── index.html
    ├── vite.config.ts               # Proxy /api → localhost:8000
    └── package.json
```

### Structure Rationale

- **backend/app/ingestion/:** Isolated from extraction. Docling is a heavy dependency; keeping it in one module makes it easy to swap or mock in tests.
- **backend/app/extraction/schemas/:** One Pydantic model per document type. Gemini's `response_json_schema` requires a concrete schema, not a union type — per-type files avoid complex conditional logic.
- **backend/app/extraction/providers/:** Abstract base allows Gemini to be replaced (e.g., GPT-4o, Claude) by adding a new file. The extractor module never imports Gemini directly.
- **backend/app/pipeline/worker.py:** Single orchestration point. Background task calls this; it owns the sequencing and writes final result to the job store.
- **frontend/src/api/client.ts:** All HTTP calls centralized here. React components never call `fetch` directly — they use typed functions. This makes the polling/edit/download flow testable.
- **frontend/src/components/ExtractionTable.tsx:** The review/edit view is one component. Field edits are local state until the user clicks "Download CSV", at which point they are sent via PATCH before the export is triggered.

## Architectural Patterns

### Pattern 1: Async Job with Status Polling

**What:** Upload endpoint immediately returns a `job_id`. A FastAPI `BackgroundTask` runs the pipeline asynchronously. Frontend polls `GET /jobs/{id}` on a fixed interval (e.g., every 1.5s) until status is `complete` or `error`.

**When to use:** Any operation that takes more than ~500ms (Docling parse + Gemini API call easily takes 3-15 seconds). Polling avoids HTTP timeout issues and keeps the UI responsive.

**Trade-offs:** Polling adds latency (up to one interval after completion). For v1 single-user tool, this is acceptable. Upgrade path: WebSockets or Server-Sent Events if low-latency notification matters.

**Example:**
```python
# backend/app/api/routes/upload.py
@router.post("/upload")
async def upload_document(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    job_store: JobStore = Depends(get_job_store),
):
    job_id = str(uuid4())
    job_store.create(job_id)
    background_tasks.add_task(run_pipeline, job_id, file, job_store)
    return {"job_id": job_id, "status": "pending"}
```

### Pattern 2: LLM Provider Abstraction (Abstract Base Class)

**What:** Define an abstract `LLMProvider` with a single method `extract(text: str, schema: type[BaseModel]) -> BaseModel`. Concrete implementations (`GeminiProvider`) implement the contract. The `Extractor` class receives a provider via constructor injection.

**When to use:** When the LLM vendor is a project requirement but may change. Gemini is v1 primary; the abstraction costs one extra file and zero runtime overhead.

**Trade-offs:** Adds one indirection layer. Overkill if you are certain the LLM will never change. Worth it here because it is already a stated project decision.

**Example:**
```python
# backend/app/extraction/providers/base.py
from abc import ABC, abstractmethod
from pydantic import BaseModel

class LLMProvider(ABC):
    @abstractmethod
    def extract(self, text: str, schema: type[BaseModel]) -> BaseModel:
        ...

# backend/app/extraction/providers/gemini.py
class GeminiProvider(LLMProvider):
    def extract(self, text: str, schema: type[BaseModel]) -> BaseModel:
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=text,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": schema.model_json_schema(),
            },
        )
        return schema.model_validate_json(response.text)
```

### Pattern 3: Per-Document-Type Schema Dispatch

**What:** After classification, look up the correct Pydantic schema and CSV formatter in a registry dict keyed by `DocumentType` enum. No `if/elif` chains in the extractor.

**When to use:** When there are N document types each requiring different fields. A registry keeps the extractor and formatter closed to modification when new types are added.

**Trade-offs:** Requires discipline to keep registry and schema files in sync. The alternative (if/elif) is simpler for 5 types but becomes unmanageable at 10+.

**Example:**
```python
# backend/app/extraction/extractor.py
SCHEMA_REGISTRY: dict[DocumentType, type[BaseModel]] = {
    DocumentType.PURCHASE_ORDER: PurchaseOrderSchema,
    DocumentType.TENDER: TenderSchema,
    DocumentType.QUOTATION: QuotationSchema,
    DocumentType.INVOICE: InvoiceSchema,
    DocumentType.SUPPLIER_COMPARISON: SupplierComparisonSchema,
}

def extract(text: str, doc_type: DocumentType, provider: LLMProvider) -> BaseModel:
    schema = SCHEMA_REGISTRY[doc_type]
    return provider.extract(text, schema)
```

### Pattern 4: Docling as Normalization Gate

**What:** All file formats (PDF, Excel, image, HTML) enter the pipeline through Docling's `DocumentConverter`. The output is always a `DoclingDocument`, from which you export structured Markdown. Everything downstream only sees Markdown text — no format-specific logic leaks into the extractor or classifier.

**When to use:** Always, for this project. Docling handles the format complexity; the rest of the pipeline stays format-agnostic.

**Trade-offs:** Docling is a large dependency with ML model weights. Cold start on first run is slow (model loading). Subsequent calls are fast. Mitigation: warm up on server startup.

**Example:**
```python
# backend/app/ingestion/docling_handler.py
from docling.document_converter import DocumentConverter

_converter = DocumentConverter()  # initialized once at module load

def ingest(file_path: str) -> str:
    result = _converter.convert(file_path)
    return result.document.export_to_markdown()
```

## Data Flow

### Upload-to-CSV Flow (Primary Path)

```
User selects file
    ↓
POST /upload (multipart/form-data)
    ↓
FastAPI: save temp file, create job_id, enqueue BackgroundTask
    ↓ (immediate response)
{"job_id": "abc123", "status": "pending"}
    ↓
[Background] worker.py starts
    ↓
Docling DocumentConverter.convert(file_path) → DoclingDocument
    ↓
DoclingDocument.export_to_markdown() → normalized_text: str
    ↓
classifier.detect(normalized_text) → DocumentType
    ↓
SCHEMA_REGISTRY[doc_type] → schema: type[BaseModel]
    ↓
GeminiProvider.extract(normalized_text, schema) → ExtractionResult
    ↓
job_store.set_result(job_id, extraction_result)
job_store.set_status(job_id, "complete")
    ↓
[Frontend polling] GET /jobs/abc123 → {status: "complete", fields: [...]}
    ↓
User reviews ExtractionTable, edits cells in place
    ↓
User clicks "Download CSV"
    ↓
PATCH /jobs/abc123/fields {edited_fields: {...}}  [if edits exist]
    ↓
GET /jobs/abc123/export → CSV bytes (Content-Disposition: attachment)
    ↓
Browser downloads file
```

### Inline Edit Flow (Frontend State Management)

```
ExtractionTable renders fields from job result
    ↓
User double-clicks cell → FieldCell enters edit mode (local React state)
    ↓
User types new value → local state updated
    ↓
User blurs or presses Enter → cell exits edit mode, parent state updated
    ↓ (no API call yet — edits accumulate in useExtraction hook)
User clicks "Download CSV"
    ↓
useExtraction flushes edits: PATCH /jobs/{id}/fields
    ↓
Server merges edits into stored ExtractionResult
    ↓
GET /jobs/{id}/export with merged data → CSV
```

**Key design decision:** Edits are held in frontend state until export is triggered. This avoids chatty PATCH calls on every keystroke and simplifies the backend (no partial-update complexity during a live edit session).

### Error Flow

```
Background task fails (Docling parse error / Gemini timeout)
    ↓
job_store.set_status(job_id, "error")
job_store.set_error(job_id, error_message)
    ↓
GET /jobs/{id} → {status: "error", error: "..."}
    ↓
Frontend stops polling, shows error banner with message
    ↓
User can re-upload (no retry endpoint in v1)
```

## Frontend / Backend Split

| Concern | Owner | Rationale |
|---------|-------|-----------|
| File format parsing | Backend (Docling) | CPU/memory intensive; ML model weights not in browser |
| Document classification | Backend (LLM) | Requires Gemini API key; cannot expose to browser |
| Field extraction | Backend (LLM) | Same as above |
| CSV generation | Backend | Schema logic is server-authoritative |
| Field edit state | Frontend | Ephemeral UX state; no server round-trip needed per keystroke |
| Edit persistence before export | Backend | Server owns the ExtractionResult; frontend sends final edits once |
| Polling interval logic | Frontend | UI concern; backend is stateless about polling frequency |
| Job status display | Frontend | Derived from polling responses |

## Build Order (Phase Dependencies)

Build in this sequence — each layer depends on the one before:

```
Phase 1: Core Ingestion
    Docling handler + file type router + normalizer
    ↓ (unblocks all downstream)

Phase 2: Extraction Pipeline
    LLM provider abstraction + Gemini provider
    Document classifier
    Per-type Pydantic schemas
    Schema registry + extractor orchestrator
    ↓ (produces ExtractionResult — unblocks export and API)

Phase 3: CSV Export
    Per-type CSV formatters
    Export dispatcher
    ↓ (completes pipeline — unblocks full API integration)

Phase 4: FastAPI Service Layer
    Job store + background worker
    Upload / job status / export / health endpoints
    ↓ (exposes full pipeline as HTTP — unblocks frontend)

Phase 5: Web UI
    React SPA: upload zone, status poller
    ExtractionTable with inline editing
    Download flow with edit flush
```

**Why this order:**
- Docling ingestion must come first: it is the input contract for everything else. Cannot write extraction schemas without knowing what text looks like.
- Schemas before provider: Gemini's `response_json_schema` requires a concrete Pydantic model. Define schemas first, then wire the provider.
- Export before API: the API endpoints delegate to the export layer. Building export in isolation (with test fixtures) avoids blocking on a running server.
- Frontend last: the React SPA only needs the API contract (endpoint paths + response shapes). Can be developed against a running backend or with mocked responses.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1-5 concurrent users | Current design is sufficient. FastAPI's async I/O + Gemini's API handles this. In-memory job store is fine. |
| 10-50 concurrent users | Gemini rate limits become the bottleneck. Add a semaphore to cap concurrent LLM calls. Consider Redis for job store to survive restarts. |
| 50+ concurrent users | Replace BackgroundTasks with a real task queue (Celery + Redis or ARQ). Move temp file storage to object storage (S3/GCS). Multiple FastAPI workers behind a load balancer. |

**First bottleneck:** Gemini API rate limits (requests-per-minute). Mitigation: asyncio Semaphore limiting concurrent LLM calls to N (start with 5).

**Second bottleneck:** Docling model loading. Each worker process loads ML model weights independently. Mitigation: pre-warm on startup; in multi-worker deployments, this multiplies memory use.

## Anti-Patterns

### Anti-Pattern 1: Format-Specific Logic in the Extractor

**What people do:** Write `if file.extension == ".pdf": ...` checks inside the extractor or classifier.
**Why it's wrong:** Breaks the single responsibility of each layer. Makes it impossible to test the extractor without a real file.
**Do this instead:** Docling normalizes all formats to Markdown before any other component sees the data. The extractor receives only `text: str`.

### Anti-Pattern 2: One Monolithic Extraction Schema

**What people do:** Define a single `ExtractionResult` model with all fields from all document types (most fields Optional), and let the LLM populate what it can.
**Why it's wrong:** Gemini's structured output (`response_json_schema`) works best with tight, concrete schemas. A union schema with 40+ optional fields produces poor extraction quality and makes CSV column ordering ambiguous.
**Do this instead:** One Pydantic schema per document type. Classify first, then pass the narrow schema to the LLM.

### Anti-Pattern 3: Blocking the FastAPI Event Loop with Docling

**What people do:** Call `DocumentConverter.convert()` directly inside an `async def` endpoint handler.
**Why it's wrong:** Docling is CPU-bound (runs ML models synchronously). Calling it in an async function blocks the entire FastAPI event loop, causing all other requests to freeze.
**Do this instead:** Run Docling inside a BackgroundTask (already off the event loop thread) or use `asyncio.to_thread()` to run it in a thread pool executor.

```python
# Correct: run Docling in thread pool from async context
normalized_text = await asyncio.to_thread(ingest, file_path)
```

### Anti-Pattern 4: Storing Edits Only in Frontend State

**What people do:** Apply user edits to the local React state and never send them to the server. Generate the CSV entirely in the browser from local state.
**Why it's wrong:** The server holds the authoritative ExtractionResult and the CSV schema. Client-side CSV generation duplicates schema logic and drifts from the server's canonical column ordering.
**Do this instead:** Frontend holds edits locally for UX responsiveness. On export, send edits to the server via PATCH, then request the CSV from the server. Server owns CSV generation.

### Anti-Pattern 5: Initializing DocumentConverter per Request

**What people do:** Instantiate `DocumentConverter()` inside the route handler or worker function for each request.
**Why it's wrong:** Docling loads ML model weights (DocLayNet, TableFormer) on construction. This adds 5-20 seconds of cold-start latency per request.
**Do this instead:** Initialize `DocumentConverter` once at module level or in the FastAPI `lifespan` startup hook. Reuse the instance across all requests.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Gemini 2.5 Flash | `google-genai` SDK, `response_json_schema` with Pydantic | API key via env var `GEMINI_API_KEY`. Use `response_mime_type: application/json` + `response_json_schema: Schema.model_json_schema()`. Validate response with `Schema.model_validate_json()`. |
| Docling (local library) | `DocumentConverter().convert(path)` → `.export_to_markdown()` | No network call; runs locally. Initialize once. Handles PDF (native + OCR), Excel, PNG, HTML natively. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| FastAPI routes ↔ Job Store | Direct Python dict access via dependency injection | Use `threading.Lock` or `asyncio.Lock` to protect concurrent writes |
| FastAPI routes ↔ Pipeline Worker | FastAPI `BackgroundTasks.add_task()` | Worker runs in same process, separate thread. Sufficient for v1. |
| Pipeline Worker ↔ Ingestion | Direct Python function call | `ingest(file_path: str) -> str` — synchronous, run via `asyncio.to_thread` |
| Pipeline Worker ↔ Extraction | Direct Python function call | `extract(text, doc_type, provider) -> BaseModel` |
| Pipeline Worker ↔ Job Store | Direct dict write | Worker writes status updates and final result |
| FastAPI export endpoint ↔ CSV Formatter | Direct Python function call | `format(result: BaseModel, doc_type: DocumentType) -> bytes` |
| React frontend ↔ FastAPI | HTTP REST over `localhost` (dev: Vite proxy to port 8000) | All calls go through `frontend/src/api/client.ts` |

## Sources

- [Docling GitHub — docling-project/docling](https://github.com/docling-project/docling) — pipeline architecture, supported formats, DocumentConverter API (HIGH confidence)
- [Docling official site](https://www.docling.ai/) — output formats (Markdown, JSON, HTML, DocTags) (HIGH confidence)
- [Gemini Structured Output — Google AI for Developers](https://ai.google.dev/gemini-api/docs/structured-output) — `response_json_schema`, Pydantic integration (HIGH confidence)
- [FastAPI Background Tasks — Official Docs](https://fastapi.tiangolo.com/tutorial/background-tasks/) — BackgroundTasks pattern (HIGH confidence)
- [FastAPI Long-Running Jobs — Leapcell](https://leapcell.io/blog/managing-background-tasks-and-long-running-operations-in-fastapi) — job ID + polling pattern (MEDIUM confidence)
- [LLM Document Extraction Architecture — Unstract Blog](https://unstract.com/blog/comparing-approaches-for-using-llms-for-structured-data-extraction-from-pdfs/) — extraction system component overview (MEDIUM confidence)
- [Modern Full-Stack FastAPI + React + Vite — DEV Community](https://dev.to/stamigos/modern-full-stack-setup-fastapi-reactjs-vite-mui-with-typescript-2mef) — project structure conventions (MEDIUM confidence)
- [Material React Table — Inline Cell Editing](https://www.material-react-table.com/docs/examples/editing-crud-inline-cell) — inline editing table patterns (MEDIUM confidence)

---
*Architecture research for: LLM-based document data extraction system (DocExtract)*
*Researched: 2026-03-18*
