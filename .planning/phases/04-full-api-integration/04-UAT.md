---
status: complete
phase: 04-full-api-integration
source: 04-01-SUMMARY.md
started: 2026-03-23T00:00:00Z
updated: 2026-03-23T00:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: Kill any running server. Start fresh with `uvicorn src.main:app --reload` (or equivalent). Server boots without errors, the lifespan startup runs (background cleanup task created), and GET /health returns {"status": "ok"}.
result: pass

### 2. PATCH endpoint — update a field
expected: Upload a document and wait for extraction to complete (status: complete). Then send PATCH /jobs/{id}/fields with a JSON body like {"fields": {"buyer_name": "Acme Corp"}}. Response is 200 with the full job result, and the patched field reflects the new value.
result: pass

### 3. PATCH on unknown job returns 404
expected: Send PATCH /jobs/nonexistent-id/fields with any fields body. Response is 404 with an appropriate error message.
result: issue
reported: "He added the field, it didn't throw an error"
severity: major

### 4. PATCH on in-progress job returns 409
expected: Upload a document (do NOT wait for it to finish). Immediately send PATCH /jobs/{id}/fields. Response is 409 (Conflict) since the job is not yet complete.
result: pass

### 5. PATCH then export — corrected value in CSV
expected: Upload a PO document, wait for extraction to complete. PATCH a field (e.g., buyer_name). Then GET /jobs/{id}/export to download the CSV. The CSV contains the corrected value, not the original extracted value.
result: pass

## Summary

total: 5
passed: 4
issues: 1
pending: 0
skipped: 0

## Gaps

- truth: "PATCH /jobs/{id}/fields returns 404 for unknown job IDs"
  status: failed
  reason: "User reported: He added the field, it didn't throw an error"
  severity: major
  test: 3
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""
