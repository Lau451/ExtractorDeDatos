---
phase: 02-extraction-pipeline
verified: 2026-03-19T00:00:00Z
status: passed
score: 17/17 must-haves verified
re_verification: false
---

# Phase 2: Extraction Pipeline Verification Report

**Phase Goal:** Build the LLM-powered extraction pipeline that classifies documents and extracts structured data
**Verified:** 2026-03-19
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Five Pydantic schema classes exist with all fields from EXT-01 through EXT-08 | VERIFIED | All 5 schema files exist with correct models and Optional[str] fields only |
| 2 | Job dataclass has doc_type and extraction_result fields | VERIFIED | `src/core/job_store.py` lines 16-17 |
| 3 | Job status type includes classifying and extracting states | VERIFIED | `JobStatus = Literal["pending","processing","classifying","extracting","complete","error"]` |
| 4 | Settings class has gemini_api_key, llm_provider, llm_timeout fields | VERIFIED | `src/core/config.py` lines 10-12 |
| 5 | Schema registry maps all five document type strings to their Pydantic classes | VERIFIED | `src/extraction/schemas/registry.py` — 5 entries, VALID_DOC_TYPES set |
| 6 | LLMProvider Protocol exists with classify() and extract() async methods | VERIFIED | `src/llm/base.py` — @runtime_checkable Protocol |
| 7 | GeminiProvider implements classify() and extract() using google-genai client.aio | VERIFIED | `src/llm/gemini.py` — `from google import genai`, `client.aio.models.generate_content` |
| 8 | Provider registry maps LLM_PROVIDER string to provider instance | VERIFIED | `src/llm/registry.py` — get_provider(), register_provider(), clear_cache() |
| 9 | Extraction service orchestrates classify → extract pipeline with retry-once and timeout | VERIFIED | `src/extraction/service.py` — _call_with_retry(), RETRY_BACKOFF=2.0 |
| 10 | After ingestion completes, extraction pipeline runs automatically | VERIFIED | `src/ingestion/service.py` line 33: `await run_extraction_pipeline(job_id)` |
| 11 | GET /jobs/{id} includes doc_type and extraction_result with None → "Not found" serialization | VERIFIED | `src/api/routes/jobs.py` — _serialize_extraction() helper |
| 12 | PATCH /jobs/{id}/doc_type with valid type returns 202 and triggers re-extraction | VERIFIED | `src/api/routes/doc_type.py` — status_code=202, background_tasks.add_task |
| 13 | PATCH /jobs/{id}/doc_type with invalid type returns 422 | VERIFIED | `src/api/routes/doc_type.py` line 39-44 |
| 14 | Five markdown fixture files simulate Docling output for each document type | VERIFIED | All 5 .md files exist in tests/fixtures/ |
| 15 | All extraction tests pass with no xfail markers | VERIFIED | 31 passed, 0 xfail — `pytest tests/ -q` |
| 16 | doc_type override flow tested end-to-end | VERIFIED | test_doc_type_override.py — 3 tests, 0 xfail |
| 17 | doc_type_router registered in main.py | VERIFIED | `src/main.py` line 3 + 12 |

**Score:** 17/17 truths verified

---

## Required Artifacts

### Plan 01 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/extraction/schemas/purchase_order.py` | PurchaseOrderResult + POLineItem | VERIFIED | 27 lines, both classes present, line_items field |
| `src/extraction/schemas/invoice.py` | InvoiceResult + InvoiceLineItem | VERIFIED | 29 lines, both classes, disambiguation descriptions on invoice_date vs due_date |
| `src/extraction/schemas/supplier_comparison.py` | SupplierComparisonResult + SupplierRow | VERIFIED | 26 lines, both classes, line_items per supplier |
| `src/extraction/schemas/tender_rfq.py` | TenderRFQResult (header-only) | VERIFIED | No line_items — matches locked decision |
| `src/extraction/schemas/quotation.py` | QuotationResult (header-only) | VERIFIED | No line_items — matches locked decision |
| `src/extraction/schemas/registry.py` | SCHEMA_REGISTRY + VALID_DOC_TYPES | VERIFIED | 5 entries, set derived from registry keys |
| `src/core/job_store.py` | doc_type + extraction_result fields + new methods | VERIFIED | Both fields present, set_doc_type() and set_extraction_result() methods exist |
| `src/core/config.py` | gemini_api_key, llm_provider, llm_timeout | VERIFIED | All 3 fields present with correct defaults |
| `src/api/models.py` | DocTypeOverrideRequest + extended JobResponse | VERIFIED | Both present |
| `.env.example` | GEMINI_API_KEY, LLM_PROVIDER, LLM_TIMEOUT | VERIFIED | Lines 7-9 |

### Plan 02 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tests/fixtures/sample_po.md` | PO fixture with line items | VERIFIED | Contains PO-2024-0847, 3-row line item table |
| `tests/fixtures/sample_invoice.md` | Invoice fixture with line items | VERIFIED | Contains INV-2024-1523, 2-row table |
| `tests/fixtures/sample_tender.md` | Tender fixture (header) | VERIFIED | Contains RFQ-2024-0312, scope of work section |
| `tests/fixtures/sample_quotation.md` | Quotation fixture (header) | VERIFIED | Contains QT-2024-0198, pricing summary |
| `tests/fixtures/sample_supplier_comparison.md` | Supplier comparison with 3 rows | VERIFIED | 3-supplier evaluation table with scores |
| `tests/test_extraction.py` | Test stubs for all extraction requirements | VERIFIED | 14 tests, 0 xfail, mocked with AsyncMock |
| `tests/test_doc_type_override.py` | CLS-03 override flow tests | VERIFIED | 3 tests, 0 xfail |

### Plan 03 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/llm/base.py` | LLMProvider Protocol | VERIFIED | @runtime_checkable, async classify + extract |
| `src/llm/gemini.py` | GeminiProvider implementation | VERIFIED | client.aio, gemini-2.5-flash, response_schema=schema, temperature=0.0 |
| `src/llm/registry.py` | get_provider() + register_provider() + clear_cache() | VERIFIED | All 3 functions present |
| `src/extraction/service.py` | run_extraction_pipeline() + extract_with_type() | VERIFIED | Both functions + _extract_with_schema() + _call_with_retry() |

### Plan 04 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/ingestion/service.py` | Calls run_extraction_pipeline after ingestion | VERIFIED | Line 9 import, line 33 call after set_complete |
| `src/api/routes/jobs.py` | Extended GET with doc_type + extraction_result | VERIFIED | _serialize_extraction helper, doc_type always included |
| `src/api/routes/doc_type.py` | PATCH /jobs/{id}/doc_type endpoint | VERIFIED | Returns 202, validates against VALID_DOC_TYPES, enqueues background task |
| `src/main.py` | doc_type_router registered | VERIFIED | Line 3 import, line 12 include_router |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/extraction/schemas/registry.py` | `src/extraction/schemas/*.py` | import + dict mapping | VERIFIED | All 5 schemas imported and mapped |
| `src/llm/gemini.py` | `google.genai` | `client.aio.models.generate_content()` | VERIFIED | `from google import genai`, async path used in both methods |
| `src/extraction/service.py` | `src/llm/registry.py` | `get_provider()` call | VERIFIED | Called in both run_extraction_pipeline and _extract_with_schema |
| `src/extraction/service.py` | `src/extraction/schemas/registry.py` | `SCHEMA_REGISTRY[doc_type]` | VERIFIED | `SCHEMA_REGISTRY.get(doc_type)` on line 93 |
| `src/extraction/service.py` | `src/core/job_store.py` | set_doc_type + set_extraction_result | VERIFIED | Both called with correct arguments |
| `src/ingestion/service.py` | `src/extraction/service.py` | `await run_extraction_pipeline(job_id)` after set_complete | VERIFIED | Line 33, inside try block after successful Docling conversion |
| `src/api/routes/doc_type.py` | `src/extraction/service.py` | `background_tasks.add_task(extract_with_type, ...)` | VERIFIED | Line 60 — correct module-level reference for test patching |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| CLS-01 | 02-02, 02-03 | Auto-detects document type after upload | SATISFIED | GeminiProvider.classify() returns one of 5 known types; _parse_doc_type normalizer handles edge cases; test_classify_returns_known_type passes |
| CLS-02 | 02-01, 02-04 | User can see detected document type before extraction | SATISFIED | GET /jobs/{id} always includes doc_type field; test_job_has_doc_type_after_classification passes |
| CLS-03 | 02-02, 02-04 | User can override detected doc type | SATISFIED | PATCH /jobs/{id}/doc_type returns 202, validates type, clears result, triggers re-extraction; all 3 override tests pass |
| EXT-01 | 02-01, 02-04 | PO header fields extracted | SATISFIED | PurchaseOrderResult has 10 header fields; test_po_extraction_header passes |
| EXT-02 | 02-01, 02-04 | Tender/RFQ header fields extracted | SATISFIED | TenderRFQResult has 8 header fields; test_tender_extraction passes |
| EXT-03 | 02-01, 02-04 | Quotation header fields extracted | SATISFIED | QuotationResult has 12 header fields; test_quotation_extraction passes |
| EXT-04 | 02-01, 02-04 | Invoice header fields extracted (invoice_date vs due_date) | SATISFIED | InvoiceResult has 13 header fields with disambiguation descriptions; test_invoice_extraction_header passes |
| EXT-05 | 02-01, 02-04 | Supplier comparison header fields extracted | SATISFIED | SupplierComparisonResult has 6 header fields; test_supplier_comparison_header passes |
| EXT-06 | 02-01, 02-04 | PO line items extracted | SATISFIED | PurchaseOrderResult.line_items: list[POLineItem]; test_po_extraction_line_items passes |
| EXT-07 | 02-01, 02-04 | Invoice line items extracted | SATISFIED | InvoiceResult.line_items: list[InvoiceLineItem]; test_invoice_extraction_line_items passes |
| EXT-08 | 02-01, 02-04 | Supplier comparison rows extracted | SATISFIED | SupplierComparisonResult.line_items: list[SupplierRow] with 10 supplier fields; test_supplier_comparison_line_items passes |
| EXT-09 | 02-03 | Pluggable LLM provider abstraction | SATISFIED | LLMProvider Protocol + register_provider() + clear_cache(); test_provider_registry_swap passes |
| EXT-10 | 02-03 | Uses google-genai SDK (not google-generativeai) | SATISFIED | `from google import genai` in gemini.py; test_gemini_provider_uses_correct_sdk passes with source inspection |

All 13 Phase 2 requirement IDs (CLS-01, CLS-02, CLS-03, EXT-01 through EXT-10) are SATISFIED. No orphaned requirements found.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/core/job_store.py` | 18, 41, 48, 64, 73 | `datetime.utcnow()` deprecated in Python 3.12+ | INFO | DeprecationWarning emitted in test output; not a logic error |

No blockers or warnings found. The `utcnow()` deprecation is a known Python stdlib migration issue and does not affect correctness or the phase goal.

---

## Human Verification Required

### 1. End-to-end extraction with real documents

**Test:** Upload a real PDF purchase order with GEMINI_API_KEY configured. Wait for completion. GET /jobs/{id}.
**Expected:** `doc_type == "purchase_order"`, `extraction_result` contains realistic po_number, buyer_name, line_items.
**Why human:** Requires a live Gemini API key and a real document. Tests mock the LLM layer.

### 2. Unknown document type user flow

**Test:** Upload a document that cannot be classified (e.g., a blank page or unrelated text). Observe the job result.
**Expected:** `status == "complete"`, `doc_type == "unknown"`, `extraction_result == null`. User should be able to override via PATCH.
**Why human:** Classification fallback to "unknown" requires a real LLM call to verify the heuristic prompt works correctly.

### 3. PATCH /jobs/{id}/doc_type end-to-end re-extraction

**Test:** After a job completes with `doc_type="purchase_order"`, issue PATCH with `{"doc_type": "invoice"}`. Poll until complete.
**Expected:** `doc_type == "invoice"`, `extraction_result` contains invoice-shaped data (invoice_number, due_date, etc.).
**Why human:** Requires a real Gemini API call to verify the schema swap actually produces different field shapes.

---

## Gaps Summary

No gaps found. All 17 observable truths verified, all 13 requirement IDs satisfied, all key links wired, all 31 tests pass with zero xfail markers.

---

_Verified: 2026-03-19_
_Verifier: Claude (gsd-verifier)_
