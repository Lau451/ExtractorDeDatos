# Phase 2: Extraction Pipeline - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Full extraction pipeline for all five document types: a document classifier that routes each job to the correct per-type Pydantic schema, followed by Gemini 2.5 Flash structured extraction using `response_schema`. Includes pluggable LLM provider abstraction and user-override re-extraction. CSV generation, inline review editing, and the web UI are out of scope — Phase 2 produces a structured extraction result in the job store only.

</domain>

<decisions>
## Implementation Decisions

### Classification mechanism
- LLM-only classification — no heuristics or keyword matching
- Two-call pipeline: first call classifies the document type, second call extracts fields using the type-specific schema
- The classification call and extraction call are separate (enables user to inspect/override type between them)
- If Gemini cannot determine the document type: job completes with `doc_type="unknown"` and no extraction run — user must override via API/UI before extraction proceeds
- When user overrides `doc_type`: re-extraction runs automatically against the correct schema (no extra trigger required)

### LLM provider abstraction
- Abstract base class / Protocol pattern: define an `LLMProvider` protocol with at minimum `classify(text: str) -> str` and `extract(text: str, schema: type[BaseModel]) -> BaseModel` methods
- `GeminiProvider` is the concrete implementation; other providers implement the same protocol
- Config lives in `src/core/config.py` (existing `Settings` class via `pydantic_settings`): add `GEMINI_API_KEY`, `LLM_PROVIDER` (default: `"gemini"`), and `LLM_TIMEOUT` (seconds, default TBD by Claude)
- Swapping providers = setting `LLM_PROVIDER` env var + ensuring the named provider is registered — zero extractor code changes
- Gemini structured output: use `response_schema` parameter (native to `google-genai` SDK) — no JSON string parsing
- Failure handling: retry the failed LLM call once with a short backoff; if it fails again, job moves to `error` state with `error_code: "llm_error"` and a human-readable `error_message`

### Line item representation (Pydantic schema shape)
- Header fields + `line_items: list[LineItem]` nested in each applicable Pydantic model
- Document types with line items: Purchase Orders, Invoices, Supplier Comparisons
- Document types without line items: Tenders/RFQs, Quotations (header fields only)
- Each `LineItem` submodel is typed per document type (PO items vs. invoice items vs. supplier rows)
- Missing/unextracted fields: `Optional[...]` defaulting to `None` in the Pydantic model; serialized as `"Not found"` string in the API job response (satisfies REV-03)

### CSV layout (locked here for Phase 3 alignment)
- One row per line item — header fields repeat on every row
- Documents with no line items produce a single row
- This is the expected shape for Phase 3 CSV formatters to implement

### Claude's Discretion
- Exact field lists for PO, Invoice, and Supplier Comparison schemas (use EXT-01, EXT-04, EXT-05, EXT-06, EXT-07, EXT-08 requirements as the definitive field source)
- Tender/RFQ and Quotation field lists (schemas already defined — researcher should locate and use existing definitions)
- LLM timeout value for Gemini calls
- Short backoff duration between retry attempts
- Module layout for extraction layer (e.g., `src/extraction/`, `src/llm/`)
- Temperature and other Gemini generation config params

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — CLS-01, CLS-02, CLS-03 (classification); EXT-01 through EXT-10 (extraction + LLM abstraction) define the full acceptance criteria for Phase 2
- `.planning/ROADMAP.md` §Phase 2 — Success criteria (5 items) and dependency on Phase 1

### Existing codebase (integration points)
- `src/core/job_store.py` — `Job` dataclass that Phase 2 must extend with `doc_type` and `extraction_result` fields; existing error pattern (`error_code`, `error_message`) must be preserved
- `src/core/config.py` — `Settings` class to extend with LLM config vars; uses `pydantic_settings` with `.env` file
- `src/api/routes/jobs.py` — existing GET /jobs/{id} response shape; Phase 2 must not break this contract

### Prior phase context
- `.planning/phases/01-foundation/01-CONTEXT.md` — establishes `raw_text` (markdown from Docling) as the handoff field Phase 2 reads; error contract pattern; `google-genai` 1.68.0 SDK decision

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/core/job_store.py`: `JobStore` singleton with `asyncio.Lock`-protected methods — Phase 2 adds `set_doc_type()` and `set_extraction_result()` (or equivalent) methods following the same pattern as `set_complete()` and `set_error()`
- `src/core/config.py`: `Settings` (pydantic_settings) — extend with `gemini_api_key`, `llm_provider`, `llm_timeout` fields using the same env var pattern
- `src/ingestion/service.py`: Background task pattern (async, uses `asyncio.to_thread` for blocking calls) — extraction should follow the same background task approach

### Established Patterns
- Error state: `job.error_code` + `job.error_message` set via `job_store.set_error()` — new `llm_error` error code follows the same contract
- All blocking work (Docling calls) runs in `asyncio.to_thread()` — Gemini SDK calls should do the same if they are synchronous
- Module layout: `src/api/`, `src/ingestion/`, `src/core/` — new extraction layer should be `src/extraction/` and `src/llm/` (or similar) following the same separation

### Integration Points
- Phase 2 reads `job.raw_text` from the job store (set by Phase 1 ingestion) — this is the input to classification and extraction
- Phase 2 writes `doc_type` and structured `extraction_result` back to the job store — Phase 3 reads these to generate CSV
- GET /jobs/{id} response must include `doc_type` and `extraction_result` in the completed job payload so Phase 5 UI can display them

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches for module naming and internal implementation patterns.

</specifics>

<deferred>
## Deferred Ideas

- Schema design discussion (user opted to leave field lists to Claude's discretion per requirements): researcher should validate against EXT-01 through EXT-08 requirements
- Per-field confidence indicators — explicitly deferred to v2 (QUAL-01 in REQUIREMENTS.md)
- Existing Tender/RFQ and Quotation schema definitions — researcher should locate these in the project (mentioned in PROJECT.md as already defined)

</deferred>

---

*Phase: 02-extraction-pipeline*
*Context gathered: 2026-03-19*
