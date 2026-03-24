---
phase: 05-web-ui
verified: 2026-03-24T14:30:00Z
status: passed
score: 14/14 must-haves verified
re_verification:
  previous_status: passed (premature — written before UAT ran)
  previous_score: 12/12
  gaps_closed:
    - "POST /api/extract routable in FastAPI — 405 error resolved by adding prefix='/api' to all API routers"
    - "Vite dev proxy forwards /api/* without path rewriting — rewrite lambda removed"
    - "All 61 pytest tests updated to /api/* URLs — 61/61 pass"
  gaps_remaining: []
  regressions: []
gaps: []
human_verification:
  - test: "Re-run UAT Test 2: Upload a file in the browser against the live server"
    expected: "POST /api/extract returns 202 (no 405). Processing spinner appears. Review table loads with extracted fields."
    why_human: "The 405 fix was verified programmatically (route introspection, 61 tests) but the live browser upload flow has not been re-run since gap closure. Confirms fix is complete end-to-end."
  - test: "Upload a PDF and observe the drag-and-drop zone visual behavior"
    expected: "Drop zone border turns primary color and background lightens when a file is dragged over"
    why_human: "isDragActive CSS state change cannot be triggered by automated grep; requires browser interaction"
  - test: "Upload a document, wait for processing, then edit a field value in the review table"
    expected: "Clicking a cell opens an inline input; pressing Enter or blurring saves the value; no page refresh; PATCH request fires"
    why_human: "End-to-end PATCH flow with live backend requires a running server and real extraction"
  - test: "On the review table, override the document type via the dropdown"
    expected: "UI transitions back to the processing spinner and returns to review with updated fields for the new doc type"
    why_human: "Requires a live backend job and real polling cycle to verify the state transition sequence"
  - test: "Click 'Download CSV' on the review page"
    expected: "Browser downloads a CSV file; UI transitions to the done state showing 'Upload another document'"
    why_human: "window.open() download behavior and state transition require browser execution"
---

# Phase 05: Web UI Verification Report

**Phase Goal:** React SPA with upload, status polling, inline-edit review table, and CSV download. Frontend communicates with backend via /api prefix. All routes working without 405 errors.
**Verified:** 2026-03-24T14:30:00Z
**Status:** PASSED
**Re-verification:** Yes — after gap closure plan 05-04 (UAT revealed 405 on POST /api/extract; fixes applied in commits 90ce1b6 and 340d0ae)

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Frontend project builds without errors via npm run build | VERIFIED | Build produced in frontend/dist/; vite.config.ts is valid |
| 2 | Vite dev proxy forwards /api/* to localhost:8000 WITHOUT path rewriting | VERIFIED | vite.config.ts lines 8-13: proxy target http://localhost:8000 with changeOrigin:true; rewrite lambda removed in commit 90ce1b6 |
| 3 | POST /api/extract reaches the extract router and is not absorbed by SPA fallback | VERIFIED | Runtime route introspection: ['POST'] /api/extract explicitly registered; SPA fallback is @app.get only |
| 4 | All API routers mounted with /api prefix; health stays at root /health | VERIFIED | src/main.py lines 47-51: prefix="/api" on extract, jobs, doc_type, export, patch routers; health_router at line 46 has no prefix |
| 5 | All five API endpoints have typed fetch wrappers calling /api/* paths | VERIFIED | frontend/src/lib/api.ts: postExtract(/api/extract), getJob(/api/jobs/{id}), patchDocType(/api/jobs/{id}/doc_type), patchFields(/api/jobs/{id}/fields), exportUrl(/api/jobs/{id}/export) |
| 6 | TypeScript types match the actual JobResponse shape from the backend | VERIFIED | frontend/src/types/api.ts exports JobResponse matching src/api/models.py |
| 7 | User can drag or pick a file and see a processing spinner with status text | VERIFIED | UploadZone.tsx uses useDropzone with accepted MIME types; App.tsx transitions phase to 'processing'; ProgressView renders Loader2 + getStatusText() |
| 8 | Status text updates as job status changes through all four stages | VERIFIED | statusText.ts maps all statuses; useJobPoller polls at 1500ms and updates status; ProgressView renders getStatusText(status) |
| 9 | Polling stops when status is complete or error | VERIFIED | useJobPoller.ts: clearInterval called for both 'complete' and 'error' before firing callbacks |
| 10 | Error state shows an inline banner with error message and Try again button | VERIFIED | ProgressView.tsx: AlertCircle + "Processing failed" + getErrorMessage(errorCode) + "Try again" Button; 6 ProgressView tests pass |
| 11 | User can see all extracted header fields in a two-column Label/Value table | VERIFIED | ReviewTable.tsx: two-column Table with getFieldLabel(key) labels and EditableCell per value; 4 ReviewTable tests pass |
| 12 | User can click any value cell, edit it, and the PATCH request fires on blur or Enter | VERIFIED | EditableCell.tsx: commit() called on blur and Enter keydown; App.tsx handleFieldSave calls api.patchFields; 8 EditableCell tests pass |
| 13 | Fields with value 'Not found' display muted gray italic; empty blur does NOT fire PATCH | VERIFIED | EditableCell.tsx: cn() applies text-muted-foreground italic when value === 'Not found'; emptyFromNotFound guard in commit() prevents spurious PATCH |
| 14 | All 61 pytest tests pass against /api/* URLs with zero failures | VERIFIED | python -m pytest tests/ -x -q: 61 passed, 0 failures in 39.98s; no bare /extract or /jobs/ URLs remain in test files |

**Score:** 14/14 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `frontend/package.json` | Project manifest with all dependencies | VERIFIED | Contains react-dropzone, lucide-react, tailwindcss, vitest, @testing-library/react |
| `frontend/vite.config.ts` | Vite config with proxy (no rewrite) and Tailwind plugin | VERIFIED | Proxy to localhost:8000 without rewrite lambda; tailwindcss() plugin; @ alias; test config |
| `frontend/src/lib/api.ts` | Typed API wrappers calling /api/* endpoints | VERIFIED | All 5 functions present with real fetch calls to /api/* paths |
| `frontend/src/types/api.ts` | TypeScript interfaces matching backend models | VERIFIED | JobResponse matches src/api/models.py |
| `frontend/src/lib/fieldLabels.ts` | Human-readable labels for all extraction fields | VERIFIED | 40+ keys covering all doc types; getFieldLabel() fallback |
| `frontend/src/components/UploadZone.tsx` | Drag-and-drop file upload with react-dropzone | VERIFIED | useDropzone with accepted MIME types; isDragActive; onFileAccepted callback |
| `frontend/src/components/ProgressView.tsx` | Spinner + status text + error banner | VERIFIED | Loader2 + animate-spin; AlertCircle + error message + retry button |
| `frontend/src/hooks/useJobPoller.ts` | Polling hook with cleanup | VERIFIED | setInterval at 1500ms; clearInterval on complete/error; intervalRef cleanup |
| `frontend/src/App.tsx` | State machine driving the linear flow | VERIFIED | 4-phase tagged union (upload/processing/review/done); all components wired |
| `frontend/src/components/EditableCell.tsx` | Click-to-edit cell with PATCH on blur/Enter | VERIFIED | commit() on blur and Enter; Escape reverts; Not found guard; 8 tests pass |
| `frontend/src/components/ReviewTable.tsx` | Two-column header fields table | VERIFIED | Label/Value table; EditableCell per value; getFieldLabel for labels; 4 tests pass |
| `frontend/src/components/LineItemsTable.tsx` | Multi-column line items table | VERIFIED | Derives columns from first item; EditableCell per cell |
| `frontend/src/components/DocTypeBar.tsx` | Doc type badge + override dropdown | VERIFIED | DOC_TYPE_LABELS badge; Select with all VALID_DOC_TYPES; onOverride callback |
| `src/main.py` | FastAPI routers with /api prefix + GET-only SPA fallback | VERIFIED | Lines 47-51: prefix="/api" on all API routers; line 64: @app.get SPA fallback is GET-only |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| frontend/vite.config.ts | http://localhost:8000 | server.proxy without rewrite | WIRED | Lines 8-13: '/api' proxy target with changeOrigin:true; no rewrite lambda (removed in gap closure commit 90ce1b6) |
| frontend/src/lib/api.ts | src/api/routes/extract.py | POST /api/extract | WIRED | api.ts line 7: fetch('/api/extract'); FastAPI line 47: prefix="/api"; runtime introspection confirms ['POST'] /api/extract |
| frontend/src/lib/api.ts | src/api/routes/jobs.py | GET /api/jobs/{id} | WIRED | api.ts line 16: fetch('/api/jobs/{jobId}'); FastAPI line 48: jobs_router prefix="/api" |
| frontend/src/lib/api.ts | src/api/routes/patch.py | PATCH /api/jobs/{id}/fields | WIRED | api.ts line 33: fetch('/api/jobs/{jobId}/fields'); FastAPI line 51: patch_router prefix="/api" |
| frontend/src/lib/api.ts | src/api/routes/export.py | GET /api/jobs/{id}/export | WIRED | api.ts line 46: /api/jobs/{jobId}/export; FastAPI line 50: export_router prefix="/api" |
| src/main.py SPA fallback | frontend/dist/index.html | @app.get GET-only catch-all | WIRED | Line 64: @app.get("/{full_path:path}") — only catches GET; POST /api/extract is no longer absorbed |
| frontend/src/App.tsx | frontend/src/hooks/useJobPoller.ts | activates when phase.tag === 'processing' | WIRED | App.tsx: jobId set from processing phase; useJobPoller called with jobId |
| frontend/src/hooks/useJobPoller.ts | frontend/src/lib/api.ts | calls api.getJob() | WIRED | useJobPoller.ts: await api.getJob(jobId) |
| frontend/src/components/ReviewTable.tsx | frontend/src/components/EditableCell.tsx | each value cell is an EditableCell | WIRED | ReviewTable.tsx: EditableCell in TableCell with onSave wired to onFieldSave prop |
| frontend/src/App.tsx | frontend/src/lib/api.ts | CSV download uses api.exportUrl | WIRED | App.tsx: window.open(api.exportUrl(currentJobId), '_blank') |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|---------|
| REV-01 | 05-01, 05-03, 05-04 | User can see all extracted fields in a review table before downloading CSV | SATISFIED | ReviewTable renders all header fields as two-column Label/Value table; wired in App.tsx review phase; 4 ReviewTable tests pass |
| REV-02 | 05-01, 05-03, 05-04 | User can edit any extracted field value inline | SATISFIED | EditableCell handles click-to-edit with blur/Enter save; handleFieldSave calls api.patchFields via PATCH /api/jobs/{id}/fields; 8 EditableCell tests pass |
| REV-03 | 05-01, 05-03, 05-04 | Fields that could not be extracted shown as "Not found" | SATISFIED | EditableCell renders italic+muted style for "Not found"; emptyFromNotFound guard prevents accidental PATCH; test cases verify this behavior |
| REV-04 | 05-01, 05-02, 05-04 | User can see extraction progress with spinner and status text | SATISFIED | useJobPoller polls at 1500ms; ProgressView renders Loader2 + getStatusText(); 4 status stages mapped; 6 ProgressView tests pass |

**Orphaned requirements check:**
- REV-05 (edited values reflected in CSV) is assigned to Phase 4 in REQUIREMENTS.md traceability — not a Phase 5 requirement. Not orphaned.
- Phase 5 owns exactly REV-01, REV-02, REV-03, REV-04 per REQUIREMENTS.md. All four are satisfied.
- No orphaned Phase 5 requirements exist.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| frontend/src/components/DocTypeBar.tsx | 23 | `placeholder="Override type"` in SelectValue | Info | Legitimate UX placeholder text in an interactive Select control; not a stub |

No blocker or warning anti-patterns found.

---

### Human Verification Required

#### 1. Re-run UAT Test 2: Live browser upload (priority)

**Test:** Start the FastAPI backend (`uvicorn src.main:app --reload`). Navigate to http://localhost:8000. Drag or click to upload a PDF or image file.
**Expected:** File upload triggers POST /api/extract and returns 202 with a job ID — no 405 error. Processing spinner appears. After completion, review table loads with extracted fields.
**Why human:** The 405 fix was verified programmatically (route introspection confirms POST /api/extract is explicitly registered; 61 tests pass) but the actual browser upload flow has not been re-run against the live server since the fix was applied. This is the previously failing UAT test and should be re-confirmed before the phase is considered fully closed.

#### 2. Drag-and-drop visual feedback

**Test:** Open the app in a browser, drag a PDF file over the upload zone without releasing.
**Expected:** The zone border changes to the primary accent color and the background lightens slightly (border-primary bg-primary/5 classes activate via isDragActive).
**Why human:** CSS class toggling from isDragActive cannot be triggered by static analysis; requires browser interaction.

#### 3. End-to-end inline edit and PATCH

**Test:** After successful processing, click any value cell in the review table, change the text, then press Enter or click elsewhere.
**Expected:** The input disappears, the updated value displays in the cell, and PATCH /api/jobs/{id}/fields is called (visible in browser network tab).
**Why human:** Requires a live backend with a processed job.

#### 4. Document type override re-extraction flow

**Test:** On the review page, open the "Override type" dropdown and select a different document type.
**Expected:** The UI transitions back to the processing spinner, polls until complete, then returns to review with fields restructured for the new doc type.
**Why human:** Requires a live backend job and real polling cycle.

#### 5. CSV download and done state transition

**Test:** On the review page, click "Download CSV".
**Expected:** A CSV file downloads in the browser. The UI transitions to show only the "Upload another document" button.
**Why human:** window.open() download behavior and phase transition to done require browser execution.

---

### Gaps Summary

No gaps remain. All 14 observable truths are verified, all artifacts exist and are substantive and wired, all 10 key links are confirmed in source code, all four Phase 5 requirements (REV-01 through REV-04) are satisfied, and 61/61 pytest tests pass.

**Gap closed since previous VERIFICATION.md:**
The single blocker found during UAT — `POST /api/extract` returning 405 because FastAPI routers lacked the `/api` prefix — was resolved by gap closure plan 05-04.

Root cause: FastAPI routers were mounted without prefix; in production mode the SPA fallback `@app.get("/{full_path:path}")` absorbed `POST /api/extract` and returned 405. The Vite proxy rewrite (which stripped `/api` in dev mode) masked the mismatch during development.

Fix applied (commits 90ce1b6, 340d0ae):
- `src/main.py`: All five API routers now use `prefix="/api"` — routes live at `/api/extract`, `/api/jobs/*`, etc.
- `frontend/vite.config.ts`: Proxy rewrite lambda removed — dev and production now agree on `/api/*` paths.
- All 61 pytest tests updated to `/api/*` URLs; 61/61 pass.

A human re-run of UAT Test 2 (browser file upload) is recommended to confirm the fix works end-to-end in a live server context.

---

_Verified: 2026-03-24T14:30:00Z_
_Verifier: Claude (gsd-verifier)_
_Re-verification after gap closure plan 05-04_
