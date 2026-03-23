# Roadmap: DocExtract

## Overview

DocExtract is built in five natural delivery phases, each completing a coherent layer of the pipeline before the next begins. Phase 1 establishes the running server and proves that every input format can be ingested safely. Phase 2 wires in Gemini extraction for all five document types. Phase 3 delivers the CSV export layer as a pure function against proven extraction results. Phase 4 completes the REST API surface so user-corrected field values reach the exported CSV. Phase 5 delivers the React SPA that makes the entire pipeline accessible in a browser with inline review and editing.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - Running FastAPI server with safe multi-format file ingestion and async job infrastructure (completed 2026-03-19)
- [ ] **Phase 2: Extraction Pipeline** - Document classification and structured field extraction for all five document types via Gemini 2.5 Flash
- [ ] **Phase 3: CSV Export** - Schema-correct, Excel-compatible CSV generation for all document types
- [ ] **Phase 4: Full API Integration** - Complete REST endpoint surface with user-edit merge into export
- [ ] **Phase 5: Web UI** - React SPA with upload, status polling, inline-edit review table, and CSV download

## Phase Details

### Phase 1: Foundation
**Goal**: A running FastAPI server that accepts any supported file format, safely ingests it via Docling with OCR and timeout protection, stores the job in a race-condition-safe in-memory store, and exposes upload and status endpoints
**Depends on**: Nothing (first phase)
**Requirements**: ING-01, ING-02, ING-03, ING-04, ING-05, ING-06, API-01, API-02, API-05
**Success Criteria** (what must be TRUE):
  1. User can POST a PDF, XLSX, PNG/JPG, or HTML file to /extract and immediately receive a job ID
  2. User can GET /jobs/{id} and see the job progress from pending through processing to complete
  3. Scanned PDFs and image files produce non-empty normalized text (OCR is active, not silently skipped)
  4. Uploading an unsupported file type returns a clear error — the job is never created
  5. GET /health returns a healthy status response
**Plans:** 3/3 plans complete

Plans:
- [x] 01-01-PLAN.md — Project scaffold, dependencies, core infrastructure (config, job store, API models, health endpoint)
- [x] 01-02-PLAN.md — Ingestion layer (Docling adapter, service), API endpoints (POST /extract, GET /jobs), full test suite
- [ ] 01-03-PLAN.md — Gap closure: PNG OCR full-page config + error message surfacing

### Phase 2: Extraction Pipeline
**Goal**: Full extraction pipeline — document classifier routing to per-type Pydantic schemas, Gemini 2.5 Flash structured extraction for all five document types including line items, and pluggable LLM provider abstraction
**Depends on**: Phase 1
**Requirements**: CLS-01, CLS-02, CLS-03, EXT-01, EXT-02, EXT-03, EXT-04, EXT-05, EXT-06, EXT-07, EXT-08, EXT-09, EXT-10
**Success Criteria** (what must be TRUE):
  1. After uploading a purchase order, the job result contains structured header fields and line items matching the PO schema
  2. After uploading a tender/RFQ, quotation, invoice, or supplier comparison, the job result contains correctly typed structured fields for that document type
  3. The detected document type is visible in the job result before the user initiates any download
  4. User can override the detected document type and re-trigger extraction against the correct schema
  5. Swapping the LLM provider requires only a config change — no extractor code changes
**Plans:** 3/4 plans executed

Plans:
- [ ] 02-01-PLAN.md — Pydantic extraction schemas, schema registry, job store + config + API model extensions
- [ ] 02-02-PLAN.md — Test fixtures (5 markdown fixtures) and test scaffolds (16 test stubs with xfail)
- [ ] 02-03-PLAN.md — LLM provider abstraction (Protocol + GeminiProvider + registry) and extraction service
- [ ] 02-04-PLAN.md — API integration (pipeline wiring, GET/PATCH endpoints) and finalize all tests

### Phase 3: CSV Export
**Goal**: Per-type CSV formatters that serialize a validated ExtractionResult to a UTF-8-with-BOM CSV with schema-correct column ordering, exposed via GET /jobs/{id}/export
**Depends on**: Phase 2
**Requirements**: EXP-01, EXP-02, EXP-03, EXP-04, API-04
**Success Criteria** (what must be TRUE):
  1. User can download a CSV file from any completed job
  2. The downloaded CSV opens in Excel without garbled characters
  3. CSV column order matches the predefined schema for the document type — no extra or reordered columns
  4. Each of the five document types produces its own distinct CSV structure (purchase order, tender/RFQ, quotation, invoice, supplier comparison)
**Plans:** 1/2 plans executed

Plans:
- [ ] 03-01-PLAN.md — CSV formatters for all 5 doc types with FORMATTER_REGISTRY and unit tests
- [ ] 03-02-PLAN.md — GET /jobs/{id}/export endpoint with 409 gate and integration tests

### Phase 4: Full API Integration
**Goal**: Complete REST API surface — PATCH endpoint for user-corrected field values merges edits into the extraction result so the exported CSV reflects corrections, plus TTL-based job cleanup and structured error states
**Depends on**: Phase 3
**Requirements**: API-03, REV-05
**Success Criteria** (what must be TRUE):
  1. User can PATCH corrected field values to a job and the subsequent CSV download contains the corrected values, not the originally extracted values
  2. Failed jobs expose a human-readable error state (Docling timeout, Gemini error, invalid file) rather than a 500 response
**Plans**: TBD

### Phase 5: Web UI
**Goal**: React SPA that exposes the complete single-file extraction workflow — upload zone, live progress indicator, inline-editable review table, document type display with override dropdown, and CSV download trigger
**Depends on**: Phase 4
**Requirements**: REV-01, REV-02, REV-03, REV-04
**Success Criteria** (what must be TRUE):
  1. User can upload a document via drag-and-drop or file picker and see a live progress indicator while Gemini processes it
  2. User can view all extracted fields in a review table with human-readable labels — fields that could not be extracted show "Not found" rather than blank
  3. User can edit any field value inline in the review table and download a CSV that reflects their edits
  4. User can see the detected document type and override it via a dropdown before extraction results are finalized
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 3/3 | Complete   | 2026-03-19 |
| 2. Extraction Pipeline | 3/4 | In Progress|  |
| 3. CSV Export | 1/2 | In Progress|  |
| 4. Full API Integration | 0/TBD | Not started | - |
| 5. Web UI | 0/TBD | Not started | - |
