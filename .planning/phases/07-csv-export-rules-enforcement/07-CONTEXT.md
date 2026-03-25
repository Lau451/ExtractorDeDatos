# Phase 7: CSV Export Rules Enforcement - Context

**Gathered:** 2026-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Tighten the CSV export layer: normalize field values before they are written, warn when mandatory fields are missing, and produce descriptive download filenames. Column header names (snake_case) are NOT changed — they stay as Pydantic field names. This phase does not add new document types or change extraction schemas.

</domain>

<decisions>
## Implementation Decisions

### Value normalization
- **Numeric amount fields** — Strip currency symbols and thousand separators so cells contain pure numbers. E.g., `"$1,234.50"` → `"1234.50"`. If stripping produces a value that cannot be parsed as a number, keep the original value unchanged (never silently drop data).
- **Date fields** — Normalize extracted date strings to DD/MM/YYYY format. If parsing fails, keep the original value unchanged.
- **None → "Not found"** — Fields that were not extracted (None/null) export as the string `"Not found"` instead of a blank cell. This matches the review table display.
- **Text whitespace** — All text cells have leading/trailing whitespace stripped and internal multi-spaces compressed to a single space.
- **Currency field** — Drop currency symbols entirely from amount cells. The dedicated `currency` / `currency_code` field in each schema already carries the currency; no need to preserve it in the amount cell.
- **Field type detection** — Determined by field-name patterns, not explicit config per field:
  - Amount fields: names containing `amount`, `price`, `total`, `subtotal`, `tax`
  - Date fields: names containing `date` or ending with `_at`
  - All other fields: text normalization only (whitespace stripping)

### Mandatory field enforcement
- **Behavior** — Warn but allow download. Export returns HTTP 200 with the CSV. If any mandatory fields are empty/`"Not found"`, include a `X-Export-Warnings` response header whose value is a comma-separated list of missing field names.
- **Frontend** — Reactive: after the user clicks "Download CSV", if the response includes `X-Export-Warnings`, show a warning toast/banner listing the missing fields. No pre-flight check endpoint needed.
- **Mandatory fields config** — A `MANDATORY_FIELDS` dict in `src/export/` (co-located with the formatters), mapping each doc type to its list of required field names:
  ```python
  MANDATORY_FIELDS: dict[str, list[str]] = {
      "purchase_order": ["reference_number", ...],
      "tender_rfq": ["..."],
      ...
  }
  ```
  The specific field names per doc type are Claude's discretion based on the schemas — the pattern is key identity fields (document number, issuer, date).

### Download filename convention
- **Format** — `{doc_type}_{export_date}.csv` where `{export_date}` is today's date in `YYYY-MM-DD` format (the export date, not the document's internal date field).
- **Examples** — `purchase_order_2026-03-24.csv`, `tender_rfq_2026-03-24.csv`
- **Underscores** — Keep underscores (consistent with codebase conventions; no hyphens).
- **Implementation** — Set the `Content-Disposition` header in the export endpoint: `attachment; filename="{doc_type}_{date}.csv"`.

### Claude's Discretion
- Exact list of mandatory fields per doc type (user approved: key identity fields — document number, issuer, date)
- Whether normalization lives as a standalone `normalize_cell(field_name, value)` function or is inlined into each formatter
- Test fixture strategy for normalization edge cases

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Export layer to modify
- `src/export/formatters.py` — All five formatters + `_make_csv_bytes` helper + `FORMATTER_REGISTRY`; normalization and `MANDATORY_FIELDS` config go here or in a co-located module

### Extraction schemas (for field names and types)
- `src/extraction/schemas/purchase_order.py` — `PurchaseOrderResult`, `POLineItem` — field names to determine amount/date detection patterns
- `src/extraction/schemas/tender_rfq.py` — `TenderRFQResult`, `TenderLineItem`
- `src/extraction/schemas/quotation.py` — `QuotationResult`, `QuotationLineItem`
- `src/extraction/schemas/invoice.py` — `InvoiceResult`, `InvoiceLineItem`
- `src/extraction/schemas/supplier_comparison.py` — `SupplierComparisonResult`, `SupplierRow`

### Export API endpoint
- `src/api/routes/export.py` — GET /jobs/{id}/export; needs `Content-Disposition` filename header + `X-Export-Warnings` header logic

### Frontend download trigger
- `frontend/src/` — CSV download button; needs to read `X-Export-Warnings` response header and surface warning toast/banner

### Prior phase context
- `.planning/phases/03-csv-export/03-CONTEXT.md` — Phase 3 decisions: None → empty cell, UTF-8 BOM, RFC 4180 line endings (Phase 7 overrides None → "Not found")
- `.planning/phases/05-web-ui/05-CONTEXT.md` — Phase 5 frontend patterns (API client, download trigger implementation)

### Requirements
- `.planning/REQUIREMENTS.md` — EXP-01 through EXP-04 (CSV export requirements, all marked complete in Phase 3)

No external specs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_make_csv_bytes(headers, rows)` in `src/export/formatters.py` — shared helper that writes BOM + headers + rows; normalization should happen before rows are passed in
- `_format_line_item_type` and `_format_header_only_type` — the two private helpers that build row lists; normalization + mandatory-field check should be applied at this level
- `src/api/routes/export.py` — existing GET export endpoint; `Content-Disposition` and `X-Export-Warnings` headers added here

### Established Patterns
- None → `""` (empty string) in cell values — Phase 7 changes this to `"Not found"` for None fields
- `model_validate(extraction_result)` at the start of each formatter — field values accessed via `getattr(result, field)`
- UTF-8-with-BOM encoding, `\r\n` line endings (RFC 4180) — unchanged
- All schema fields are `Optional[str]` — no native float/int types; normalization must parse strings

### Integration Points
- Formatter functions receive a plain `dict` and return `bytes` — normalization applies inside the formatter before `_make_csv_bytes`
- Export endpoint in `src/api/routes/export.py` sets `Content-Disposition: attachment` — extend to include doc-type-aware filename and optional `X-Export-Warnings`
- Frontend download handler (Phase 5) reads the blob and triggers browser download — needs to also inspect response headers for warnings

</code_context>

<specifics>
## Specific Ideas

No specific references ("I want it like X") — open to standard approaches for the implementation details.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 07-csv-export-rules-enforcement*
*Context gathered: 2026-03-24*
