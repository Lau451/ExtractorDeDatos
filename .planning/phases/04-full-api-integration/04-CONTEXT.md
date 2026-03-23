# Phase 4: Full API Integration - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Complete the REST API surface: PATCH endpoint for user-corrected field values that merges edits into `extraction_result` so the exported CSV reflects corrections; TTL-based job cleanup; and structured error states. No web UI (Phase 5).

</domain>

<decisions>
## Implementation Decisions

### Edit storage strategy
- User edits are merged **directly into `extraction_result`** (overwrite in place) — no separate `user_edits` field
- Merge is **deep** (recursive): nested dicts and list elements like `line_items` are merged field-by-field, not replaced wholesale
- Original extraction values are not preserved after a PATCH — each PATCH produces the new canonical state

### PATCH request shape
- Endpoint: `PATCH /jobs/{id}/fields`
- Request body: flat field map `{"fields": {"field_name": "new_value"}}`
- Semantics: **full replacement** — the `fields` dict in the request is deep-merged into the current `extraction_result`; any fields not included in the request retain their current value (already baked into `extraction_result`)
- On success: returns the **full updated `JobResponse`** (not 204) so the client can confirm applied edits immediately
- Error cases: 404 if job not found, 409 if job is not in `complete` state (can't edit mid-processing)

### Error taxonomy
- **Distinct error codes per root cause** — Phase 5 UI can show specific messages per code
- Error codes to define:
  - `DOCLING_TIMEOUT` — document parsing timed out
  - `DOCLING_PARSE_ERROR` — Docling failed to parse the file
  - `GEMINI_ERROR` — LLM call failed or returned invalid response
  - `INVALID_FILE_TYPE` — file extension/MIME not in supported list
  - `FILE_TOO_LARGE` — file exceeds size limit (if applicable)
- `error_code` and `error_message` already exist on the `Job` dataclass — this phase expands the vocabulary, not the storage model

### TTL job cleanup
- **Background asyncio task** running periodically (not lazy/on-access)
- **TTL: 1 hour** from job creation
- Cleanup interval: Claude's discretion (e.g., every 5 minutes)
- Expired jobs are removed silently — subsequent requests return 404 (same as unknown job ID)

### Claude's Discretion
- Deep merge algorithm implementation (handle dict, list, scalar)
- Cleanup task startup (lifespan context vs. startup event)
- Cleanup interval frequency
- Whether to validate field names against the known schema or accept any key

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — API-03 (PATCH /jobs/{id}/fields), REV-05 (edits reflected in CSV)
- `.planning/ROADMAP.md` §Phase 4 — Success criteria (2 items), dependency on Phase 3

### Existing job infrastructure
- `src/core/job_store.py` — `Job` dataclass (fields: `extraction_result`, `error_code`, `error_message`, `status`), `JobStore` methods (`set_extraction_result`, `set_error`, `set_status`)
- `src/api/models.py` — `JobResponse`, `ErrorResponse` — PATCH response should reuse `JobResponse`
- `src/api/routes/jobs.py` — Existing route patterns; PATCH route follows same conventions
- `src/api/routes/export.py` — Export route already merges from `extraction_result`; any deep-merge must maintain export compatibility

### Phase 3 export contract
- `.planning/phases/03-csv-export/03-CONTEXT.md` — Export reads `job.extraction_result` directly; deep-merged values must remain a valid serialized Pydantic model dict

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/core/job_store.py`: `JobStore` already has `set_extraction_result()` — PATCH needs a new `patch_extraction_result()` method that does deep merge
- `src/api/models.py`: `JobResponse` is the return type — PATCH returns the same model
- `src/main.py`: FastAPI app instance — background cleanup task attaches here (lifespan or startup event)

### Established Patterns
- Error pattern: `error_code` + `error_message` set via `job_store.set_error()` — Phase 4 expands the error_code vocabulary without changing the storage pattern
- Route pattern: separate files per concern in `src/api/routes/` — PATCH gets its own route or extends `jobs.py`
- Async pattern: all `JobStore` methods use `asyncio.Lock` — new `patch_extraction_result()` follows the same pattern

### Integration Points
- PATCH writes to `job.extraction_result` (dict) — `GET /jobs/{id}/export` reads this same dict; deep merge must not break CSV formatter expectations
- Background cleanup task removes entries from `job_store._store` — needs to acquire the same `asyncio.Lock`

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches for deep merge and background task implementation.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 04-full-api-integration*
*Context gathered: 2026-03-23*
