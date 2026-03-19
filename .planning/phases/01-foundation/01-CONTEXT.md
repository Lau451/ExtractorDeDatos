# Phase 1: Foundation - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

A running FastAPI server that accepts any supported file format (PDF, XLSX/XLS, PNG/JPG, HTML), safely ingests it via Docling with OCR fallback and 60-second timeout protection, stores the job in a race-condition-safe in-memory store, and exposes POST /extract, GET /jobs/{id}, and GET /health endpoints. Document classification and LLM extraction are out of scope — Phase 1 produces ingested text only.

</domain>

<decisions>
## Implementation Decisions

### Docling output format
- Export format: structured markdown via `export_to_markdown()` — tables become markdown tables, headings preserved
- This is what gets stored in the job result and handed off to Phase 2 (LLM extraction)
- Field key in job result: `raw_text` (contains markdown string)

### Excel ingestion
- Extract all sheets as separate markdown table sections
- Multi-sheet workbooks are fully captured — no sheet is skipped

### OCR strategy
- OCR runs as fallback only: use Docling's native text extraction first
- Fall back to OCR when no text layer is detected or extracted text is below a minimum character count
- Never force OCR on text-based PDFs (performance cost not justified)

### Docling timeout
- Hard timeout: 60 seconds per document
- If exceeded, job moves to `error` state with `error_code: "docling_timeout"`

### Job response schema
- Successful completed job includes `raw_text` (markdown string from Docling) in result
- Failed job includes `error_code` + `error_message` (see error contract below)

### Error response contract
- JSON error body shape: `{"error": "<error_code>", "message": "<human-readable description>"}`
- HTTP status mapping:
  - `400` → unsupported file type or invalid request (job never created)
  - `404` → job ID not found
  - `408` → Docling processing timeout
  - `422` → corrupt or unreadable file (file accepted but unparseable)
  - `500` → unexpected server error
- Failed job state response from GET /jobs/{id}: `{"status": "error", "error_code": "docling_timeout", "error_message": "Document processing exceeded 60s timeout"}`
- Error codes: `unsupported_file_type`, `docling_timeout`, `docling_parse_error`, `job_not_found`

### Claude's Discretion
- Project directory layout (module structure within src/)
- Minimum character count threshold for OCR fallback trigger
- Exact job store data structure (fields beyond status/result/error)
- asyncio.Lock implementation pattern
- uvicorn startup configuration

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — ING-01 through ING-06, API-01, API-02, API-05 define the acceptance criteria for Phase 1
- `.planning/ROADMAP.md` §Phase 1 — Success criteria (5 items) and dependency chain

### Architecture
- `.planning/codebase/ARCHITECTURE.md` — Layer 1 (ingestion) design, job store pattern, entry points
- `.planning/codebase/CONCERNS.md` §Phase-Specific Risks (Phase 1) — OCR reliability risks and mitigation
- `.planning/codebase/STACK.md` — Note: STACK.md references older stack (pdfplumber/Tesseract); STATE.md decision overrides: Docling is the unified parser

### Key override from STATE.md
- Use `Docling` as the unified document parser for all formats (replaces pdfplumber + pytesseract chain documented in STACK.md)
- Always read `UploadFile` bytes in endpoint before passing to `BackgroundTask` (FastAPI v0.106+ lifecycle requirement)
- In-memory job store with `asyncio.Lock` for race-condition safety

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — greenfield project. No existing source code.

### Established Patterns
- Architecture maps define the intended module layout: `src/api/`, `src/ingestion/`, `src/core/`
- Job lifecycle pattern defined in ARCHITECTURE.md: pending → processing → complete | error
- File routing pattern: factory/registry dispatching by extension to per-format handler

### Integration Points
- Phase 2 will read `job.result.raw_text` (markdown string) from the job store — this is the handoff contract
- Phase 5 (React SPA) will poll GET /jobs/{id} — response schema must be stable
- GET /health must be available for Phase 5 startup checks

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches for project layout and internal implementation patterns.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-foundation*
*Context gathered: 2026-03-18*
