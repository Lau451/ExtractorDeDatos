---
phase: 03-csv-export
plan: 01
subsystem: api
tags: [csv, pydantic, utf8-bom, formatters, export]

# Dependency graph
requires:
  - phase: 02-extraction-pipeline
    provides: Five Pydantic schemas (PurchaseOrderResult, InvoiceResult, SupplierComparisonResult, TenderRFQResult, QuotationResult) and SCHEMA_REGISTRY
provides:
  - src/export/__init__.py — export module init
  - src/export/formatters.py — FORMATTER_REGISTRY + five format_* functions + _make_csv_bytes helper
  - tests/test_export.py — 12 unit tests covering BOM, column order, None handling, line-item expansion
affects: [04-download-endpoint, 05-frontend]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "_make_csv_bytes: write BOM as \\ufeff before csv.writer for UTF-8-with-BOM output"
    - "_format_line_item_type: model_fields iteration preserves Pydantic declaration order; line_items excluded from header_fields via f != 'line_items'"
    - "FORMATTER_REGISTRY mirrors SCHEMA_REGISTRY keys exactly — callers use same key for both"
    - "None-to-empty: ('' if v is None else v) applied to every cell before writing"

key-files:
  created:
    - src/export/__init__.py
    - src/export/formatters.py
    - tests/test_export.py
  modified: []

key-decisions:
  - "csv.writer lineterminator set to \\r\\n (RFC 4180 compliant) for maximum compatibility"
  - "BOM written as \\ufeff to io.StringIO buffer before csv.writer; encode('utf-8') produces b'\\xef\\xbb\\xbf' prefix"
  - "model_fields key order drives column order — matches Pydantic field declaration order exactly"
  - "Zero-line-item documents produce single data row with None placeholders for item columns (replaced with '' before write)"

patterns-established:
  - "Formatter pattern: validate dict into Pydantic model, iterate model_fields for column order, replace None with empty string"
  - "Line-item expansion: header fields repeated on every row, one CSV row per line item"

requirements-completed: [EXP-01, EXP-02, EXP-03, EXP-04]

# Metrics
duration: 5min
completed: 2026-03-22
---

# Phase 3 Plan 1: CSV Formatters Summary

**Five UTF-8-BOM CSV formatters using Pydantic model_fields iteration for schema-driven column ordering, with line-item expansion and None-to-empty-cell handling**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-23T02:08:48Z
- **Completed:** 2026-03-23T02:13:00Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files modified:** 3 created

## Accomplishments
- Created `src/export/formatters.py` with `_make_csv_bytes` helper (UTF-8 BOM), `_format_line_item_type`, `_format_header_only_type`, five public `format_*` functions, and `FORMATTER_REGISTRY`
- Implemented schema-driven column ordering via `model_class.model_fields` iteration — columns follow Pydantic field declaration order automatically
- Line-item types (purchase_order, invoice, supplier_comparison) expand to one CSV row per item with header fields repeated; zero-item docs produce one data row with empty item columns
- Header-only types (tender_rfq, quotation) produce exactly two rows (header + one data row)
- All None field values render as empty cells, never as the string "None"
- 12 unit tests covering BOM prefix, column order for all five types, distinct schema column counts, None handling, line-item expansion, zero-item edge case, header-only count, and registry completeness

## Task Commits

Each task was committed atomically:

1. **RED phase — failing test scaffold** - `ef94b00` (test)
2. **GREEN phase — formatters implementation** - `56d2c10` (feat)

_Note: TDD task split into RED commit (tests) and GREEN commit (implementation)_

## Files Created/Modified
- `src/export/__init__.py` — empty module init for export package
- `src/export/formatters.py` — core CSV generation logic: BOM helper, line-item and header-only helpers, five formatters, FORMATTER_REGISTRY
- `tests/test_export.py` — 12 unit tests; all pass (43/43 full suite green)

## Decisions Made
- `csv.writer` with `lineterminator="\r\n"` — RFC 4180 compliant, consistent across platforms
- BOM inserted as `"\ufeff"` directly into `io.StringIO` before `csv.writer`, then encoded as UTF-8 — produces `b'\xef\xbb\xbf'` prefix without any special encoding dance
- `model_fields` iteration for column order — directly reflects Pydantic declaration order with no hardcoded column lists, so schema changes propagate automatically

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness
- `FORMATTER_REGISTRY` is ready for Phase 4 download endpoint to consume — `FORMATTER_REGISTRY[doc_type](extraction_result)` produces CSV bytes
- All five doc types covered; column schemas match the interfaces specified in the plan exactly

---
*Phase: 03-csv-export*
*Completed: 2026-03-22*

## Self-Check: PASSED

- FOUND: src/export/__init__.py
- FOUND: src/export/formatters.py
- FOUND: tests/test_export.py
- FOUND: .planning/phases/03-csv-export/03-01-SUMMARY.md
- FOUND commit: ef94b00 (RED phase)
- FOUND commit: 56d2c10 (GREEN phase)
