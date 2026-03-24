---
phase: 05-web-ui
verified: 2026-03-24T00:48:45Z
status: passed
score: 12/12 must-haves verified
re_verification: false
gaps: []
human_verification:
  - test: "Upload a PDF and observe the drag-and-drop zone visual behavior"
    expected: "Drop zone border turns primary color and background lightens when a file is dragged over"
    why_human: "isDragActive CSS state change cannot be triggered by automated grep; requires browser interaction"
  - test: "Upload a document, wait for processing to complete, then edit a field value in the review table"
    expected: "Clicking a cell opens an inline input; pressing Enter or blurring saves the value; the page does not refresh"
    why_human: "End-to-end PATCH flow with live backend requires a running server and real extraction"
  - test: "On the review table, override the document type via the dropdown"
    expected: "UI transitions back to the processing/spinner state and then returns to review with updated fields for the new doc type"
    why_human: "Requires a live backend job and real polling cycle to verify the re-extraction transition"
  - test: "Click 'Download CSV' on the review page"
    expected: "Browser downloads a CSV file; UI transitions to the done state showing 'Upload another document'"
    why_human: "window.open() download behavior and state transition require browser execution"
---

# Phase 05: Web UI Verification Report

**Phase Goal:** Build the complete web UI for the document extraction service — upload, processing, review/edit, and export flows — so end-users can interact with the extraction pipeline entirely through the browser.
**Verified:** 2026-03-24T00:48:45Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Frontend project builds without errors via npm run build | VERIFIED | Build exits 0; 430KB bundle produced in frontend/dist/ |
| 2 | Vite dev server proxies /api/* to localhost:8000 | VERIFIED | vite.config.ts line 9-14: proxy entry with target http://localhost:8000 and rewrite stripping /api prefix |
| 3 | TypeScript types match the actual JobResponse shape from the backend | VERIFIED | frontend/src/types/api.ts exports JobResponse with all 7 fields matching src/api/models.py exactly |
| 4 | All five API endpoints have typed fetch wrappers | VERIFIED | frontend/src/lib/api.ts: postExtract, getJob, patchDocType, patchFields, exportUrl — all present and wired to correct paths |
| 5 | Field label mappings exist for all extraction schema fields across all 5 doc types | VERIFIED | frontend/src/lib/fieldLabels.ts: 40+ keys covering PO, Invoice, Tender/RFQ, Quotation, Supplier Comparison header + line item fields |
| 6 | User can drag or pick a file and see a processing spinner with status text | VERIFIED | UploadZone.tsx uses useDropzone with all 6 accepted MIME types; App.tsx transitions phase to 'processing' on upload success; ProgressView renders Loader2 + getStatusText() |
| 7 | Status text updates as job status changes: Uploading -> Parsing -> Classifying -> Extracting | VERIFIED | statusText.ts maps all 4 statuses; useJobPoller polls at 1500ms and updates status; ProgressView renders getStatusText(status) |
| 8 | Polling stops when status is complete or error | VERIFIED | useJobPoller.ts lines 26-31: clearInterval called for both 'complete' and 'error' statuses before firing callbacks |
| 9 | Error state shows an inline banner with human-readable message and Try again button | VERIFIED | ProgressView.tsx renders AlertCircle + "Processing failed" + getErrorMessage(errorCode) + "Try again" Button; all 6 ProgressView tests pass |
| 10 | User can see all extracted header fields in a two-column Label/Value table | VERIFIED | ReviewTable.tsx renders two-column Table with getFieldLabel(key) labels and EditableCell per value; excludes lineItemKey row; all 4 ReviewTable tests pass |
| 11 | User can click any value cell, edit it, and the PATCH request fires on blur or Enter | VERIFIED | EditableCell.tsx: commit() called on blur and Enter keydown; App.tsx handleFieldSave calls api.patchFields; all 8 EditableCell tests pass including blur-saves-on-change |
| 12 | Fields with value 'Not found' display as muted gray italic text; clicking opens empty input; empty blur does NOT fire PATCH | VERIFIED | EditableCell.tsx: cn() applies 'text-muted-foreground italic' when value === 'Not found'; draft initialized to '' for Not found; commit() guards with emptyFromNotFound check |

**Score:** 12/12 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `frontend/package.json` | Project manifest with all dependencies | VERIFIED | Contains react-dropzone, lucide-react, tailwindcss, vitest, @testing-library/react |
| `frontend/vite.config.ts` | Vite config with proxy and Tailwind plugin | VERIFIED | proxy to localhost:8000, tailwindcss() plugin, @ alias, test config present |
| `frontend/src/lib/api.ts` | Typed API wrappers for all 5 endpoints | VERIFIED | postExtract(/api/extract), getJob(/api/jobs/{id}), patchDocType, patchFields, exportUrl — all substantive with real fetch calls |
| `frontend/src/types/api.ts` | TypeScript interfaces matching backend models | VERIFIED | JobResponse matches src/api/models.py; all 7 fields present including error_code, extraction_result |
| `frontend/src/lib/fieldLabels.ts` | Human-readable labels for all extraction fields | VERIFIED | po_number, invoice_number, tender_reference, quote_number, project_name all present; LINE_ITEM_KEYS; getFieldLabel() fallback |
| `frontend/src/components/UploadZone.tsx` | Drag-and-drop file upload with react-dropzone | VERIFIED | useDropzone with 6 MIME types; isDragActive; border-primary drag-over state; onFileAccepted callback |
| `frontend/src/components/ProgressView.tsx` | Spinner + status text + error banner | VERIFIED | Loader2 + animate-spin for active; AlertCircle + "Processing failed" + getErrorMessage + "Try again" for error |
| `frontend/src/hooks/useJobPoller.ts` | Polling hook with cleanup | VERIFIED | setInterval at 1500ms; clearInterval in useEffect cleanup; intervalRef.current; pollingKey dependency; 'complete' and 'error' handled |
| `frontend/src/App.tsx` | State machine driving the linear flow | VERIFIED | 4-phase tagged union (upload/processing/review/done); all components wired; handleFieldSave, handleDocTypeOverride, handleLineItemsSave, handleDownloadCSV, handleRetry, handleReset |
| `frontend/src/components/EditableCell.tsx` | Click-to-edit cell with PATCH on blur/Enter | VERIFIED | commit() on blur and Enter; Escape reverts; Not found -> empty draft; all 8 tests pass |
| `frontend/src/components/ReviewTable.tsx` | Two-column header fields table | VERIFIED | "Extracted Fields" heading; filters lineItemKey; uses EditableCell for values; getFieldLabel for labels; all 4 tests pass |
| `frontend/src/components/LineItemsTable.tsx` | Multi-column line items table | VERIFIED | "Line Items" heading; derives column keys from first item; EditableCell per cell; handleCellSave creates deep copy |
| `frontend/src/components/DocTypeBar.tsx` | Doc type badge + override dropdown | VERIFIED | DOC_TYPE_LABELS badge; Select with all VALID_DOC_TYPES; onOverride callback; null guard on onValueChange |
| `src/main.py` | FastAPI static file serving | VERIFIED | spa_fallback route registered after all API routers; StaticFiles + FileResponse; guarded by os.path.isdir(_dist_dir) |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| frontend/vite.config.ts | http://localhost:8000 | server.proxy config | WIRED | Line 9: '/api' proxy target 'http://localhost:8000' with path rewrite |
| frontend/src/lib/api.ts | frontend/src/types/api.ts | import JobResponse | WIRED | Line 1: `import type { ExtractResponse, JobResponse } from '@/types/api'` |
| frontend/src/App.tsx | frontend/src/components/UploadZone.tsx | renders when phase.tag === 'upload' | WIRED | Line 118-123: conditional render on phase.tag === 'upload' renders UploadZone |
| frontend/src/App.tsx | frontend/src/hooks/useJobPoller.ts | activates when phase.tag === 'processing' | WIRED | Line 50-61: jobId set from processing phase; useJobPoller called with jobId |
| frontend/src/hooks/useJobPoller.ts | frontend/src/lib/api.ts | calls api.getJob() | WIRED | Line 23: `const res = await api.getJob(jobId)` |
| frontend/src/components/ProgressView.tsx | frontend/src/lib/statusText.ts | maps status to display text | WIRED | Line 2 import; line 37 `{getStatusText(status)}` |
| frontend/src/components/ProgressView.tsx | frontend/src/lib/errorMessages.ts | maps error_code to message on error | WIRED | Line 3 import; line 21 `{getErrorMessage(errorCode)}` |
| frontend/src/App.tsx | frontend/src/components/ReviewTable.tsx | renders when phase.tag === 'review' | WIRED | Lines 134-144: conditional on phase.tag === 'review' renders ReviewTable |
| frontend/src/components/ReviewTable.tsx | frontend/src/components/EditableCell.tsx | each value cell is an EditableCell | WIRED | Lines 36-39: EditableCell in TableCell with onSave wired to onFieldSave prop |
| frontend/src/components/DocTypeBar.tsx | frontend/src/lib/api.ts | override calls api.patchDocType | WIRED | App.tsx line 86: `await api.patchDocType(currentJobId, newType)` via handleDocTypeOverride callback |
| frontend/src/App.tsx | frontend/src/lib/api.ts | CSV download uses api.exportUrl | WIRED | Line 107: `window.open(api.exportUrl(currentJobId), '_blank')` |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|---------|
| REV-01 | 05-01, 05-03 | User can see all extracted fields in a review table before downloading CSV | SATISFIED | ReviewTable renders all header fields as two-column Label/Value table; wired in App.tsx review phase |
| REV-02 | 05-01, 05-03 | User can edit any extracted field value inline | SATISFIED | EditableCell handles click-to-edit with blur/Enter save; handleFieldSave calls api.patchFields; all 8 EditableCell tests pass |
| REV-03 | 05-01, 05-03 | Fields that could not be extracted shown as "Not found" | SATISFIED | EditableCell renders italic+muted style for "Not found"; empty blur guard prevents accidental PATCH; tests 3, 4, 6 in EditableCell suite verify this |
| REV-04 | 05-01, 05-02 | User can see extraction progress with spinner and status text | SATISFIED | useJobPoller polls at 1500ms; ProgressView renders Loader2 + getStatusText(); status text updates through all 4 backend stages; 6 ProgressView tests pass |

**Orphaned requirements check:** REV-05 (edited values reflected in CSV) is assigned to Phase 4 in REQUIREMENTS.md traceability — not a Phase 5 requirement. No orphaned requirements.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| frontend/src/components/DocTypeBar.tsx | 23 | `placeholder="Override type"` in SelectValue | Info | Legitimate HTML placeholder attribute for UX; not a stub |
| frontend/src/components/ui/select.tsx | 44 | shadcn-generated placeholder forwarding | Info | Auto-generated shadcn component code; not authored stub |

No blocker or warning anti-patterns found. Both flagged occurrences are legitimate UI placeholder text in interactive controls.

---

### Human Verification Required

#### 1. Drag-and-drop visual feedback

**Test:** Open the app in a browser, drag a PDF file over the upload zone without releasing.
**Expected:** The zone border changes to the primary accent color and the background lightens slightly (border-primary bg-primary/5 classes activate via isDragActive).
**Why human:** CSS class toggling from isDragActive state cannot be triggered programmatically via grep; requires a browser interaction.

#### 2. End-to-end inline edit and PATCH

**Test:** Upload a document, wait for extraction to complete, click any value cell in the review table, change the text, then press Enter or click elsewhere.
**Expected:** The input disappears and the updated value displays in the cell. No page refresh occurs. The backend PATCH /jobs/{id}/fields is called (verify in network tab).
**Why human:** Requires a live backend with a processed job; the actual HTTP request firing and state update require runtime verification.

#### 3. Document type override re-extraction flow

**Test:** On the review page, open the "Override type" dropdown and select a different document type.
**Expected:** The UI transitions back to the processing spinner, polls the job until complete, then returns to the review page with fields restructured for the new doc type.
**Why human:** Requires a live backend job, real polling cycle, and visual confirmation of the state transition sequence.

#### 4. CSV download and done state transition

**Test:** On the review page, click "Download CSV".
**Expected:** A CSV file downloads in the browser. The UI transitions to show only the "Upload another document" button (the done phase).
**Why human:** window.open() download and phase transition to done require browser execution; cannot verify file download programmatically.

---

### Gaps Summary

No gaps found. All 12 observable truths are verified, all artifacts exist and are substantive and wired, all key links are confirmed in the source code, all 4 requirements are satisfied, and the test suite passes at 18/18.

The phase delivers the complete web UI goal: upload zone, polling-based progress view, two-column review table with inline editing, line items table, document type override dropdown, CSV download, and done state — all wired end-to-end in a 4-phase state machine.

---

_Verified: 2026-03-24T00:48:45Z_
_Verifier: Claude (gsd-verifier)_
