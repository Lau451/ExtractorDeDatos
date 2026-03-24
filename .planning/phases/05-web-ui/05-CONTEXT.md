# Phase 5: Web UI - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

React SPA that exposes the complete single-file extraction workflow: upload zone → live progress indicator → inline-editable review table (with document type override) → CSV download. No new backend endpoints — all API surface is already complete after Phase 4.

</domain>

<decisions>
## Implementation Decisions

### Tech stack
- **React** with **Vite** as the build tool (fast HMR, first-class React support)
- **Tailwind CSS** for styling (utility-first, no separate stylesheets)
- **shadcn/ui** component library on top of Tailwind (copy-paste Radix UI components — Table, Input, Dropdown, Button)
- **Frontend directory:** `frontend/` at repo root, alongside `src/` (Python)

### Review table — header fields
- **Two-column table:** Label column | Value column
- Each row is one extracted field
- Powered by shadcn/ui Table component

### Review table — line items
- **Separate multi-column table below header fields** (not tabs, not collapsible)
- Each column is a line item field (e.g., Description, Qty, Unit Price, Extended Price)
- Document types without line items (tender, quotation, supplier comparison) show only the header table

### Inline editing
- **Click-to-edit:** clicking anywhere on a value cell switches it to an `<input>`
- Save on blur (click away) or Enter key
- Value cells have a subtle hover highlight (e.g., Tailwind `hover:bg-muted/50`) to signal editability
- No separate edit icon needed

### "Not found" fields
- Displayed as **muted gray italic text** (`"Not found"` in `text-muted-foreground italic`)
- User can click the cell to override — editing replaces the placeholder with real input
- No red/warning styling — "Not found" is a normal, expected state

### Processing indicator
- **Centered spinner + status text** that updates as the job progresses
- Text stages: `"Uploading..."` → `"Classifying document..."` → `"Extracting fields..."` → done
- Status text sourced from polling `GET /jobs/{id}` response (use `status` field)

### Error feedback
- **Inline error banner** replaces the spinner area on failure
- Banner shows a human-readable message derived from `error_code` (e.g., "Gemini failed to process this document" for `GEMINI_ERROR`)
- **"Try again" button** resets the UI to the upload state (no page refresh needed)
- No toast notifications — user must see the error clearly

### Restart / upload another
- After CSV download, show an **"Upload another document" button** that resets UI to upload state
- No persistent upload zone always visible — the flow is linear: upload → process → review → download → reset

### API integration — development
- **Vite dev server proxy:** all `/api/*` requests proxied to `http://localhost:8000` in `vite.config.ts`
- Zero CORS configuration needed during development

### API integration — production
- **FastAPI serves the built Vite output:** `npm run build` produces `frontend/dist/`, FastAPI mounts it as static files and serves `index.html` as the catch-all route
- One URL, one process — analyst just opens the browser after starting the FastAPI server

### Status polling
- Frontend polls `GET /jobs/{id}` every **1-2 seconds** until `status` is `complete` or `error`
- No WebSocket or SSE — polling is sufficient for 10-30s processing time

### Claude's Discretion
- Exact polling interval (1s vs 2s) and backoff strategy
- Drag-and-drop implementation details (react-dropzone or native HTML5)
- Exact component breakdown and file structure inside `frontend/`
- How PATCH requests are batched or debounced (per-field on blur vs. batch on download)
- Document type override dropdown placement and trigger timing

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — REV-01 (review table), REV-02 (inline editing), REV-03 (Not found display), REV-04 (progress indicator)
- `.planning/ROADMAP.md` §Phase 5 — Success criteria (4 items), dependency on Phase 4

### API surface (all endpoints the UI will call)
- `src/api/routes/extract.py` — POST /extract (upload, returns job ID)
- `src/api/routes/jobs.py` — GET /jobs/{id} (status polling, returns JobResponse)
- `src/api/routes/doc_type.py` — PATCH /jobs/{id}/doc-type or equivalent (document type override)
- `src/api/routes/patch.py` — PATCH /jobs/{id}/fields (user-corrected field values, deep merge)
- `src/api/routes/export.py` — GET /jobs/{id}/export (download CSV)
- `src/api/models.py` — JobResponse shape (status, extraction_result, error_code, error_message, doc_type fields)

### Error codes (must surface in UI)
- `src/core/errors.py` — Error code constants: DOCLING_TIMEOUT, DOCLING_PARSE_ERROR, GEMINI_ERROR, INVALID_FILE_TYPE, FILE_TOO_LARGE — UI maps these to human-readable messages

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- No existing frontend code — this is greenfield for the React SPA
- `src/api/models.py`: `JobResponse` is the source of truth for what the UI receives from polling; read it to understand field names before building the review table

### Established Patterns
- All API routes follow REST conventions; no GraphQL or RPC
- PATCH /jobs/{id}/fields returns the full updated `JobResponse` (not 204) — UI can refresh the review table directly from the PATCH response without a separate GET
- Error states are always in the job JSON body (not HTTP error codes for polling) — `GET /jobs/{id}` returns 200 for all states including error; actual error info is in `error_code` + `error_message`

### Integration Points
- `src/main.py`: FastAPI app instance — the static file mount for `frontend/dist/` goes here (production serving)
- `src/core/config.py`: settings object — may need a `static_dir` setting or similar for production static serving path

</code_context>

<specifics>
## Specific Ideas

No specific references — open to standard approaches for layout, animation, and component design.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 05-web-ui*
*Context gathered: 2026-03-23*
