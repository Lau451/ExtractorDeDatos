---
phase: 05-web-ui
plan: 02
subsystem: ui
tags: [react, typescript, react-dropzone, vitest, tdd, state-machine]

# Dependency graph
requires:
  - phase: 05-web-ui
    plan: 01
    provides: "Frontend scaffold, types/api.ts, lib/api.ts, lib/statusText.ts, lib/errorMessages.ts"
provides:
  - "UploadZone component with react-dropzone, file type filtering, drag-over state"
  - "useFileUpload hook wrapping api.postExtract with uploading state"
  - "useJobPoller hook with setInterval/clearInterval cleanup and pollingKey restart support"
  - "ProgressView component with spinner+status text and error banner"
  - "App.tsx 4-phase state machine (upload/processing/review/done)"
affects: [05-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "useRef stores interval ID for cleanup — avoids stale closure issue in useEffect"
    - "pollingKey as numeric dependency — incrementing restarts the poller without unmounting"
    - "Phase tagged union type: { tag: 'upload' } | { tag: 'processing'; jobId } | ..."
    - "TDD RED/GREEN cycle: test file committed before implementation"

key-files:
  created:
    - "frontend/src/hooks/useFileUpload.ts"
    - "frontend/src/hooks/useJobPoller.ts"
    - "frontend/src/components/UploadZone.tsx"
    - "frontend/src/components/ProgressView.tsx"
    - "frontend/src/components/ProgressView.test.tsx"
  modified:
    - "frontend/src/App.tsx"

key-decisions:
  - "Button label 'Try again' (not 'Retry Upload') per user decision recorded in plan revision commit 33f4d6d"
  - "pollingKey increment on retry/reset ensures useJobPoller restarts cleanly for doc-type override re-extraction"
  - "Single useJobPoller call in App.tsx — polledStatus synced to local pollingStatus state for ProgressView"
  - "useEffect cleanup via return () => clearInterval(id) — intervalRef.current tracks live interval ID"

# Metrics
duration: 2min
completed: 2026-03-24
---

# Phase 05 Plan 02: Upload and Processing Flow Summary

**Upload-to-processing flow with react-dropzone UploadZone, setInterval-based job poller with cleanup, ProgressView spinner/error-banner, and 4-phase App.tsx state machine**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-24T03:37:33Z
- **Completed:** 2026-03-24T03:39:49Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- UploadZone: react-dropzone with accept config for 6 file types, drag-over visual (border-primary + bg-primary/5), inline rejection error, disabled during upload
- useFileUpload: wraps api.postExtract, manages uploading boolean state, surfaces error message via onError callback
- useJobPoller: setInterval at 1500ms, clearInterval in useEffect cleanup, intervalRef.current for stale-closure safety, pollingKey dependency for restart
- ProgressView: spinner (Loader2 animate-spin) + getStatusText() for active states; AlertCircle + "Processing failed" heading + getErrorMessage() + "Try again" Button for error state
- App.tsx: 4-phase tagged union state machine; upload->processing on upload success; processing->review on poll complete; error handled inline within processing phase; review/done placeholders for Plan 03

## Task Commits

Each task was committed atomically:

1. **Task 1: Create UploadZone, useFileUpload, useJobPoller hooks** - `5ff6e18` (feat)
2. **TDD RED: Add failing ProgressView tests** - `b2d07be` (test)
3. **Task 2 GREEN: Implement ProgressView and App.tsx state machine** - `807653e` (feat)

## Files Created/Modified

- `frontend/src/hooks/useFileUpload.ts` - api.postExtract wrapper with uploading state and onSuccess/onError callbacks
- `frontend/src/hooks/useJobPoller.ts` - 1500ms interval poller with useRef cleanup, pollingKey restart support
- `frontend/src/components/UploadZone.tsx` - react-dropzone with 6-type accept config, drag-over styling, rejection error
- `frontend/src/components/ProgressView.tsx` - spinner view + error banner; getStatusText/getErrorMessage utilities
- `frontend/src/components/ProgressView.test.tsx` - 6 tests: spinner, extracting, fallback, GEMINI_ERROR banner, Try again button, null errorCode
- `frontend/src/App.tsx` - 4-phase state machine (upload/processing/review/done) with useFileUpload + useJobPoller integration

## Decisions Made

- **"Try again" button label**: Used "Try again" (not "Retry Upload") per user decision recorded in plan revision commit 33f4d6d. CONTEXT.md also specifies "Try again" in the error feedback section.
- **pollingKey restart pattern**: Incrementing pollingKey on retry/reset causes useJobPoller's useEffect to re-run, cleanly restarting the interval without component unmount.
- **intervalRef pattern**: Storing interval ID in useRef (not useState) avoids triggering re-renders and ensures cleanup always references the correct live interval.

## Deviations from Plan

None — plan executed exactly as written. TDD RED/GREEN cycle followed. All acceptance criteria met.

## Self-Check

- [x] frontend/src/hooks/useFileUpload.ts — FOUND
- [x] frontend/src/hooks/useJobPoller.ts — FOUND
- [x] frontend/src/components/UploadZone.tsx — FOUND
- [x] frontend/src/components/ProgressView.tsx — FOUND
- [x] frontend/src/components/ProgressView.test.tsx — FOUND
- [x] frontend/src/App.tsx — FOUND
- [x] All 6 ProgressView tests pass
- [x] npm run build exits 0
- [x] Task 1 commit 5ff6e18 — FOUND
- [x] Task 2 commit 807653e — FOUND
