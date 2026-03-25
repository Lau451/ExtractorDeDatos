---
phase: 07-csv-export-rules-enforcement
plan: "02"
subsystem: ui
tags: [react, fastapi, cors, fetch-api, warning-banner, lucide-react]

# Dependency graph
requires:
  - phase: 07-csv-export-rules-enforcement-01
    provides: X-Export-Warnings header in export endpoint response, backend normalization and mandatory-field logic
provides:
  - CORS expose_headers allowing browser to read X-Export-Warnings header
  - Fetch-based programmatic CSV download replacing window.open
  - Amber warning banner in review and done phases when mandatory fields are missing
  - Loader2 spinner on download button during fetch
  - exportWarnings state cleared on reset
affects:
  - future phases requiring frontend state pattern reference

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Fetch raw Response to inspect custom headers before triggering programmatic download"
    - "void promise pattern for async event handler in onClick"
    - "role=alert for dynamic banner announcements to screen readers"

key-files:
  created: []
  modified:
    - src/main.py
    - frontend/src/lib/api.ts
    - frontend/src/App.tsx

key-decisions:
  - "CORSMiddleware added with expose_headers=['X-Export-Warnings'] so the browser CORS policy does not strip the custom header"
  - "exportCSV returns raw Response (not parsed JSON/blob) so caller can read headers before consuming body"
  - "Warning stays visible in review phase after download so user can re-download or PATCH fields without losing warning context"
  - "Phase transitions to done only when no warnings; when warnings exist, phase stays in review with banner"

patterns-established:
  - "Pattern: api.exportCSV() returns Promise<Response> — raw response for header inspection before body consumption"
  - "Pattern: void handleAsync() in onClick to satisfy @typescript-eslint/no-floating-promises"

requirements-completed:
  - P7-MAND-02
  - P7-FE-01

# Metrics
duration: 2min
completed: 2026-03-24
---

# Phase 07 Plan 02: Warning Banner and CORS Expose Headers Summary

**CORS expose_headers wired to browser fetch-based CSV download that reads X-Export-Warnings and renders an amber warning banner listing missing mandatory fields**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-24T00:07:32Z
- **Completed:** 2026-03-24T00:09:35Z
- **Tasks:** 1 of 2 (Task 2 is human-verify checkpoint — awaiting user confirmation)
- **Files modified:** 3

## Accomplishments
- Added CORSMiddleware to FastAPI app with `expose_headers=["X-Export-Warnings"]` so browser CORS policy no longer strips the custom header
- Added `api.exportCSV()` method that returns raw `Response` for header inspection before body consumption, keeping `exportUrl` for backward compatibility
- Replaced `window.open(api.exportUrl(...))` with an async fetch-based programmatic download that reads `X-Export-Warnings` header and triggers blob download via anchor click
- Added `exportWarnings: string[] | null` and `isDownloading: boolean` state; warning banner appears in both review and done phases when header is present
- Added `Loader2` spinner replacing `Download` icon on button during fetch; button disabled while downloading
- `handleReset` clears `exportWarnings` so banner disappears after "Upload another document"

## Task Commits

Each task was committed atomically:

1. **Task 1: Add CORS expose_headers and frontend download flow** - `f5f4003` (feat)

**Plan metadata:** (docs commit to follow after human-verify checkpoint)

## Files Created/Modified
- `src/main.py` - Added CORSMiddleware with expose_headers for X-Export-Warnings
- `frontend/src/lib/api.ts` - Added exportCSV() returning raw Response
- `frontend/src/App.tsx` - Async handleDownloadCSV, exportWarnings state, isDownloading state, warning banner (review and done phases), Loader2 spinner, handleReset clears warnings

## Decisions Made
- CORSMiddleware inserted between `app = FastAPI(...)` and first `app.include_router(...)` call — CORS middleware must be registered before routers to wrap all responses
- Warning banner remains in review phase (phase does not transition to done when warnings are present) — allows user to read warnings and optionally PATCH fields before deciding to continue
- Phase transitions to done only when `!warnings` — clean separation of warning vs. no-warning post-download flows

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Task 2 (human-verify checkpoint) awaits user running both servers and visually confirming:
  1. Warning banner renders with amber styling and lists missing field names
  2. Download button shows spinner during fetch
  3. CSV downloads with descriptive filename and BOM encoding
  4. Warning clears after "Upload another document"

---
*Phase: 07-csv-export-rules-enforcement*
*Completed: 2026-03-24*
