---
phase: 05-web-ui
plan: 04
subsystem: api
tags: [fastapi, vite, proxy, routing, pytest]

# Dependency graph
requires:
  - phase: 05-web-ui
    provides: frontend React SPA that calls /api/* routes
  - phase: 04-full-api-integration
    provides: FastAPI routers for extract/jobs/doc_type/export/patch
provides:
  - FastAPI routers mounted with /api prefix — POST /api/extract, GET /api/jobs/*, etc.
  - Vite dev proxy forwarding /api/* without path stripping
  - All 61 pytest tests updated to use /api/* URLs
affects: [05-UAT, future-api-changes]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - FastAPI router prefix pattern: include_router with prefix='/api' for all API routes, health stays at root
    - Vite proxy pattern: changeOrigin:true without rewrite — both dev and production agree on /api/* paths

key-files:
  created: []
  modified:
    - src/main.py
    - frontend/vite.config.ts
    - tests/test_extract.py
    - tests/test_jobs.py
    - tests/test_export.py
    - tests/test_patch.py
    - tests/test_doc_type_override.py
    - tests/test_extraction.py

key-decisions:
  - "FastAPI routers mounted with prefix='/api' — all API routes under /api/*, health stays at root /health"
  - "Vite proxy rewrite lambda removed — /api/* forwarded as-is so dev and production share the same URL scheme"

patterns-established:
  - "API prefix pattern: frontend calls /api/*, backend mounts with prefix='/api', health is the only unprefixed endpoint"

requirements-completed: [REV-01, REV-02, REV-03, REV-04]

# Metrics
duration: 5min
completed: 2026-03-24
---

# Phase 5 Plan 04: /api Prefix Fix Summary

**FastAPI routers now mount with prefix='/api' and Vite proxy forwards /api/* without path rewriting, resolving the 405 SPA fallback collision that blocked all UAT file upload tests**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-24T13:50:00Z
- **Completed:** 2026-03-24T13:55:00Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Mounted all API routers (extract, jobs, doc_type, export, patch) with `prefix="/api"` in src/main.py
- Removed the Vite proxy `rewrite` lambda so `/api/*` passes through to FastAPI as `/api/*` in dev mode
- Updated all 6 test files to use `/api/extract` and `/api/jobs/*` URLs — 61 tests pass, zero failures
- `GET /health` remains at root without prefix, unchanged throughout

## Task Commits

Each task was committed atomically:

1. **Task 1: Add /api prefix to FastAPI routers and remove Vite proxy rewrite** - `90ce1b6` (feat)
2. **Task 2: Update all test URLs to use /api prefix** - `340d0ae` (feat)

**Plan metadata:** (docs commit — created below)

## Files Created/Modified

- `src/main.py` - Added `prefix="/api"` to five include_router calls; health_router stays unprefixed
- `frontend/vite.config.ts` - Removed `rewrite: (path) => path.replace(/^\/api/, '')` from proxy config
- `tests/test_extract.py` - Changed `/extract` to `/api/extract`, `/jobs/` to `/api/jobs/`
- `tests/test_jobs.py` - Changed `/extract` to `/api/extract`, `/jobs/` to `/api/jobs/`
- `tests/test_export.py` - Changed `/jobs/` to `/api/jobs/`
- `tests/test_patch.py` - Changed `/jobs/` to `/api/jobs/`
- `tests/test_doc_type_override.py` - Changed `/extract` to `/api/extract`, `/jobs/` to `/api/jobs/`
- `tests/test_extraction.py` - Changed `/extract` to `/api/extract`, `/jobs/` to `/api/jobs/`

## Decisions Made

- `prefix="/api"` applied at router registration, not inside individual route definitions — single change site, no per-route edits
- `health_router` intentionally left without prefix per plan spec — health check lives at `/health` not `/api/health`
- Vite proxy rewrite removal is the minimal change — the proxy block stays to handle CORS in dev mode

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- UAT Test 2 blocker resolved: POST /api/extract is now routable in FastAPI without SPA fallback collision
- Both dev mode (Vite proxy) and production mode (FastAPI static serving) use /api/* consistently
- UAT tests 2-11 should now be re-runnable against the running server

---
*Phase: 05-web-ui*
*Completed: 2026-03-24*
