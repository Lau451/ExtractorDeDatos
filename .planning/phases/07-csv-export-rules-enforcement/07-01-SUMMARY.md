---
phase: 07-csv-export-rules-enforcement
plan: 01
subsystem: api
tags: [csv, export, normalization, formatters, fastapi]

# Dependency graph
requires:
  - phase: 03-csv-export
    provides: formatters.py with FORMATTER_REGISTRY and _format_line_item_type/_format_header_only_type
  - phase: 04-full-api-integration
    provides: export endpoint in src/api/routes/export.py
provides:
  - normalize_cell function dispatching to amount/date/text normalization by field name pattern
  - MANDATORY_FIELDS dict defining key identity fields for all 5 doc types
  - check_mandatory_fields returning list of missing field names
  - Export filename as {doc_type}_{YYYY-MM-DD}.csv instead of job_{id}_{doc_type}.csv
  - X-Export-Warnings response header listing missing mandatory fields
affects: [frontend, 07-02]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Field-name pattern matching for normalization dispatch (_is_amount_field/_is_date_field)
    - Optional warning header — absent when clean, present with comma-separated fields when missing
    - MANDATORY_FIELDS registry keyed by doc_type matching FORMATTER_REGISTRY keys

key-files:
  created: []
  modified:
    - src/export/formatters.py
    - src/api/routes/export.py
    - tests/test_export.py

key-decisions:
  - "normalize_cell uses keyword substring matching on field names (_is_amount_field/_is_date_field) — no explicit whitelist, covers current and future fields"
  - "Unparseable amounts and dates kept unchanged to avoid data loss — best-effort normalization"
  - "submission_deadline and valid_until intentionally not date-normalized (lack 'date' in name)"
  - "X-Export-Warnings header absent (not empty) when no mandatory fields missing — cleaner contract"
  - "HTTP 200 always returned from export even when mandatory fields missing — warnings are informational"

patterns-established:
  - "normalize_cell pattern: field_name string drives dispatch, None/''/whitespace -> 'Not found'"
  - "check_mandatory_fields: returns list of field name strings, empty list means clean"

requirements-completed:
  - P7-NORM-01
  - P7-NORM-02
  - P7-NORM-03
  - P7-NORM-04
  - P7-MAND-01
  - P7-FILE-01

# Metrics
duration: 8min
completed: 2026-03-24
---

# Phase 07 Plan 01: CSV Export Rules Enforcement — Normalization and Headers Summary

**normalize_cell with amount/date/text dispatch, MANDATORY_FIELDS for 5 doc types, X-Export-Warnings header, and {doc_type}_{YYYY-MM-DD}.csv filenames**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-24T00:00:00Z
- **Completed:** 2026-03-24T00:08:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Added normalize_cell function that dispatches to amount/date/text normalization based on field name patterns — None and blank values become "Not found"
- Added MANDATORY_FIELDS dict and check_mandatory_fields for all 5 doc types; both formatter helpers (_format_line_item_type, _format_header_only_type) now use normalize_cell
- Updated export endpoint to use descriptive {doc_type}_{YYYY-MM-DD}.csv filename and X-Export-Warnings response header

## Task Commits

Each task was committed atomically:

1. **Task 1: Add normalize_cell, MANDATORY_FIELDS, check_mandatory_fields to formatters.py** - `cffa6f2` (feat)
2. **Task 2: Update export endpoint with descriptive filename and X-Export-Warnings header** - `3dbb035` (feat)

## Files Created/Modified
- `src/export/formatters.py` - Added normalize_cell, _is_amount_field, _is_date_field, _normalize_amount, _normalize_date, _normalize_text, MANDATORY_FIELDS, check_mandatory_fields; replaced inline None-to-empty logic in both formatter helpers
- `src/api/routes/export.py` - Changed filename to {doc_type}_{YYYY-MM-DD}.csv, added X-Export-Warnings header via check_mandatory_fields
- `tests/test_export.py` - Renamed test_none_values_are_empty_cells, updated test_zero_line_items_single_row, updated integration test filename assertions, added 17 new unit tests and 4 new integration tests (39 total, all pass)

## Decisions Made
- normalize_cell uses keyword substring matching on field names — covers current and future fields without an explicit whitelist
- Unparseable amounts and dates kept unchanged (no data loss — best-effort normalization)
- submission_deadline and valid_until intentionally not date-normalized (lack "date" substring in name)
- X-Export-Warnings header is absent (not set to empty string) when no mandatory fields are missing
- HTTP 200 returned even when mandatory fields missing — warnings are informational, not blocking

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Plan 07-02 can now consume check_mandatory_fields and MANDATORY_FIELDS from formatters.py
- Frontend can read the X-Export-Warnings header to surface missing field warnings in the UI
- All 82 tests in the test suite pass

---
*Phase: 07-csv-export-rules-enforcement*
*Completed: 2026-03-24*
