# Phase 3: CSV Export - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Per-type CSV formatters that serialize a validated ExtractionResult to a UTF-8-with-BOM CSV with schema-correct column ordering, exposed via GET /jobs/{id}/export. This phase produces the export layer only — no user editing (Phase 4), no web UI (Phase 5).

</domain>

<decisions>
## Implementation Decisions

### Missing data handling
- Missing/unextracted fields render as **empty cells** in the CSV (not "Not found" or "N/A")
- The API response continues to show "Not found" for the UI — CSV deliberately differs for Excel usability
- Empty cells allow Excel users to filter blanks and process numeric columns without string cleanup

### Export endpoint behavior
- `GET /jobs/{id}/export` returns the CSV file with `Content-Disposition: attachment; filename="job_{id}_{doc_type}.csv"`
- Filename convention: `job_{job_id}_{doc_type}.csv` (e.g., `job_abc123_purchase_order.csv`)
- If job is not exportable (still processing, failed, doc_type=unknown): return **HTTP 409 Conflict** with a JSON body explaining why
- If job does not exist: return HTTP 404 (existing pattern)
- Content-Type: `text/csv; charset=utf-8`

### Line item row layout
- **Header-only doc types** (Tender/RFQ, Quotation): CSV contains only header columns — no empty line-item columns. Each doc type gets its own clean, distinct column schema (per EXP-04)
- **Line-item doc types** (PO, Invoice, Supplier Comparison): one row per line item with header fields **repeated on every row** (denormalized). Every row is self-contained for filtering/sorting/pivoting
- Documents with no extracted line items but that have a line-item schema: produce a single row with header fields and empty line-item columns

### CSV layout (carried from Phase 2)
- One row per line item — header fields repeat on every row
- Documents with no line items produce a single row
- UTF-8 with BOM encoding (utf-8-sig) for Excel compatibility

### Claude's Discretion
- Column ordering within each doc type's CSV schema
- Column header labels (human-readable vs field names)
- CSV formatter module structure (one formatter per type vs registry pattern)
- CSV delimiter (standard comma expected, but implementation detail)
- How to handle edge case of zero line items in a line-item doc type

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — EXP-01 (download CSV), EXP-02 (column order matches schema), EXP-03 (UTF-8 with BOM), EXP-04 (distinct CSV per doc type), API-04 (GET /jobs/{id}/export endpoint)
- `.planning/ROADMAP.md` §Phase 3 — Success criteria (4 items) and dependency on Phase 2

### Extraction schemas (CSV source data)
- `src/extraction/schemas/purchase_order.py` — PurchaseOrderResult + POLineItem fields (10 header + 7 line item fields)
- `src/extraction/schemas/invoice.py` — InvoiceResult + InvoiceLineItem fields (13 header + 6 line item fields)
- `src/extraction/schemas/supplier_comparison.py` — SupplierComparisonResult + SupplierRow fields (6 header + 10 line item fields)
- `src/extraction/schemas/tender_rfq.py` — TenderRFQResult fields (8 header-only fields)
- `src/extraction/schemas/quotation.py` — QuotationResult fields (12 header-only fields)
- `src/extraction/schemas/registry.py` — SCHEMA_REGISTRY mapping doc_type string to Pydantic model class

### Phase 2 context (CSV layout decision)
- `.planning/phases/02-extraction-pipeline/02-CONTEXT.md` §CSV layout — Locked decision: one row per line item, header fields repeat

### Integration points
- `src/core/job_store.py` — Job dataclass with `extraction_result` (dict from .model_dump()) and `doc_type` fields
- `src/api/routes/jobs.py` — Existing route patterns; new export route follows same conventions

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/extraction/schemas/registry.py`: SCHEMA_REGISTRY maps doc_type to Pydantic model — CSV formatters can use the same registry pattern for type-to-formatter routing
- All 5 Pydantic schemas define field order via class attribute order — CSV column order can derive from model field iteration
- `src/core/config.py`: Settings class available if any CSV-related config is needed

### Established Patterns
- Module layout: `src/api/`, `src/ingestion/`, `src/extraction/`, `src/llm/`, `src/core/` — new export layer should be `src/export/` following the same separation
- Error pattern: `error_code` + `error_message` in job store — export errors should follow this
- Route pattern: separate route files per concern in `src/api/routes/` — export gets its own route file

### Integration Points
- CSV formatters read `job.extraction_result` (dict) and `job.doc_type` (str) from the job store
- New route `GET /jobs/{id}/export` registered alongside existing routes in `src/api/routes/`
- Export must reconstruct the Pydantic model from the stored dict to access field metadata for column ordering

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches for CSV formatting and module structure.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-csv-export*
*Context gathered: 2026-03-22*
