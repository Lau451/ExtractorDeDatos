---
phase: 04-full-api-integration
plan: "01"
subsystem: api
tags: [patch-endpoint, deep-merge, ttl-cleanup, error-codes, tdd]
dependency_graph:
  requires: []
  provides:
    - PATCH /jobs/{id}/fields endpoint with deep merge
    - Error code constants module (src/core/errors.py)
    - JobStore.patch_extraction_result() method
    - JobStore.cleanup_expired_jobs() method
    - Background TTL cleanup via lifespan context manager
  affects:
    - src/main.py (lifespan, patch router)
    - src/core/job_store.py (new methods)
    - src/api/models.py (PatchFieldsRequest)
tech_stack:
  added: []
  patterns:
    - deep-merge: recursive dict/list merge without mutation (copy.deepcopy)
    - toctou-safe-patch: patch_extraction_result returns updated Job directly (no re-fetch)
    - lifespan-cleanup: asynccontextmanager creates/cancels background asyncio task
key_files:
  created:
    - src/core/errors.py
    - src/api/routes/patch.py
    - tests/test_patch.py
  modified:
    - src/core/job_store.py
    - src/api/models.py
    - src/main.py
decisions:
  - patch_extraction_result returns Optional[Job] directly to avoid TOCTOU re-fetch
  - _deep_merge uses copy.deepcopy to prevent mutation of either argument
  - PATCH response reuses _serialize_extraction() from jobs.py for None->'Not found' consistency
  - test_patch_then_export uses buyer_name/supplier_name (actual PO schema fields) not buyer_company (plan spec had wrong field name)
  - Cleanup loop interval set to 300s (5 min); JOB_TTL = 1 hour
metrics:
  duration: "4 min"
  completed_date: "2026-03-23"
  tasks_completed: 3
  files_modified: 6
---

# Phase 4 Plan 01: PATCH Endpoint, Error Codes, TTL Cleanup Summary

**One-liner:** PATCH /jobs/{id}/fields with deep-merge, error code constants, TTL background cleanup, and 9-test suite proving REV-05 corrections flow to CSV export.

## What Was Built

Three components completing the Phase 4 API surface:

1. **`src/core/errors.py`** — Five string constants (`DOCLING_TIMEOUT`, `DOCLING_PARSE_ERROR`, `GEMINI_ERROR`, `INVALID_FILE_TYPE`, `FILE_TOO_LARGE`) for structured error reporting to Phase 5 UI.

2. **Core JobStore additions** — `_deep_merge()` pure function with recursive dict/list-by-index merging; `patch_extraction_result()` holding the lock during merge and returning the updated `Job` directly (avoids TOCTOU); `cleanup_expired_jobs()` removing all jobs older than `JOB_TTL = timedelta(hours=1)`.

3. **PATCH /jobs/{id}/fields endpoint** — Returns 200 + full JobResponse-shaped dict for complete jobs, 404 for unknown IDs, 409 for non-complete jobs. Reuses `_serialize_extraction()` for consistent None->"Not found" serialization.

4. **Lifespan context manager in `src/main.py`** — Creates a background `_cleanup_loop()` task on startup that runs every 5 minutes; cancels cleanly on shutdown.

5. **`tests/test_patch.py`** — 9 tests: 3 deep-merge unit tests, 1 TTL cleanup unit test, 1 error constants test, 3 PATCH integration tests (200/404/409), 1 end-to-end test proving REV-05 (PATCH then export CSV contains corrected values).

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | f61aa3d | feat(04-01): core infrastructure — error codes, deep merge, JobStore methods, PatchFieldsRequest |
| Task 2 | 5218bcf | feat(04-01): PATCH route, lifespan cleanup task, patch router wiring |
| Task 3 | 6215005 | test(04-01): full test suite for PATCH endpoint, deep merge, TTL cleanup, error codes |

## Test Results

- `pytest tests/test_patch.py -x -v`: **9/9 passed**
- `pytest tests/ -x`: **58/58 passed** (no regressions)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] test_patch_then_export used wrong PO schema field names**
- **Found during:** Task 3 (writing the end-to-end test)
- **Issue:** Plan spec used `buyer_company` and `supplier_company` in the extraction_result dict for the export test, but PurchaseOrderResult schema uses `buyer_name` and `supplier_name`. Using wrong field names would cause the formatter to reject the dict.
- **Fix:** Used `buyer_name` / `supplier_name` to match the actual Pydantic model in `src/extraction/schemas/purchase_order.py`
- **Files modified:** tests/test_patch.py
- **Commit:** 6215005

## Self-Check: PASSED

All created files found on disk. All three task commits verified in git log.
