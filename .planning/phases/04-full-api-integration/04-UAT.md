---
status: diagnosed
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
  root_cause: "patch_extraction_result() line 113 uses `job.extraction_result or {}`, silently coercing a None extraction result to empty dict and returning 200 instead of an error. A job can exist with status=complete but extraction_result=None if set_status() was used directly, bypassing the extraction pipeline. The route has no guard for this case."
  artifacts:
    - path: "src/core/job_store.py"
      issue: "patch_extraction_result() line 113: `current = job.extraction_result or {}` silently initializes to empty dict when extraction_result was never set"
    - path: "src/api/routes/patch.py"
      issue: "No guard checking that job.extraction_result is not None before calling patch_extraction_result(); only checks status != complete"
  missing:
    - "In patch.py: guard after status check — if job.extraction_result is None, return 409 or 422"
    - "In job_store.py patch_extraction_result(): replace `or {}` with explicit None check that returns None when extraction_result was never set"
    - "In job_store.py: set_status() should not allow transitioning to 'complete' without extraction_result being set (invariant enforcement)"
  debug_session: ""
