# Phase 6: Product Table Extraction - Context

**Gathered:** 2026-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Add product line item extraction to Tender/RFQ and Quotation document types. Both currently extract header fields only — this phase retrofits `line_items` tables into their Pydantic schemas, Gemini extraction prompts, CSV formatters, and the frontend review table. Purchase Order line items are already implemented and unchanged.

Scope: schema changes + Gemini extraction + CSV formatters + frontend display. Full end-to-end delivery.

</domain>

<decisions>
## Implementation Decisions

### Tender/RFQ line item fields
- Add `line_items: list[TenderLineItem]` to `TenderRFQResult`
- `TenderLineItem` fields: `item_number` (row/sequence), `quantity`, `description`
- All fields `Optional[str]` (established pattern — prevents Gemini InvalidArgument 400 errors)

### Quotation line item fields
- Add `line_items: list[QuotationLineItem]` to `QuotationResult`
- `QuotationLineItem` fields: `item_number` (row/sequence), `quantity`, `description`
- Same three fields as Tender/RFQ — consistent schema across both request/offer types

### Purchase Order
- No changes — existing `POLineItem` schema (item_number, description, sku, quantity, unit, unit_price, extended_price) is sufficient

### CSV formatter changes
- Tender/RFQ and Quotation switch from **header-only** to **denormalized line-item** format
- Same layout as PO/Invoice: one row per line item, header fields repeat on every row
- Documents with no extracted line items produce a single row (header fields, empty line item columns)
- This overrides the Phase 3 "header-only" decision for these two doc types

### Frontend changes
- Phase 5 shows the line items table only for PO and Invoice — extend to also show it for Tender/RFQ and Quotation
- Same `LineItemsTable` component, same column-per-field layout already used for PO/Invoice

### Claude's Discretion
- Pydantic model names for the new line item submodels (`TenderLineItem`, `QuotationLineItem`, or alternatives)
- Column header labels in CSV (human-readable vs field names)
- Whether to update `LINE_ITEM_KEYS` in frontend or add to it — implementation detail

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing schemas to modify
- `src/extraction/schemas/tender_rfq.py` — `TenderRFQResult` (8 header fields, no line_items) — add `TenderLineItem` submodel and `line_items` field
- `src/extraction/schemas/quotation.py` — `QuotationResult` (12 header fields, no line_items) — add `QuotationLineItem` submodel and `line_items` field
- `src/extraction/schemas/purchase_order.py` — `PurchaseOrderResult` + `POLineItem` — reference only, no changes
- `src/extraction/schemas/registry.py` — schema registry, may need updating

### Existing CSV formatters to modify
- `src/export/` — CSV formatters for all doc types; Tender/RFQ and Quotation formatters switch from header-only to line-item layout
- `src/export/formatters/` (or equivalent) — reference PO/Invoice formatters as the pattern to follow

### Frontend file to modify
- `frontend/src/` — `LINE_ITEM_KEYS` constant maps doc_type to line items key; extend to include `tender_rfq` and `quotation`
- Phase 5 context: `.planning/phases/05-web-ui/05-CONTEXT.md` — established that `LineItemsTable` is a separate multi-column table below header fields

### Prior phase decisions
- `.planning/phases/02-extraction-pipeline/02-CONTEXT.md` §CSV layout — locked layout: one row per line item, header repeats (Phase 6 extends this to tender/quotation)
- `.planning/phases/03-csv-export/03-CONTEXT.md` §Line item row layout — Phase 6 overrides the "header-only" classification for tender/quotation

### Requirements
- `.planning/REQUIREMENTS.md` — EXT-02 (tender/RFQ extraction), EXT-03 (quotation extraction)
- `.planning/ROADMAP.md` §Phase 6 — Goal statement

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/extraction/schemas/purchase_order.py`: `POLineItem` — exact pattern to follow for `TenderLineItem` and `QuotationLineItem` (same Optional[str] field pattern)
- `src/export/`: PO and Invoice CSV formatters already implement the denormalized line-item layout — reuse the same pattern for tender/quotation formatters
- Frontend `LineItemsTable` component — already built for PO/Invoice; just needs doc_types expanded

### Established Patterns
- All line item fields `Optional[str]` — no float/int types (prevents Gemini schema rejections, Phase 2 decision)
- `line_items: list[SubModel] = Field(default_factory=list, ...)` — same default as POLineItem
- CSV: missing fields → empty cells (not "Not found") — Phase 3 decision
- `LINE_ITEM_KEYS` in frontend maps `doc_type → line_items key` in `extraction_result` dict

### Integration Points
- `TenderRFQResult` and `QuotationResult` in schema registry — adding `line_items` field changes what Gemini is asked to extract and what CSV formatters serialize
- Frontend `ReviewTable` / `LineItemsTable` split — tender/quotation need to route to the line items path the same way PO/Invoice does

</code_context>

<specifics>
## Specific Ideas

- User explicitly confirmed: row number, quantity, description — exactly these three fields for both Tender/RFQ and Quotation line items
- Quotation and Tender/RFQ intentionally share the same line item field set — no price fields in quotation line items (totals stay in header)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 06-product-table-extraction*
*Context gathered: 2026-03-24*
