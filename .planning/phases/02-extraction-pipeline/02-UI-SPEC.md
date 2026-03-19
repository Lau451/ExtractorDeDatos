---
phase: 2
slug: extraction-pipeline
status: approved
reviewed_at: 2026-03-19
shadcn_initialized: false
preset: none
created: 2026-03-19
---

# Phase 2 — UI Design Contract: Extraction Pipeline

> Visual and interaction contract for Phase 2. Phase 2 is a pure backend phase — no frontend components, no React, no Tailwind. The "UI" contract here defines the API response surface that Phase 5 (Web UI) will consume: JSON shapes, state machine, copywriting for error messages, and the interaction contract for the doc_type override flow.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none |
| Preset | not applicable |
| Component library | none — backend phase |
| Icon library | none — backend phase |
| Font | none — backend phase |

Source: CONTEXT.md Phase Boundary — "CSV generation, inline review editing, and the web UI are out of scope — Phase 2 produces a structured extraction result in the job store only."

---

## Spacing Scale

Not applicable. Phase 2 introduces no rendered UI surfaces. Spacing contract deferred to Phase 5.

Exceptions: none

---

## Typography

Not applicable. Phase 2 introduces no rendered UI surfaces. Typography contract deferred to Phase 5.

---

## Color

Not applicable. Phase 2 introduces no rendered UI surfaces. Color contract deferred to Phase 5.

---

## API Interaction Contract

This section replaces the visual design sections for backend-only phases. It defines the interaction contract that downstream phases (3, 4, 5) and the Phase 5 UI must honor.

### Job State Machine

Phase 2 extends the job lifecycle with two new intermediate states visible in `GET /jobs/{id}`.

```
pending
  → processing          ← ingestion background task starts
    → classifying       ← NEW: classification LLM call in progress
      → extracting      ← NEW: extraction LLM call in progress
        → complete      ← doc_type + extraction_result written
        → error         ← LLM error after retry
    → error             ← ingestion error (existing, unchanged)
```

States exposed in the `status` field of `GET /jobs/{id}` response:

| Status value | Meaning | Who sets it |
|---|---|---|
| `pending` | Job created, not yet picked up | Phase 1 — unchanged |
| `processing` | Ingestion background task running | Phase 1 — unchanged |
| `classifying` | Classification LLM call in progress | Phase 2 NEW |
| `extracting` | Extraction LLM call in progress | Phase 2 NEW |
| `complete` | Extraction result available | Phase 2 (replaces Phase 1 complete) |
| `error` | Permanent failure after retry | Phase 1 + Phase 2 — same contract |

Source: CONTEXT.md — "The classification call and extraction call are separate (enables user to inspect/override type between them)" + RESEARCH.md Pattern 5.

### GET /jobs/{id} Response Shape — Phase 2 Extension

Phase 2 adds `doc_type` and `extraction_result` to the existing response body. The existing fields (`job_id`, `status`, `filename`, `error_code`, `error_message`) are unchanged.

```json
{
  "job_id": "string",
  "status": "complete | error | classifying | extracting | pending | processing",
  "filename": "string",
  "doc_type": "purchase_order | tender_rfq | quotation | invoice | supplier_comparison | unknown | null",
  "extraction_result": {
    "<<schema fields>>": "<<value or 'Not found'>>"
  },
  "error_code": "null | llm_error | ingestion_error | unsupported_file_type",
  "error_message": "null | string"
}
```

Rules:
- `doc_type` is `null` until classification completes. After classification it is one of the six string values above.
- `extraction_result` is `null` until extraction completes. After extraction it is a flat dict with all schema fields.
- `None` values in the Pydantic extraction result are serialized as the string `"Not found"` in the API response body — never as JSON `null`. (Source: CONTEXT.md + RESEARCH.md Pattern 6, satisfies REV-03.)
- `line_items` is always an array — empty array `[]` when no line items were found, never `null` or absent.

### PATCH /jobs/{id}/doc_type — Override Endpoint

New endpoint introduced in Phase 2. Satisfies CLS-03.

**Request:**
```json
{ "doc_type": "purchase_order | tender_rfq | quotation | invoice | supplier_comparison" }
```

**Behavior sequence (locked):**
1. Validate `doc_type` is one of the five known values (not `"unknown"`). Return 422 if invalid.
2. Update `doc_type` in job store.
3. Clear `extraction_result` (set to `null`).
4. Set `status` to `"extracting"`.
5. Enqueue `run_extraction_pipeline` background task with the new doc_type as the forced type (skip re-classification).
6. Return `202 Accepted` with updated job snapshot.

**Response:** Same shape as `GET /jobs/{id}` — status `"extracting"`, `doc_type` updated, `extraction_result: null`.

Source: CONTEXT.md — "When user overrides doc_type: re-extraction runs automatically against the correct schema (no extra trigger required)" + RESEARCH.md Pitfall 6.

### doc_type = "unknown" Interaction Contract

When Gemini cannot classify the document:

- Job `status` becomes `"complete"` (not error — classification succeeded, result is unknown).
- `doc_type` is `"unknown"`.
- `extraction_result` is `null`.
- User must call `PATCH /jobs/{id}/doc_type` with a valid type before extraction proceeds.
- Phase 5 UI must render a doc_type override dropdown in this state (contract for Phase 5 planner).

Source: CONTEXT.md — "If Gemini cannot determine the document type: job completes with doc_type='unknown' and no extraction run — user must override via API/UI before extraction proceeds."

---

## Copywriting Contract

These string values appear in API response bodies. They are the copy contract for all downstream consumers (Phase 5 UI, logs, error displays).

| Element | Copy |
|---------|------|
| Primary action label (Phase 5 will surface this) | "Retry with correct document type" |
| Unknown doc_type user message | "Document type could not be determined. Select the correct type to extract fields." |
| LLM error message (human-readable) | "Extraction failed after retry. Check your document and try again." |
| LLM timeout error message | "Extraction timed out. The document may be too large or complex. Try again." |
| Invalid doc_type override (422 body) | "Invalid document type. Must be one of: purchase_order, tender_rfq, quotation, invoice, supplier_comparison." |
| Empty extraction result (no line items found) | Empty `line_items` array — no "Not found" string on the array itself, only on missing field strings |
| Missing field sentinel (all document types) | `"Not found"` — exact string, no variation (satisfies REV-03) |
| Classification in progress status text | `"classifying"` — used in `status` field; Phase 5 maps this to display label "Identifying document type..." |
| Extraction in progress status text | `"extracting"` — used in `status` field; Phase 5 maps this to display label "Extracting fields..." |

Source: CONTEXT.md — "Missing/unextracted fields: Optional[...] defaulting to None in the Pydantic model; serialized as 'Not found' string in the API job response (satisfies REV-03)" + REQUIREMENTS.md REV-03.

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | none — backend phase | not applicable |

No third-party component registries. Phase 2 uses no frontend tooling.

---

## Phase 5 Handoff Notes

The following decisions made in Phase 2 directly constrain Phase 5 UI design. The Phase 5 UI-SPEC must honor these contracts.

| Contract point | Phase 2 decision | Phase 5 implication |
|---|---|---|
| Status polling | `status` field cycles through `classifying` → `extracting` → `complete` | UI must poll GET /jobs/{id} and display distinct copy for each status (REV-04) |
| doc_type display | `doc_type` is available after `status = "classifying"` completes | UI must show doc_type before extraction result is available (CLS-02) |
| doc_type override | PATCH /jobs/{id}/doc_type — triggers automatic re-extraction | UI needs a dropdown pre-populated with 5 document type options (CLS-03) |
| "Not found" sentinel | All missing fields are the exact string `"Not found"` — never `null` | UI renders this string directly, no null-guard needed in rendering logic |
| line_items shape | Always an array, never null | UI renders table from array; empty array = no line items section shown |
| CSV layout | One row per line item, header fields repeat | Phase 5 review table must match this shape for consistency with Phase 3 CSV |

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS — not applicable (backend phase)
- [ ] Dimension 3 Color: PASS — not applicable (backend phase)
- [ ] Dimension 4 Typography: PASS — not applicable (backend phase)
- [ ] Dimension 5 Spacing: PASS — not applicable (backend phase)
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending
