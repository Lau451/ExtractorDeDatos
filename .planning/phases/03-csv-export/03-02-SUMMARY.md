---
phase: 03-csv-export
plan: 02
subsystem: api
tags: [fastapi, csv, export, router, integration-tests, pytest]

# Dependency graph
requires:
  - phase: 03-csv-export-01
    provides: FORMATTER_REGISTRY with five doc-type CSV formatter functions
  - phase: 02-extraction-pipeline
    provides: job_store singleton with Job dataclass and JobStatus
provides:
  - GET /jobs/{job_id}/export endpoint with 404/409/200 response contract
  - Integration tests covering all export endpoint branches
affects: [any future phase adding new doc types to FORMATTER_REGISTRY]

# Tech tracking
tech-stack:
  added: []
  patterns: [Router-per-resource with 404/409 gate, FORMATTER_REGISTRY dispatch pattern]

key-files:
  created:
    - src/api/routes/export.py
    - (tests appended to) tests/test_export.py
  modified:
    - src/main.py

key-decisions:
  - "EXPORTABLE_STATUSES set-literal makes it easy to add new exportable statuses later without modifying the gate logic"
  - "EXPORTABLE_DOC_TYPES derived from FORMATTER_REGISTRY.keys() at module load — stays in sync automatically when new formatters are added"
  - "FastAPI Response(content=bytes, media_type=...) used instead of StreamingResponse — CSV fits in memory for v1"

patterns-established:
  - "409 gate pattern: check status before checking doc_type — avoids calling FORMATTER_REGISTRY lookup on non-complete jobs"
  - "Integration tests insert directly into job_store._store under the lock to set up controlled job state"

requirements-completed: [API-04]

# Metrics
duration: 4min
completed: 2026-03-22
---

# Phase 03 Plan 02: CSV Export API Endpoint Summary

**GET /jobs/{id}/export FastAPI endpoint with 404/409 state gate, CSV file download, and six integration tests covering all response branches**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-23T02:14:07Z
- **Completed:** 2026-03-23T02:18:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Created `src/api/routes/export.py` with 404 (job not found), 409 (not complete or unknown doc_type), and 200 (CSV attachment) response paths
- Registered `export_router` in `src/main.py` — route `/jobs/{job_id}/export` confirmed in app routes
- Added 6 integration tests to `tests/test_export.py`; all 18 export tests and full 49-test suite pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Create export route and register in app** - `7cedbbc` (feat)
2. **Task 2: Add integration tests for export endpoint** - `821c2db` (test)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `src/api/routes/export.py` - GET /jobs/{job_id}/export with 404/409 gate and CSV Response
- `src/main.py` - Added export_router import and include_router call
- `tests/test_export.py` - Appended 6 integration tests (test_export_complete_job, test_export_404, test_export_409_not_complete, test_export_409_unknown_doc_type, test_export_content_type, test_export_filename)

## Decisions Made

- EXPORTABLE_STATUSES defined as `{"complete"}` set literal — extensible without changing gate logic
- EXPORTABLE_DOC_TYPES derived from `set(FORMATTER_REGISTRY.keys())` at module load — auto-syncs when new formatters are registered
- Used `fastapi.responses.Response` with `content=bytes` for CSV payload — fits in memory for v1; StreamingResponse unnecessary at this scale

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- CSV export feature is complete end-to-end: upload document → classify → extract → download CSV
- Phase 03 (csv-export) fully done; all 49 tests green
- Phase 04 can consume the export endpoint directly if needed

---
*Phase: 03-csv-export*
*Completed: 2026-03-22*
