---
status: complete
phase: 02-extraction-pipeline
source: [02-01-SUMMARY.md, 02-02-SUMMARY.md, 02-03-SUMMARY.md, 02-04-SUMMARY.md]
started: 2026-03-20T00:30:00Z
updated: 2026-03-20T00:30:00Z
---

## Current Test

## Current Test

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: Kill any running server. Start fresh with `uvicorn src.main:app --reload`. Server boots without errors. The new PATCH /jobs/{id}/doc_type endpoint appears in http://localhost:8000/docs.
result: pass

### 2. Upload triggers auto-extraction
expected: POST a document to POST /extract (e.g., a PDF or image). Poll GET /jobs/{id} — the status should progress through "classifying" → "extracting" → "complete" automatically. No manual trigger needed.
result: pass

### 3. Classified doc_type in job response
expected: After the job reaches "complete", GET /jobs/{id} returns a "doc_type" field with the classified document type (e.g., "purchase_order", "invoice", "tender_rfq", "quotation", or "supplier_comparison").
result: pass

### 4. Extraction result contains structured fields
expected: GET /jobs/{id} when complete returns "extraction_result" as a JSON object with document-specific fields populated (e.g., for a purchase order: po_number, vendor_name, total_amount, line_items). The value is structured data, not "Not found".
result: pass

### 5. Unknown document shows "Not found" extraction
expected: If a document can't be classified (Gemini returns an unknown type), GET /jobs/{id} returns doc_type as the raw value and extraction_result as "Not found" (the job still reaches "complete", not "error").
result: skipped
reason: difficult to trigger manually

### 6. PATCH doc_type override triggers re-extraction
expected: Given a completed job, send PATCH /jobs/{id}/doc_type with body {"doc_type": "invoice"} (or another valid type). Response is 202. Polling GET /jobs/{id} shows status transitions to "extracting" then back to "complete" with a new extraction_result for the overridden type.
result: pass

### 7. Invalid doc_type returns 422
expected: PATCH /jobs/{id}/doc_type with {"doc_type": "unknown"} or an invalid value like "banana" returns HTTP 422 Unprocessable Entity — the request is rejected without changing the job.
result: pass

## Summary

total: 7
passed: 6
issues: 0
pending: 0
skipped: 1
skipped: 0

## Gaps

[none yet]
