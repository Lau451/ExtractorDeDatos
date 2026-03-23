---
phase: 03-csv-export
verified: 2026-03-23T04:00:00Z
status: passed
score: 16/16 must-haves verified
re_verification:
  previous_status: passed
  previous_score: 13/13
  gaps_closed:
    - "GET /jobs/{id}/export returns 200 with CSV for a completed job (status collision bug fixed)"
    - "Status 'complete' is only reached after extraction_result is populated"
    - "Ingestion completion stores raw_text without prematurely setting status to complete"
  gaps_remaining: []
  regressions: []
---

# Phase 3: CSV Export Verification Report

**Phase Goal:** Implement CSV export feature — GET /jobs/{id}/export endpoint returns properly formatted CSV for completed jobs
**Verified:** 2026-03-23
**Status:** PASSED
**Re-verification:** Yes — after gap closure (Plan 03 fixed status collision bug reported in UAT)

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Each of the five document types produces a CSV with its own distinct column schema | VERIFIED | `formatters.py` 136 lines; 5 formatters with distinct schemas (17, 19, 16, 8, 12 columns); `test_distinct_schemas` asserts all 5 counts unique |
| 2 | CSV bytes begin with UTF-8 BOM (b'\xef\xbb\xbf') | VERIFIED | `_make_csv_bytes` writes `"\ufeff"` at buffer position 0 before csv.writer; `test_csv_has_bom` and `test_export_complete_job` both assert `b"\xef\xbb\xbf"` prefix |
| 3 | CSV column order matches the Pydantic model field declaration order | VERIFIED | `model_fields` iterated directly for column names; 5 `test_column_order_*` tests pass with exact expected column lists |
| 4 | Missing/None field values render as empty cells, never as the string 'None' | VERIFIED | `("" if v is None else v)` applied in both `_format_line_item_type` and `_format_header_only_type`; `test_none_values_are_empty_cells` confirms |
| 5 | Line-item doc types produce one row per line item with header fields repeated | VERIFIED | `_format_line_item_type` repeats `header_values` per item row; `test_line_item_rows_repeat_headers` confirms PO with 2 items yields 3 rows |
| 6 | Header-only doc types produce a single row with only header columns | VERIFIED | `_format_header_only_type` always passes a single-element row list; `test_header_only_single_row` confirms TenderRFQ produces exactly 2 rows |
| 7 | Documents with zero line items produce a single row with empty line-item columns | VERIFIED | Zero-items branch: `[None] * len(item_fields)` → cleaned to `""`; `test_zero_line_items_single_row` confirms |
| 8 | User can download a CSV file from a completed job via GET /jobs/{id}/export | VERIFIED | Route at `/jobs/{job_id}/export` in `export.py`; `test_export_complete_job` asserts 200, BOM, correct headers |
| 9 | Non-existent job returns HTTP 404 with JSON error body | VERIFIED | 404 branch in `export.py` lines 16-20; `test_export_404` asserts `{"error": "job_not_found"}` |
| 10 | Job still processing returns HTTP 409 with JSON explanation | VERIFIED | 409 status-gate in `export.py` lines 22-29; `test_export_409_not_complete` asserts `"not complete"` in message |
| 11 | Job with doc_type 'unknown' returns HTTP 409 | VERIFIED | 409 doc_type-gate in `export.py` lines 31-38; `test_export_409_unknown_doc_type` asserts `"unknown"` in message |
| 12 | Response Content-Type is 'text/csv; charset=utf-8' | VERIFIED | `media_type="text/csv; charset=utf-8"` in `export.py` line 45; `test_export_content_type` asserts exact header value |
| 13 | Content-Disposition filename follows 'job_{id}_{doc_type}.csv' pattern | VERIFIED | `f'attachment; filename="{filename}"'` with `filename = f"job_{job_id}_{job.doc_type}.csv"`; `test_export_filename` asserts exact pattern |
| 14 | GET /jobs/{id}/export returns 200 with CSV body for a fully completed job (end-to-end status machine) | VERIFIED | Status collision eliminated: `ingestion/service.py` line 32 calls `set_raw_text()` (not `set_complete()`); `complete` only reached via `set_extraction_result()` at pipeline end or explicit `set_status("complete")` for unknown doc_type |
| 15 | Status 'complete' is only reached after extraction_result is populated | VERIFIED | `job_store.set_extraction_result()` (line 74-80) is the sole path to `status="complete"` for extractable jobs; unknown doc_type uses explicit `set_status` at classification end (no extraction_result needed — correct) |
| 16 | Ingestion completion stores raw_text without prematurely setting status to complete | VERIFIED | `ingestion/service.py` line 32: `await job_store.set_raw_text(job_id, raw_text=markdown)`; `set_raw_text()` (job_store lines 43-48) sets only `raw_text` and `updated_at` — status untouched |

**Score:** 16/16 truths verified

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/export/__init__.py` | Module init | VERIFIED | Exists (empty, as expected for Python package init) |
| `src/export/formatters.py` | Five formatters + FORMATTER_REGISTRY + _make_csv_bytes | VERIFIED | 136 lines; all 5 formatters, both private helpers, registry with 5 keys — substantive and wired |
| `tests/test_export.py` | Unit and integration tests covering all formatters and endpoint | VERIFIED | 429 lines; 12 unit tests + 6 integration tests; no xfail markers |
| `src/api/routes/export.py` | GET /jobs/{id}/export endpoint with 404/409 gates | VERIFIED | 49 lines; all branches present: 404, 409 (status), 409 (doc_type), 200 CSV response |
| `src/main.py` | Export router registration | VERIFIED | `from src.api.routes.export import router as export_router` on line 4; `app.include_router(export_router)` on line 14 |
| `src/core/job_store.py` | set_raw_text() method that stores text without changing status | VERIFIED | Lines 43-48: acquires lock, sets `job.raw_text` and `job.updated_at`, does NOT touch `job.status` |
| `src/ingestion/service.py` | Fixed pipeline — uses set_raw_text, never set_complete mid-pipeline | VERIFIED | Line 32: `await job_store.set_raw_text(job_id, raw_text=markdown)`; `set_complete` absent from file |
| `tests/test_ingestion.py` | Updated assertions — ingestion leaves job in 'processing' | VERIFIED | All 5 ingestion test functions assert `job.status == "processing"`; helper docstring updated to match |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/export/formatters.py` | `src/extraction/schemas/*.py` | `model_validate()` and `model_fields` iteration | VERIFIED | `model_validate` called in both private helpers; `model_fields` iterated for column ordering |
| `src/export/formatters.py` | `src/extraction/schemas/registry.py` | FORMATTER_REGISTRY mirrors SCHEMA_REGISTRY keys | VERIFIED | `test_formatter_registry_has_all_types` asserts `set(FORMATTER_REGISTRY.keys()) == set(SCHEMA_REGISTRY.keys())` |
| `src/api/routes/export.py` | `src/export/formatters.py` | `FORMATTER_REGISTRY[job.doc_type](job.extraction_result)` | VERIFIED | Line 40: `formatter = FORMATTER_REGISTRY[job.doc_type]`; line 41: `csv_bytes = formatter(job.extraction_result)` |
| `src/api/routes/export.py` | `src/core/job_store.py` | `job_store.get(job_id)` | VERIFIED | Line 14: `job = await job_store.get(job_id)` |
| `src/main.py` | `src/api/routes/export.py` | `app.include_router(export_router)` | VERIFIED | Import on line 4; `app.include_router(export_router)` on line 14 |
| `src/ingestion/service.py` | `src/core/job_store.py` | `set_raw_text()` replaces `set_complete()` | VERIFIED | Line 32 of ingestion/service.py: `await job_store.set_raw_text(job_id, raw_text=markdown)`; `set_complete` not present in file |
| `src/extraction/service.py` | `src/core/job_store.py` | `set_extraction_result()` sets status=complete (sole complete path for extractable jobs) | VERIFIED | `extraction/service.py` line 123: `await job_store.set_extraction_result(job_id, result.model_dump())`; `set_extraction_result` lines 74-80 sets both `extraction_result` and `status="complete"` atomically |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| EXP-01 | 03-01, 03-03 | User can download the extraction result as a CSV file | SATISFIED | GET /jobs/{id}/export returns 200 with CSV bytes for complete jobs; status collision bug fixed in 03-03 ensures 'complete' is only reached with extraction_result populated |
| EXP-02 | 03-01 | CSV column order matches the predefined schema for the detected document type | SATISFIED | Column order driven by `model_fields` iteration; all five `test_column_order_*` tests pass with exact expected column lists |
| EXP-03 | 03-01 | CSV file is encoded as UTF-8 with BOM (utf-8-sig) for correct display in Excel | SATISFIED | `"\ufeff"` written as first character in `_make_csv_bytes`; BOM bytes confirmed in unit test and integration test |
| EXP-04 | 03-01 | Each document type produces its own CSV structure (distinct column schemas) | SATISFIED | Five distinct schemas with column counts 17, 19, 16, 8, 12 — all unique; `test_distinct_schemas` confirms |
| API-04 | 03-02, 03-03 | API exposes a GET /jobs/{id}/export endpoint that returns the final CSV file | SATISFIED | Endpoint live at `/jobs/{job_id}/export`; 404/409/200 branches all tested and passing; premature-complete window eliminated |

No orphaned requirements. All five IDs declared across plan frontmatter are accounted for and satisfied. REQUIREMENTS.md traceability table marks all five as Complete under Phase 3.

---

## Anti-Patterns Found

No anti-patterns detected. Scanned files:
- `src/export/formatters.py`
- `src/api/routes/export.py`
- `src/main.py`
- `src/core/job_store.py`
- `src/ingestion/service.py`
- `tests/test_export.py`
- `tests/test_ingestion.py`

No TODO/FIXME/HACK/placeholder comments, no `return null` / `return {}` stubs, no xfail markers remaining in tests. `set_complete()` is retained in job_store for backwards compatibility but is harmless — it is no longer called from any pipeline path.

---

## Human Verification Required

None. All acceptance criteria are programmatically verifiable and have been confirmed via automated tests and direct code inspection.

The one UAT test marked "skipped" (test 5 — CSV Column Order Matches Schema) is fully covered by the five `test_column_order_*` automated unit tests in `tests/test_export.py`.

---

## Test Suite Results

- `python -m pytest tests/test_export.py -x -q` — 18 passed (12 unit + 6 integration)
- `python -m pytest tests/test_ingestion.py -x -q` — 7 passed (all status assertions updated to 'processing')
- `python -m pytest tests/ -x -q` — 49 passed (full suite, zero regressions)
- UAT: 6 passed, 1 fixed (export-409 bug), 1 skipped (covered by automated tests), 0 open

---

## Gap Closure Confirmation

The UAT-reported issue (test 1: "Export CSV for Completed Job" returned 409 instead of 200) was caused by a status collision in the ingestion pipeline:

**Root cause:** `src/ingestion/service.py` called `job_store.set_complete()` on line 32, setting `status='complete'` with `extraction_result=None`. Line 33 immediately called `run_extraction_pipeline()`, which overwrote status to `'classifying'`. The export gate (`status not in {"complete"}`) would fire 409 during this window.

**Fix applied (Plan 03):**
1. `set_raw_text()` added to `JobStore` — stores `raw_text` without touching `status`
2. `ingestion/service.py` line 32 changed from `set_complete()` to `set_raw_text()` — job stays in `'processing'` during pipeline execution
3. `status='complete'` is now exclusively reached via `set_extraction_result()` at end of extraction pipeline (or `set_status("complete")` for `unknown` doc_type, which has no extraction_result to populate)
4. Ingestion tests updated to assert `status == "processing"` post-ingestion (pipeline mocked out)

---

## Summary

Phase 3 goal is fully achieved. The complete CSV export pipeline is wired end-to-end with the status machine fixed:

1. `src/export/formatters.py` — converts extraction result dicts into UTF-8 BOM CSV bytes with schema-correct column ordering for all five document types, proper line-item expansion, and None-to-empty-cell handling.
2. `src/api/routes/export.py` — exposes GET /jobs/{id}/export with 404 gate (job not found), 409 gate (job not complete or unrecognized doc_type), and 200 CSV response with correct `text/csv; charset=utf-8` Content-Type and `job_{id}_{doc_type}.csv` Content-Disposition filename.
3. `src/main.py` — registers the export router.
4. `src/core/job_store.py` + `src/ingestion/service.py` — status machine corrected: `'complete'` is exclusively reached after `extraction_result` is populated, eliminating the premature-complete window that caused 409 export errors.
5. All five requirement IDs (EXP-01, EXP-02, EXP-03, EXP-04, API-04) are satisfied with direct evidence.

---

_Verified: 2026-03-23_
_Verifier: Claude (gsd-verifier)_
