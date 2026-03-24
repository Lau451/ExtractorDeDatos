---
phase: 06-product-table-extraction
plan: 01
subsystem: extraction
tags: [pydantic, csv, gemini, schemas, line-items]

# Dependency graph
requires:
  - phase: 03-csv-export
    provides: _format_line_item_type helper and FORMATTER_REGISTRY pattern
  - phase: 02-extraction-pipeline
    provides: Optional[str] schema field pattern, TenderRFQResult and QuotationResult base schemas
provides:
  - TenderLineItem submodel with item_number, quantity, description fields
  - QuotationLineItem submodel with item_number, quantity, description fields
  - format_tender_rfq producing 11-column denormalized line-item CSV
  - format_quotation producing 15-column denormalized line-item CSV
affects: [phase-06-plan-02, gemini-extraction, csv-export]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Denormalized line-item CSV: one row per line item with header fields repeated on every row
    - Schema-driven formatter: _format_line_item_type infers columns from model_fields ordering

key-files:
  created: []
  modified:
    - src/extraction/schemas/tender_rfq.py
    - src/extraction/schemas/quotation.py
    - src/export/formatters.py
    - tests/test_export.py

key-decisions:
  - "TenderLineItem and QuotationLineItem use only 3 fields (item_number, quantity, description) — simpler than POLineItem since tenders/quotations lack pricing detail at line level"
  - "line_items declared as last field in both result models so CSV column ordering appends line item columns after all header columns"

patterns-established:
  - "New line-item doc type pattern: add XLineItem submodel before XResult, add line_items as last field, switch formatter from _format_header_only_type to _format_line_item_type"

requirements-completed: [P6-SCHEMA-01, P6-SCHEMA-02, P6-CSV-01, P6-CSV-02, P6-TEST-01]

# Metrics
duration: 4min
completed: 2026-03-24
---

# Phase 6 Plan 01: Add Line Item Submodels to Tender/RFQ and Quotation Schemas Summary

**TenderLineItem and QuotationLineItem submodels added to schemas, formatters switched from header-only to 11-column and 15-column denormalized line-item CSV, 20 tests passing**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-24T21:45:40Z
- **Completed:** 2026-03-24T21:49:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Added TenderLineItem (item_number, quantity, description — all Optional[str]) to tender_rfq.py, enabling Gemini to extract product tables from tender/RFQ documents via response_schema propagation
- Added QuotationLineItem with the same 3 fields to quotation.py for quotation product table extraction
- Switched format_tender_rfq from _format_header_only_type to _format_line_item_type — produces 11-column CSV (8 header + 3 line item)
- Switched format_quotation — produces 15-column CSV (12 header + 3 line item)
- Updated all test fixtures and assertions; added 3 new tests for line item expansion; all 20 tests pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Add TenderLineItem and QuotationLineItem submodels** - `a0fc82f` (feat)
2. **Task 2: Switch CSV formatters and update tests** - `72bd10c` (feat)

## Files Created/Modified
- `src/extraction/schemas/tender_rfq.py` - Added TenderLineItem class and line_items field to TenderRFQResult
- `src/extraction/schemas/quotation.py` - Added QuotationLineItem class and line_items field to QuotationResult
- `src/export/formatters.py` - Updated imports and switched format_tender_rfq/format_quotation to use _format_line_item_type
- `tests/test_export.py` - Updated fixtures, column count assertions, renamed test, added 3 new tests

## Decisions Made
- TenderLineItem and QuotationLineItem carry only 3 fields (item_number, quantity, description) matching the plan spec — no pricing fields since tenders/quotations describe requested/quoted items at a higher level than purchase orders
- line_items declared as last field in both result models so CSV column ordering appends line item columns after all header columns naturally via model_fields ordering

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Schemas updated: Gemini will now extract product tables from tender/RFQ and quotation documents automatically via response_schema
- CSV export reflects new columns; all existing column counts for PO (17), Invoice (19), SupplierComparison (16) unchanged
- Ready for Phase 6 Plan 02

---
*Phase: 06-product-table-extraction*
*Completed: 2026-03-24*
