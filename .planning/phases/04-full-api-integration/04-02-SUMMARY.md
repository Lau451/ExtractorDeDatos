---
phase: 04-full-api-integration
plan: "02"
subsystem: api
tags: [patch, job_store, fastapi, tdd, regression]

# Dependency graph
requires:
  - phase: 04-01
    provides: PATCH endpoint with deep merge and patch_extraction_result store method
provides:
  - PATCH /jobs/{id}/fields returns 409 extraction_result_missing when job has no extraction_result
  - patch_extraction_result() returns None instead of silently coercing None to empty dict
  - set_status() raises ValueError when called with 'complete' (invariant enforcement)
  - Regression tests covering all three UAT-identified gaps
affects: [future-api-phases, csv-export]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Belt-and-suspenders guard: route checks extraction_result before calling store, store also returns None for same condition
    - Invariant enforcement via ValueError in set_status to prevent bypassing set_extraction_result()

key-files:
  created: []
  modified:
    - src/api/routes/patch.py
    - src/core/job_store.py
    - tests/test_patch.py

key-decisions:
  - "Route-level guard for extraction_result=None returns 409 with structured error before calling store — clearer HTTP semantics than relying on store returning None which previously mapped to 404"
  - "set_status() ValueError raised before acquiring the lock — guard is purely logic-level, no store state involved"
  - "patch_extraction_result() returns None for both missing job and None extraction_result — caller (route) distinguishes via pre-check on the job object already fetched"

patterns-established:
  - "None-guard pattern: check extraction_result is None explicitly rather than relying on truthiness coercion"
  - "Invariant guard: domain operations that should not be reached directly raise ValueError with a descriptive message pointing to the correct method"

requirements-completed: [API-03]

# Metrics
duration: 3min
completed: 2026-03-24
---

# Phase 4 Plan 2: PATCH None Extraction Result Gap Closure Summary

**PATCH /jobs/{id}/fields now returns 409 extraction_result_missing when complete job has no extraction_result, closing the UAT-identified silent-success bug via TDD with 12 passing tests**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-24T00:07:16Z
- **Completed:** 2026-03-24T00:10:10Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Three regression tests written first (RED) to pin the exact UAT failure behavior
- `patch_extraction_result()` now returns `None` instead of silently coercing `None` to `{}` and proceeding with a meaningless patch
- `set_status()` raises `ValueError` if called with `"complete"`, enforcing that only `set_extraction_result()` can complete a job (which guarantees extraction_result is set)
- Route-level guard in `patch.py` returns 409 with `extraction_result_missing` error before ever reaching the store
- Full suite: 61 tests pass, 0 regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Add regression tests for None extraction_result and set_status invariant** - `cf6a229` (test)
2. **Task 2: Fix patch_extraction_result, set_status invariant, and patch.py guard** - `507d516` (fix)

_Note: TDD tasks — test commit (RED) followed by fix commit (GREEN)_

## Files Created/Modified

- `tests/test_patch.py` - Added 3 regression tests: test_patch_complete_but_no_extraction, test_patch_extraction_result_returns_none_when_no_extraction, test_set_status_rejects_complete
- `src/core/job_store.py` - patch_extraction_result() explicit None check; set_status() ValueError guard for 'complete'
- `src/api/routes/patch.py` - 409 extraction_result_missing guard after status check, before calling store

## Decisions Made

- Route-level guard returns 409 before calling the store rather than relying on `patch_extraction_result` returning `None` (which previously would have produced a generic 404) — gives clearer HTTP semantics for this specific error condition.
- `set_status()` ValueError raised outside the async lock since it is a pure logic guard unrelated to store state — no need to acquire the lock before failing.
- `patch_extraction_result()` returns `None` for both "job not found" and "job has no extraction_result" — the route distinguishes these by pre-checking `job.extraction_result` on the job already fetched via `get()`, so the dual-None return value does not create ambiguity.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. The `--timeout=60` flag in the plan's verify command is not supported by this pytest environment (not installed); ran `python -m pytest tests/ -x` without it, which worked correctly.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- UAT gap fully closed: PATCH on complete job with no extraction_result returns 409 (not 200)
- All invariants enforced: jobs can only reach 'complete' status via set_extraction_result()
- Phase 4 is fully complete — all API integration requirements met

---
*Phase: 04-full-api-integration*
*Completed: 2026-03-24*
