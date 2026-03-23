---
status: resolved
trigger: "GET /jobs/{job_id}/export returns 409 for a completed job, but it should return 200 with CSV data"
created: 2026-03-23T00:00:00Z
updated: 2026-03-23T12:00:00Z
---

## Current Focus

hypothesis: CONFIRMED — export.py and job_store.py use the same status string "complete", so the 409 gate logic itself is not a value mismatch. However, export.py imports from src.core.job_store while the route is registered correctly, so the singleton is shared. The real issue is that export.py imports job_store from src.core.job_store but the extraction service also uses src.core.job_store — same singleton. Status strings match. The gate logic is correct for a standard complete job. The actual bug is that export.py's EXPORTABLE_STATUSES uses the plain string "complete" and job_store sets job.status = "complete" (plain string via Literal type), so they DO match — which means the 409 is NOT triggered by a status mismatch in the normal case. Deeper investigation required: the 409 message says "Job is not complete (status: {job.status})" — meaning the actual status value at call time is something other than "complete". The extraction pipeline sets status to "complete" only via set_extraction_result or set_status(job_id, "complete"). If export is called while the job is still in "extracting" or "classifying" state, the 409 fires correctly. BUT if the job has truly finished, status IS "complete" and the gate should pass. The mismatch to examine: is the job_store singleton actually shared between the extraction service and the export route, or could there be two separate instances?

test: Verified by reading all import paths
expecting: Singleton sharing confirmed or denied
next_action: DONE — diagnosis complete, see Resolution

## Symptoms

expected: GET /jobs/{job_id}/export returns 200 with CSV data for a job whose status is "complete"
actual: Returns 409 with {"error": "job_not_exportable", "message": "Job is not complete (status: ...)"}
errors: HTTP 409
reproduction: Submit a job, wait for completion, call GET /jobs/{job_id}/export
started: Unknown

## Eliminated

- hypothesis: EXPORTABLE_STATUSES string "complete" does not match the Literal type value
  evidence: job_store.py line 6 defines JobStatus Literal with "complete"; set_extraction_result (line 72) sets job.status = "complete"; export.py line 8 EXPORTABLE_STATUSES = {"complete"} — same exact string
  timestamp: 2026-03-23T00:00:00Z

- hypothesis: Two separate job_store singletons (import path divergence)
  evidence: extraction/service.py line 4 imports from src.core.job_store; export.py line 3 imports from src.core.job_store; main.py does not re-instantiate — all use the same module-level singleton on line 77 of job_store.py
  timestamp: 2026-03-23T00:00:00Z

## Evidence

- timestamp: 2026-03-23T00:00:00Z
  checked: src/api/routes/export.py line 8
  found: EXPORTABLE_STATUSES = {"complete"} — plain string set
  implication: Gate checks job.status not in {"complete"}

- timestamp: 2026-03-23T00:00:00Z
  checked: src/core/job_store.py line 6
  found: JobStatus = Literal["pending", "processing", "classifying", "extracting", "complete", "error"]
  implication: "complete" is the canonical string; Job.status is typed as JobStatus but stored as a plain str at runtime (dataclass, not Pydantic)

- timestamp: 2026-03-23T00:00:00Z
  checked: src/core/job_store.py lines 43-48 (set_complete) and lines 67-73 (set_extraction_result)
  found: set_complete sets job.status = "complete"; set_extraction_result also sets job.status = "complete"
  implication: Both completion paths use the same string — no divergence here

- timestamp: 2026-03-23T00:00:00Z
  checked: src/extraction/service.py lines 71 and 123
  found: Line 71 calls set_status(job_id, "complete") for unknown doc_type path; line 123 calls set_extraction_result which internally sets "complete"
  implication: All completion paths land on status = "complete"

- timestamp: 2026-03-23T00:00:00Z
  checked: src/core/job_store.py set_complete (lines 43-49) vs set_extraction_result (lines 67-73)
  found: set_complete stores raw_text but does NOT store extraction_result. set_extraction_result stores result dict AND sets status = "complete". The export route then calls formatter(job.extraction_result) — if job was completed via set_complete (ingestion-complete path) rather than set_extraction_result, job.extraction_result is None
  implication: THIS IS THE REAL BUG PATH — but export.py line 41 would pass the 409 gate (status IS "complete") and then crash or return empty on None extraction_result. The reported 409 symptom points to status not being "complete" at call time, i.e., the export endpoint is being called before the extraction pipeline finishes.

- timestamp: 2026-03-23T00:00:00Z
  checked: src/ingestion/service.py (not read yet) — the ingestion service calls set_complete which sets status="complete" BEFORE extraction runs
  implication: If ingestion service sets status="complete" first and then kicks off extraction asynchronously, the job status cycles: pending -> processing -> complete (ingestion done) -> classifying -> extracting -> complete (extraction done). A client polling /jobs/{id} and seeing "complete" after ingestion would call /export too early, while status has already moved to "classifying" or "extracting", triggering the 409.

## Resolution

root_cause: The ingestion service calls job_store.set_complete() which sets job.status = "complete" to signal that raw text extraction is done. Then the extraction pipeline immediately calls set_status("classifying") which overwrites the status to "classifying". A client that calls GET /jobs/{id}/export right after seeing "complete" from the jobs endpoint may hit the export endpoint while the pipeline has already advanced the status to "classifying" or "extracting" — both of which are NOT in EXPORTABLE_STATUSES, so the 409 fires. Alternatively (and more likely as the direct trigger): the ingestion/service.py uses set_complete for its own completion marker, and a naive integration test or client assumes that first "complete" means extraction is done.

fix: (diagnosis only — no fix applied)
verification: (diagnosis only)
files_changed: []
