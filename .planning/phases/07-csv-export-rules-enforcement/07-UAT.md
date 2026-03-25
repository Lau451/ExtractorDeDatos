---
status: complete
phase: 07-csv-export-rules-enforcement
source: [07-01-SUMMARY.md, 07-02-SUMMARY.md]
started: 2026-03-25T00:00:00Z
updated: 2026-03-25T00:08:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: Kill any running server/service. Start the FastAPI backend from scratch (e.g., uvicorn src.main:app) and the frontend dev server. Both should boot without errors. A basic API call (e.g., GET /health or the root endpoint) should return a live response.
result: pass

### 2. CSV Download — Descriptive Filename
expected: After processing a document and clicking the Download CSV button, the browser saves the file with a name like `invoice_2026-03-25.csv` (doc_type + today's date). The old `job_{id}_{doc_type}.csv` format should no longer appear.
result: pass

### 3. Missing/Blank Fields Become "Not found" in CSV
expected: Open the downloaded CSV. Any field that was blank, null, or missing in the source document should show the text `Not found` in the CSV cell — not an empty cell or a dash.
result: pass

### 4. Amount and Date Fields Are Normalized
expected: In the downloaded CSV, monetary fields (e.g., total_amount, unit_price) should be formatted as plain numbers (e.g., `1234.56`), and date fields containing "date" in their name (e.g., issue_date, due_date) should be formatted as `YYYY-MM-DD`. Fields like `submission_deadline` and `valid_until` (no "date" substring) are intentionally NOT date-normalized.
result: pass

### 5. Warning Banner Appears When Mandatory Fields Are Missing
expected: Process a document that is missing one or more mandatory fields (e.g., upload an invoice without a vendor name). After clicking Download CSV, an amber/yellow warning banner should appear listing the missing field names. The banner should say something like "Warning: missing fields — [field names]".
result: pass

### 6. Download Button Shows Spinner During Fetch
expected: When the Download CSV button is clicked, the Download icon is replaced by a spinning Loader2 spinner and the button is disabled while the file is being fetched. Once the download completes, the button returns to its normal state.
result: pass

### 7. Phase Stays in Review When Warnings Are Present
expected: After downloading a CSV that has missing mandatory fields (and the warning banner is shown), the UI should remain in the review phase — it should NOT advance to the "done" phase. The user can still see and interact with the document data alongside the warning.
result: pass

### 8. Warning Banner Clears on Reset
expected: After seeing the warning banner, click "Upload another document" (or the reset button). The warning banner should disappear completely. On the next upload and download cycle, warnings should only appear if the new document also has missing mandatory fields.
result: pass

## Summary

total: 8
passed: 8
issues: 0
pending: 0
skipped: 0

## Gaps

[none yet]
