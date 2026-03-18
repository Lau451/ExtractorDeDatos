# Roadmap: DocExtract

## Overview

DocExtract is built in four phases that mirror the data flow: first accept and read any file format, then interpret content with an LLM, then produce structured comparison and CSV outputs, and finally expose everything as a FastAPI service. Each phase delivers a testable, end-to-end slice of capability that the next phase builds on.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Ingestion & Text Extraction** - Accept PDF, Excel, and PNG files and produce raw text from each
- [ ] **Phase 2: LLM Extraction Pipeline** - Use a swappable LLM provider to extract structured fields from raw text
- [ ] **Phase 3: Comparison & CSV Output** - Generate supplier comparison logic and produce all three CSV formats
- [ ] **Phase 4: FastAPI Service** - Expose the full pipeline as an async FastAPI service with health and export endpoints

## Phase Details

### Phase 1: Ingestion & Text Extraction
**Goal**: Any supported file can be uploaded and its full text content is reliably extracted
**Depends on**: Nothing (first phase)
**Requirements**: INGEST-01, INGEST-02, INGEST-03, INGEST-04, OCR-01, OCR-02, OCR-03, OCR-04
**Success Criteria** (what must be TRUE):
  1. A text-based PDF is submitted and all its selectable text is returned without OCR
  2. A scanned PDF or PNG image is submitted and OCR produces readable extracted text
  3. An Excel file is submitted and all cell values are returned as structured text
  4. Multiple files are submitted in a single request and all are processed together
**Plans**: TBD

Plans:
- [ ] 01-01: File ingestion module — accept and route PDF, Excel, PNG inputs
- [ ] 01-02: Text extraction — direct text layer (PDF), OCR (scanned PDF + PNG), Excel cell reader

### Phase 2: LLM Extraction Pipeline
**Goal**: Extracted text from any document type is interpreted by a configurable LLM and returns structured fields with confidence scores
**Depends on**: Phase 1
**Requirements**: LLM-01, LLM-02, LLM-03, LLM-04
**Success Criteria** (what must be TRUE):
  1. The active LLM provider can be switched via configuration without code changes
  2. A document is processed and the system returns: client/supplier name, line items, prices, dates, and reference numbers
  3. The system correctly identifies document type (invoice, PO, tender, quotation, supplier comparison) from content alone
  4. Each extracted field is returned with a numeric confidence score
**Plans**: TBD

Plans:
- [ ] 02-01: LLM provider abstraction — pluggable adapter for GPT, Claude, Gemini
- [ ] 02-02: Field extraction prompts — structured field extraction with document type detection and confidence scoring

### Phase 3: Comparison & CSV Output
**Goal**: Supplier data from multiple documents can be compared side-by-side and all results can be exported as CSV
**Depends on**: Phase 2
**Requirements**: COMP-01, COMP-02, COMP-03, CSV-01, CSV-02, CSV-03
**Success Criteria** (what must be TRUE):
  1. An existing supplier comparison document is uploaded and all supplier entries are extracted into discrete rows
  2. Multiple quote documents are uploaded together and the system synthesizes a comparison table across suppliers
  3. The comparison output flags the lowest-price supplier for each line item
  4. A summary CSV is downloadable with one row per document (type, client, date, total, reference)
  5. A line items CSV is downloadable with one row per extracted line item including source document
**Plans**: TBD

Plans:
- [ ] 03-01: Supplier comparison logic — ingest existing comparison doc and synthesize new one from quotes
- [ ] 03-02: CSV export — summary, line items, and supplier comparison formats with best-price flagging

### Phase 4: FastAPI Service
**Goal**: The full extraction pipeline is accessible via an async REST API with job tracking, health monitoring, and CSV download
**Depends on**: Phase 3
**Requirements**: API-01, API-02, API-03, API-04
**Success Criteria** (what must be TRUE):
  1. POST /extract accepts one or more files and immediately returns a job ID
  2. A client polls for job status and retrieves results when extraction completes
  3. GET /health returns a response confirming the service is running and ready
  4. GET /export returns extraction results as a downloadable CSV file
**Plans**: TBD

Plans:
- [ ] 04-01: FastAPI endpoints — /extract (async upload), /health, /export
- [ ] 04-02: Async job processing — job ID model, status polling, background extraction workers

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Ingestion & Text Extraction | 0/2 | Not started | - |
| 2. LLM Extraction Pipeline | 0/2 | Not started | - |
| 3. Comparison & CSV Output | 0/2 | Not started | - |
| 4. FastAPI Service | 0/2 | Not started | - |
