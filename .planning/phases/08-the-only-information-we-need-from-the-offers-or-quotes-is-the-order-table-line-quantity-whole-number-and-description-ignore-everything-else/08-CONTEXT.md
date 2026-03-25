# Phase 8: Offers/Quotes — Line Items Only - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

For tender/RFQ and quotation document types, narrow the entire pipeline to only the line items table — item_number, quantity (whole number), and description. Header fields (vendor name, dates, totals, payment terms, etc.) are removed from schemas, extraction prompts, CSV output, and the frontend review table. All other document types (purchase order, invoice, supplier comparison) are unchanged.

</domain>

<decisions>
## Implementation Decisions

### CSV output scope
- Tender/RFQ and quotation CSVs produce **3 columns only**: `item_number`, `quantity`, `description`
- All header columns are omitted entirely from the CSV — this replaces the Phase 6 denormalized layout for these two types
- Other doc types (purchase_order, invoice, supplier_comparison) are unchanged
- If zero line items are extracted: produce **one data row** with `"Not found"` in all 3 fields (consistent with Phase 7 None → "Not found")

### Quantity normalization to whole number
- **Strip trailing `.0`**: `"3.00"` → `"3"`, `"5.0"` → `"5"`. Do NOT round — `"3.5"` stays `"3.5"` (only strip when it's already an integer value with a decimal suffix)
- **Strip non-numeric suffix**: extract the leading numeric part — `"5 kg"` → `"5"`, `"10 pcs"` → `"10"`. Strip is applied before the `.0` stripping step
- **Unparseable strings**: keep the original value unchanged (never lose data)
- **None/missing quantity**: export as `"Not found"` (Phase 7 rule applies)
- This normalization applies only to the `quantity` field in line items, not to quantity fields in other doc types

### Extraction scope — narrow schemas and Gemini prompts
- **Remove header fields** from `TenderRFQResult` and `QuotationResult` Pydantic schemas — only `line_items: list[TenderLineItem]` / `list[QuotationLineItem]` remains
- Gemini is no longer asked to extract tender reference, issue date, vendor name, totals, etc. for these two doc types — narrower prompt reduces token cost and extraction noise
- `TenderLineItem` and `QuotationLineItem` schemas are unchanged (item_number, quantity, description)

### Frontend review table
- For tender/RFQ and quotation, the review table shows **only the line items table** (no header fields section)
- The header fields section (`ReviewTable` / key-value pairs) is hidden for these doc types
- `LineItemsTable` remains the same component, already handles the 3-field layout
- The doc type display and override dropdown are unchanged (still shown at the top)

### Claude's Discretion
- How to detect "integer-valued float string" for the `.0` strip (e.g., check if `float(s) == int(float(s))`)
- Whether to apply quantity normalization inside `normalize_cell` (via a new `_is_quantity_field` helper) or in a dedicated `normalize_quantity` function
- Whether the header-field removal from schemas is a breaking schema change that requires updating Gemini extraction tests

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Schemas to modify
- `src/extraction/schemas/tender_rfq.py` — `TenderRFQResult` (8 header fields + line_items): strip all header fields, keep only `line_items`; `TenderLineItem` unchanged
- `src/extraction/schemas/quotation.py` — `QuotationResult` (12 header fields + line_items): strip all header fields, keep only `line_items`; `QuotationLineItem` unchanged

### CSV formatters
- `src/export/formatters.py` — `format_tender_rfq` and `format_quotation`: switch to a new output path that produces only 3 columns (item_number, quantity, description); update `MANDATORY_FIELDS` to remove tender/quotation header field entries; add quantity normalization logic

### Frontend
- `frontend/src/` — review table rendering logic: for tender/RFQ and quotation, skip the header fields section and show only `LineItemsTable`

### Prior phase context
- `.planning/phases/06-the-tables-of-requests-offers-and-quotations-must-be-extracted-these-tables-contain-the-requested-products-this-information-must-be-extracted-in-addition-purchase-orders-or-order-notes-also-describe-the-awarded-products/06-CONTEXT.md` — Phase 6 added TenderLineItem/QuotationLineItem with item_number, quantity, description; Phase 8 removes header fields from the same schemas
- `.planning/phases/07-csv-export-rules-enforcement/07-CONTEXT.md` — Phase 7 normalization rules (normalize_cell, MANDATORY_FIELDS, None → "Not found"); Phase 8 builds on these

No external specs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `normalize_cell(field_name, value)` in `src/export/formatters.py` — already handles None → "Not found"; quantity normalization can be added as a new branch here via a `_is_quantity_field` helper
- `_format_line_item_type(model_class, item_model_class, extraction_result)` — existing helper for line-item doc types; tender/quotation can reuse a simplified version (no header_fields, only item_fields)
- Frontend `LineItemsTable` component — already renders item_number, quantity, description columns for PO/invoice; no changes needed to the component itself

### Established Patterns
- All schema fields are `Optional[str]` — quantity stays `Optional[str]`; normalization to whole number is a string transformation, not a type change
- `FORMATTER_REGISTRY` maps doc_type → formatter function; tender_rfq and quotation formatters are replaced in-place
- `MANDATORY_FIELDS` dict in `formatters.py` — entries for tender_rfq and quotation become empty lists (or removed) since no header fields remain mandatory

### Integration Points
- Removing header fields from `TenderRFQResult` / `QuotationResult` changes `model_validate()` behavior in formatters — any code calling `.model_validate(extraction_result)` on these types must tolerate extra keys being ignored (Pydantic v2 default behavior: extra fields are ignored)
- Frontend review table renders header fields via `ReviewTable` (key-value section) — needs a guard per doc_type to skip this section for tender/quotation
- If existing extraction jobs in the job store have the old schema (with header fields), the new Pydantic model will silently ignore those keys — no migration needed for in-memory store

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

*Phase: 08-offers-quotes-line-items-only*
*Context gathered: 2026-03-25*
