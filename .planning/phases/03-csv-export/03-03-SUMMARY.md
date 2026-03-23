---
phase: 03-csv-export
plan: "03"
subsystem: api
tags: [job-store, ingestion, status-machine, bug-fix]

# Dependency graph
requires:
  - phase: 03-csv-export-02
    provides: Export endpoint that gates on status='complete' and extraction_result
  - phase: 02-extraction-pipeline
    provides: set_extraction_result() which correctly sets status='complete' at pipeline end
provides:
  - set_raw_text() method on JobStore that stores raw_text without changing status
  - Ingestion flow that leaves job in 'processing' during pipeline execution
  - Elimination of premature status='complete' window that caused 409 export errors
affects: [csv-export, ingestion, extraction-pipeline, testing]

# Tech tracking
tech-stack:
  added: []
  patterns: [status-machine progression enforced — complete only reachable via set_extraction_result or unknown doc_type path]

key-files:
  created: []
  modified:
    - src/core/job_store.py
    - src/ingestion/service.py
    - tests/test_ingestion.py

key-decisions:
  - "set_raw_text() added alongside set_complete() — set_complete() kept for backwards compatibility but no longer called from ingestion flow"
  - "Status='complete' is now exclusively reached via set_extraction_result() or explicit set_status() for unknown doc_type"

patterns-established:
  - "Status machine: pending -> processing -> classifying -> extracting -> complete; raw_text storage and status progression are now decoupled"

requirements-completed: [EXP-01, API-04]

# Metrics
duration: 5min
completed: 2026-03-23
---

# Phase 03 Plan 03: Gap Closure — Status Collision Bug Fix Summary

**set_raw_text() added to JobStore to decouple text storage from status progression, eliminating premature 'complete' window that caused 409 export errors**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-23T03:11:00Z
- **Completed:** 2026-03-23T03:16:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Added `set_raw_text()` method to JobStore that stores raw_text without touching status
- Replaced `set_complete()` call in ingestion/service.py with `set_raw_text()` — job stays in 'processing' during pipeline execution
- Updated all 5 ingestion test status assertions from 'complete' to 'processing', reflecting the corrected pipeline behavior
- Full 49-test suite passes with no regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Add set_raw_text to JobStore and fix ingestion service** - `66ea5b1` (fix)
2. **Task 2: Update ingestion tests to expect processing status mid-pipeline** - `3912e56` (test)

## Files Created/Modified
- `src/core/job_store.py` - Added set_raw_text() method; set_complete() retained for compatibility
- `src/ingestion/service.py` - Changed set_complete() call to set_raw_text() on line 32
- `tests/test_ingestion.py` - Updated 5 test assertions and helper docstring to reflect 'processing' status

## Decisions Made
- `set_complete()` was kept in JobStore rather than removed — it may still be called in test contexts and is not harmful to retain. The key change is that the ingestion flow no longer calls it.
- No changes needed in `src/extraction/service.py` — the unknown doc_type path already correctly calls `set_status(job_id, "complete")` which is valid (no extraction needed for unknown types).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. The AST verification command in the plan used `ast.FunctionDef` but async methods require `ast.AsyncFunctionDef` — verified with both node types. This was a verification script issue only, not a code issue.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Status collision bug is fully resolved. The end-to-end flow is now correct:
  1. POST /extract -> status: pending
  2. Ingestion runs -> status: processing (raw_text stored, NOT 'complete')
  3. Extraction pipeline -> status: classifying -> extracting -> complete (with extraction_result)
  4. GET /jobs/{id}/export -> 200 with CSV
- Phase 03 is complete. Phase 04 (or UAT re-run) can proceed.

---
*Phase: 03-csv-export*
*Completed: 2026-03-23*
