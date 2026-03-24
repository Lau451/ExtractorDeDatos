---
status: complete
phase: 05-web-ui
source: [05-01-SUMMARY.md, 05-02-SUMMARY.md, 05-03-SUMMARY.md]
started: 2026-03-24T04:00:00Z
updated: 2026-03-24T04:03:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: Kill any running server. Start the FastAPI backend from scratch (uvicorn src.main:app --reload or equivalent). Server boots without errors. Navigate to http://localhost:8000 — the React frontend loads (no blank page, no 404). A basic page title or upload zone is visible.
result: pass

### 2. Upload Zone — Drop or Click to Upload
expected: Open the app. You should see an upload zone (dashed border area). You can either drag a PDF/image file onto it or click to open a file picker. Accepted types: PDF, PNG, JPG, JPEG, WEBP, TIFF. If you drop an unsupported file type (e.g., .txt), an inline rejection error appears. The upload zone is disabled (non-interactive) while an upload is in progress.
result: issue
reported: "When dragging or searching for the file, nothing happens; POST /api/extract HTTP/1.1 405 Method Not Allowed"
severity: major

### 3. Processing Progress View — Spinner and Status Text
expected: After uploading a valid file, the upload zone disappears and a spinner (animated icon) appears with a status text label describing the current processing stage (e.g., "Uploading…", "Extracting…", "Processing…"). The spinner continues polling until the job completes.
result: skipped
reason: blocked by Test 2 — upload does not work (405 on POST /api/extract)

### 4. Processing Error State — Error Banner and Try Again
expected: If the backend returns an error during processing (or to simulate: use a corrupted/invalid file), the spinner is replaced by an error banner. The banner shows an alert icon, "Processing failed" heading, a human-readable error message, and a "Try again" button. Clicking "Try again" resets back to the upload zone.
result: skipped
reason: blocked by Test 2 — upload does not work

### 5. Review Table — Header Fields in Two-Column Format
expected: After successful processing, the review phase appears. A two-column table (Label | Value) shows all extracted header fields. Labels are human-readable (e.g., "Invoice Number", not "invoice_number"). Each row corresponds to one extracted field from the document.
result: skipped
reason: blocked by Test 2 — upload does not work

### 6. Inline Cell Editing — Click to Edit, PATCH on Blur/Enter
expected: In the review table, click on any value cell. The cell switches to an editable text input. You can type a new value. Pressing Enter or clicking away (blur) saves the change — a PATCH request fires to update the field. Pressing Escape cancels editing without saving.
result: skipped
reason: blocked by Test 2 — upload does not work

### 7. Not Found Fields — Muted Gray Italic Display
expected: Fields that were not found in the document appear in the value column as muted/gray italic text (e.g., "Not found"). Clicking on a "not found" cell opens an empty text input for manual entry. Leaving the input empty (blur with no value) does NOT fire a PATCH request.
result: skipped
reason: blocked by Test 2 — upload does not work

### 8. Doc Type Bar — Override Dropdown
expected: At the top of the review view, a badge or label shows the current detected document type (e.g., "Invoice"). A dropdown/select control allows choosing a different doc type. Selecting a new doc type triggers re-extraction — the processing spinner reappears and the review table updates with results for the new doc type.
result: skipped
reason: blocked by Test 2 — upload does not work

### 9. Line Items Table — Conditional Rendering for Applicable Doc Types
expected: For document types that have line items (invoices, purchase orders, etc.), a second table appears below the header fields table, showing the line items in a multi-column editable grid. For doc types without line items, this table does not appear.
result: skipped
reason: blocked by Test 2 — upload does not work

### 10. Download CSV
expected: In the review phase, a "Download CSV" button is present. Clicking it downloads a CSV file containing the extracted data. The file downloads (browser download bar appears or a file is saved).
result: skipped
reason: blocked by Test 2 — upload does not work

### 11. Done Phase — Upload Another Document
expected: After downloading or completing review, there is a way to reach the "done" state (or it transitions automatically). The done phase shows an "Upload another document" button. Clicking it resets the app back to the upload zone, ready for a new file.
result: skipped
reason: blocked by Test 2 — upload does not work

## Summary

total: 11
passed: 1
issues: 1
pending: 0
skipped: 9

## Gaps

- truth: "Dropping or selecting a file triggers POST /api/extract and upload proceeds"
  status: failed
  reason: "User reported: When dragging or searching for the file, nothing happens; POST /api/extract HTTP/1.1 405 Method Not Allowed"
  severity: major
  test: 2
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""
