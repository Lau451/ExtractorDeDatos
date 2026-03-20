---
phase: 02-extraction-pipeline
plan: 04
subsystem: api
tags: [fastapi, extraction-pipeline, doc-type-override, test-suite]

# Dependency graph
requires:
  - phase: 02-extraction-pipeline
    provides: "run_extraction_pipeline and extract_with_type in src/extraction/service.py"
  - phase: 02-extraction-pipeline
    provides: "VALID_DOC_TYPES in src/extraction/schemas/registry.py"
  - phase: 02-extraction-pipeline
    provides: "DocTypeOverrideRequest in src/api/models.py"
provides:
  - "Pipeline wiring: run_extraction_pipeline called after ingestion completes"
  - "Extended GET /jobs/{id} with doc_type field and extraction_result with Not found serialization"
  - "PATCH /jobs/{id}/doc_type endpoint returning 202 and triggering re-extraction"
  - "Full test suite (31 tests) with zero xfail markers"
affects: [03-csv-export, future phases using job status API]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "None->Not found serialization in _serialize_extraction helper for API responses"
    - "BackgroundTasks.add_task for async re-extraction without blocking PATCH response"
    - "patch src.api.routes.doc_type.extract_with_type (not service module) for test isolation"

key-files:
  created:
    - src/api/routes/doc_type.py
  modified:
    - src/ingestion/service.py
    - src/api/routes/jobs.py
    - src/main.py
    - tests/test_extraction.py
    - tests/test_doc_type_override.py
    - tests/test_jobs.py

key-decisions:
  - "Patch src.api.routes.doc_type.extract_with_type (not src.extraction.service) for test isolation — patching the import reference in the route module, not the origin"
  - "Updated test_jobs.py to poll through classifying/extracting statuses and drop result.raw_text assertion — API no longer returns raw_text wrapper"

patterns-established:
  - "Test doc_type override by patching the extract_with_type reference in the route module (src.api.routes.doc_type.extract_with_type)"
  - "GET /jobs/{id} always includes doc_type field; extraction_result only present when status=complete"

requirements-completed: [CLS-02, CLS-03, EXT-01, EXT-02, EXT-03, EXT-04, EXT-05, EXT-06, EXT-07, EXT-08]

# Metrics
duration: 9min
completed: 2026-03-20
---

# Phase 02 Plan 04: Wire Pipeline and Finalize Tests Summary

**End-to-end extraction pipeline wired with PATCH /jobs/{id}/doc_type override, GET extended with extraction_result (None->"Not found"), and all 31 tests green with zero xfail markers**

## Performance

- **Duration:** 9 min
- **Started:** 2026-03-20T00:14:40Z
- **Completed:** 2026-03-20T00:23:26Z
- **Tasks:** 2
- **Files modified:** 6 (modified) + 1 (created)

## Accomplishments
- Chained `run_extraction_pipeline` after ingestion so every upload triggers full extraction automatically
- Created PATCH /jobs/{id}/doc_type endpoint that validates doc_type, clears previous result, sets status "extracting", and returns 202
- Extended GET /jobs/{id} to include `doc_type` always and `extraction_result` (with None->"Not found" serialization) when complete
- Removed all 8 xfail markers across test_extraction.py and test_doc_type_override.py — 31 tests pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire extraction pipeline and extend API endpoints** - `0c53656` (feat)
2. **Task 2: Finalize all tests — remove xfail and implement test bodies** - `fc2c37c` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified
- `src/ingestion/service.py` - Added run_extraction_pipeline import and call after set_complete
- `src/api/routes/jobs.py` - Replaced with extended version: doc_type + extraction_result + Not found serializer
- `src/api/routes/doc_type.py` - New PATCH endpoint for doc_type override
- `src/main.py` - Registered doc_type_router
- `tests/test_extraction.py` - Removed all xfail markers
- `tests/test_doc_type_override.py` - Removed xfail markers, fixed route (/extract not /jobs), fixed mock target
- `tests/test_jobs.py` - Updated to new API shape (removed result.raw_text, added doc_type check, extended polling statuses)

## Decisions Made
- Patching `src.api.routes.doc_type.extract_with_type` (not `src.extraction.service.extract_with_type`) for test isolation — the route module imports extract_with_type at load time, so the patch must target the reference in the route module's namespace
- Updated test_jobs.py to treat classifying/extracting as non-terminal statuses and removed result.raw_text assertion since API no longer returns the raw_text wrapper

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test_jobs.py polling and assertion for new API shape**
- **Found during:** Task 1 (verification of test_jobs.py)
- **Issue:** test_job_lifecycle expected `job.get("result")` with `raw_text` inside it, and polled only for pending/processing statuses — both incompatible with the new extended API that returns doc_type/extraction_result and goes through classifying/extracting statuses
- **Fix:** Updated TERMINAL_STATUSES set to include all non-terminal statuses, replaced raw_text assertion with doc_type presence check
- **Files modified:** tests/test_jobs.py
- **Verification:** pytest tests/test_jobs.py passes (2/2)
- **Committed in:** 0c53656 (Task 1 commit)

**2. [Rule 1 - Bug] Fixed test_doc_type_override.py route and mock target**
- **Found during:** Task 2 (writing test_doc_type_override.py)
- **Issue:** Tests used `/jobs` POST route (does not exist — correct route is `/extract`) and patched `src.extraction.service.run_extraction_pipeline` (doc_type endpoint uses `extract_with_type`, not `run_extraction_pipeline`)
- **Fix:** Changed POST to `/extract`, changed patch target to `src.api.routes.doc_type.extract_with_type`
- **Files modified:** tests/test_doc_type_override.py
- **Verification:** pytest tests/test_doc_type_override.py passes (3/3)
- **Committed in:** fc2c37c (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (2 Rule 1 bugs in test files)
**Impact on plan:** Both fixes required for correct test operation. No scope creep — tests now verify the exact behavior specified in the plan.

## Issues Encountered
None beyond the auto-fixed test deviations above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Full extraction pipeline operational end-to-end: upload -> classify -> extract -> result available via GET /jobs/{id}
- Doc type override via PATCH /jobs/{id}/doc_type works and re-triggers extraction
- Test suite fully green (31 tests, 0 xfail)
- Ready for Phase 03: CSV export from extraction_result

---
*Phase: 02-extraction-pipeline*
*Completed: 2026-03-20*
