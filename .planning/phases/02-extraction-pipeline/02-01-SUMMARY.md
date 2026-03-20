---
phase: 02-extraction-pipeline
plan: 01
subsystem: extraction-schemas
tags: [pydantic, schemas, job-store, config, data-contracts]
dependency_graph:
  requires: []
  provides:
    - src/extraction/schemas/registry.py (SCHEMA_REGISTRY, VALID_DOC_TYPES)
    - src/extraction/schemas/purchase_order.py (PurchaseOrderResult, POLineItem)
    - src/extraction/schemas/tender_rfq.py (TenderRFQResult)
    - src/extraction/schemas/quotation.py (QuotationResult)
    - src/extraction/schemas/invoice.py (InvoiceResult, InvoiceLineItem)
    - src/extraction/schemas/supplier_comparison.py (SupplierComparisonResult, SupplierRow)
    - src/core/job_store.py (doc_type, extraction_result fields + set_doc_type, set_extraction_result methods)
    - src/core/config.py (gemini_api_key, llm_provider, llm_timeout)
    - src/api/models.py (DocTypeOverrideRequest, extended JobResponse)
  affects:
    - Phase 2 plans 02-03 (LLM provider, extraction service, API routes all depend on these contracts)
tech_stack:
  added: []
  patterns:
    - Pydantic v2 BaseModel with Optional[str] fields for Gemini response_schema compatibility
    - Schema registry dict mapping doc type strings to Pydantic classes
    - JobStore method extension following existing set_complete/set_error pattern
    - pydantic_settings extension for LLM config
key_files:
  created:
    - src/extraction/__init__.py
    - src/extraction/schemas/__init__.py
    - src/extraction/schemas/purchase_order.py
    - src/extraction/schemas/tender_rfq.py
    - src/extraction/schemas/quotation.py
    - src/extraction/schemas/invoice.py
    - src/extraction/schemas/supplier_comparison.py
    - src/extraction/schemas/registry.py
  modified:
    - src/core/job_store.py
    - src/core/config.py
    - src/api/models.py
    - .env.example
decisions:
  - "All schema fields use Optional[str] (not float/int) to prevent Gemini InvalidArgument 400 schema rejections"
  - "TenderRFQResult and QuotationResult are header-only (no line_items) per locked decision in CONTEXT.md"
  - "extraction_result stored as Optional[dict] (plain dict from .model_dump()) not Pydantic model for JSON serialization"
  - "doc_type field placed before created_at/updated_at in Job dataclass for logical ordering"
metrics:
  duration: "~4 min"
  completed_date: "2026-03-19"
  tasks_completed: 2
  files_created: 8
  files_modified: 4
---

# Phase 2 Plan 1: Data Contracts and Extraction Schemas Summary

Five Pydantic extraction schemas + schema registry + extended Job/Settings/API models defining all data contracts for the Phase 2 extraction pipeline.

## What Was Built

### Task 1: Pydantic Extraction Schemas and Registry

Created the complete `src/extraction/` module with five per-document-type schemas:

- **`purchase_order.py`** — `POLineItem` + `PurchaseOrderResult` (10 header fields + `line_items: list[POLineItem]`)
- **`invoice.py`** — `InvoiceLineItem` + `InvoiceResult` (13 header fields + `line_items: list[InvoiceLineItem]`; disambiguation descriptions on `invoice_date` vs `due_date`)
- **`supplier_comparison.py`** — `SupplierRow` + `SupplierComparisonResult` (6 header fields + `line_items: list[SupplierRow]` with 10 supplier evaluation fields)
- **`tender_rfq.py`** — `TenderRFQResult` (8 header fields, no line items per locked decision)
- **`quotation.py`** — `QuotationResult` (12 header fields, no line items per locked decision)
- **`registry.py`** — `SCHEMA_REGISTRY: dict[str, type]` mapping 5 doc type strings to classes; `VALID_DOC_TYPES` set

All fields are `Optional[str] = Field(None, description="...")` — no `Optional[float]` or complex types anywhere, preventing Gemini `InvalidArgument 400` schema rejection.

### Task 2: Job Store, Config, and API Model Extensions

Extended three core files to support the extraction pipeline:

**`src/core/job_store.py`:**
- `JobStatus` literal extended with `"classifying"` and `"extracting"` states
- `Job` dataclass gains `doc_type: Optional[str]` and `extraction_result: Optional[dict]` fields
- `JobStore` gains `set_doc_type()` and `set_extraction_result()` methods following existing lock/utcnow pattern

**`src/core/config.py`:**
- `Settings` class gains `gemini_api_key: str = ""`, `llm_provider: str = "gemini"`, `llm_timeout: float = 60.0`

**`src/api/models.py`:**
- `JobResponse` gains `doc_type: Optional[str]` and `extraction_result: Optional[dict]` fields
- New `DocTypeOverrideRequest(BaseModel)` with `doc_type: str` for PATCH endpoint

**`.env.example`:**
- Appended `GEMINI_API_KEY=`, `LLM_PROVIDER=gemini`, `LLM_TIMEOUT=60`

## Verification

All plan-level checks passed:
- `from src.extraction.schemas.registry import SCHEMA_REGISTRY; assert len(SCHEMA_REGISTRY) == 5` — OK
- `from src.core.job_store import Job; j = Job(job_id='x'); assert j.doc_type is None` — OK
- `from src.core.config import settings; assert settings.llm_provider == 'gemini'` — OK
- `pytest tests/ -q` — 15 passed, 0 failed (no regressions)

## Commits

| Task | Commit | Message |
|------|--------|---------|
| Task 1 | 630f45a | feat(02-01): create Pydantic extraction schemas and registry |
| Task 2 | 2cb278d | feat(02-01): extend job store, config, and API models for Phase 2 |

## Decisions Made

1. **All `Optional[str]` fields** — Gemini's `response_schema` validator rejects `Optional[float]` and complex nested types with `InvalidArgument 400`. Using `Optional[str]` throughout avoids this pitfall documented in RESEARCH.md.

2. **Header-only schemas for Tender/RFQ and Quotation** — Per locked decision in CONTEXT.md. These document types do not have structured line item tables in practice.

3. **`extraction_result` as `Optional[dict]`** — Storing as plain Python dict (from Pydantic's `.model_dump()`) avoids needing custom JSON encoders in FastAPI. The Pydantic schema is the source of truth; the dict is the transport form.

4. **`doc_type` and `extraction_result` placed before `created_at`/`updated_at`** — Logical grouping: mutable operational fields before immutable timestamp fields.

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

Files created/exist:
- src/extraction/__init__.py: FOUND
- src/extraction/schemas/purchase_order.py: FOUND
- src/extraction/schemas/registry.py: FOUND
- src/core/job_store.py modified with doc_type: FOUND
- src/core/config.py modified with gemini_api_key: FOUND
- src/api/models.py modified with DocTypeOverrideRequest: FOUND

Commits exist:
- 630f45a: FOUND
- 2cb278d: FOUND
