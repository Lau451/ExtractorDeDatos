---
status: complete
phase: 03-csv-export
source: [03-01-SUMMARY.md, 03-02-SUMMARY.md, 03-03-SUMMARY.md]
started: 2026-03-22T03:00:00Z
updated: 2026-03-23T03:21:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

[testing complete]

## Tests

### 1. Export CSV for Completed Job
expected: Call GET /jobs/{job_id}/export on a completed job. Response is 200, Content-Type is text/csv, Content-Disposition header includes a filename, and the body contains CSV data.
result: fixed
reported: "error 409"
fix: "set_raw_text() in 03-03 — status='complete' now only set by set_extraction_result() at end of pipeline"
severity: resolved

### 2. 404 for Unknown Job
expected: Call GET /jobs/nonexistent-id/export. Response is 404 (job not found).
result: pass

### 3. 409 for Incomplete Job
expected: Call GET /jobs/{job_id}/export on a job that is still processing (not complete). Response is 409 (conflict — job not ready for export).
result: pass

### 4. CSV Opens Correctly in Excel (UTF-8 BOM)
expected: Open the downloaded CSV file in Excel or a text editor. It should open without garbled characters — special characters (accents, symbols) display correctly because the file starts with a UTF-8 BOM marker.
result: pass

### 5. CSV Column Order Matches Schema
expected: Open any exported CSV. Columns appear in the same order as the document's schema fields (e.g., for a purchase order: order fields first, then line-item fields). No random column ordering.
result: skipped

### 6. Line Items Expand to Multiple Rows
expected: Export a document type that has line items (purchase order, invoice, or supplier comparison) with 2+ line items. Each line item appears as its own row in the CSV, with header fields (like document number, date) repeated on every row.
result: pass

### 7. None Fields Appear as Empty Cells
expected: Export a document where some optional fields have no value. Those fields appear as empty cells in the CSV — never as the text "None".
result: pass

## Summary

total: 7
passed: 6
issues: 0
fixed: 1
pending: 0
skipped: 1

## Gaps

- truth: "GET /jobs/{job_id}/export returns 200 with CSV for a completed job"
  status: failed
  reason: "User reported: error 409"
  severity: major
  test: 1
  root_cause: "Status collision: set_complete() in ingestion/service.py line 32 sets status='complete' (with extraction_result=None) before calling run_extraction_pipeline (line 33), which immediately overwrites status to 'classifying'. If export is called while extraction is in-flight, the status is not 'complete', triggering the 409 gate. The fix: do not call set_complete() mid-pipeline; 'complete' should only be set by set_extraction_result() at the end of the full pipeline."
  artifacts:
    - path: "src/ingestion/service.py"
      issue: "line 32 calls set_complete() (sets status='complete') then line 33 starts extraction pipeline which immediately overwrites status to 'classifying'"
    - path: "src/core/job_store.py"
      issue: "set_complete() sets status='complete' with extraction_result=None — inconsistent with export requirements"
  missing:
    - "Remove or replace set_complete() call in ingestion/service.py — use an intermediate status (e.g., keep 'processing') instead of 'complete' to signal ingestion-done"
    - "Ensure 'complete' status is only set by set_extraction_result() at end of full pipeline"
  debug_session: ".planning/debug/export-409-complete-job.md"
