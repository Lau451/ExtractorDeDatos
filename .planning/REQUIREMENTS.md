# Requirements: DocExtract

**Defined:** 2026-03-17
**Core Value:** Procurement and ops teams can upload any business document and get structured, usable data out as CSV without manual data entry.

## v1 Requirements

### File Ingestion

- [ ] **INGEST-01**: System accepts PDF files for processing
- [ ] **INGEST-02**: System accepts Excel files (.xlsx, .xls) for processing
- [ ] **INGEST-03**: System accepts PNG and image files for processing
- [ ] **INGEST-04**: User can upload multiple files in a single request (batch mode)

### OCR Processing

- [ ] **OCR-01**: System extracts text directly from selectable (text-based) PDFs without OCR
- [ ] **OCR-02**: System applies OCR to scanned or image-based PDFs to extract raw text
- [ ] **OCR-03**: System applies OCR to standalone PNG/image files to extract raw text
- [ ] **OCR-04**: System reads cell values directly from Excel files without OCR

### LLM Extraction

- [ ] **LLM-01**: System supports swappable LLM provider (GPT, Claude, Gemini) via configuration
- [ ] **LLM-02**: System extracts structured fields from documents: client/supplier name, line items, prices, dates/deadlines, reference numbers
- [ ] **LLM-03**: System auto-detects document type (invoice, PO, tender, quotation request, supplier comparison)
- [ ] **LLM-04**: System returns a confidence score per extracted field

### Supplier Comparison

- [ ] **COMP-01**: System extracts all suppliers from an existing supplier comparison document
- [ ] **COMP-02**: System generates a supplier comparison from multiple uploaded quote documents
- [ ] **COMP-03**: System flags the lowest price per line item in comparison output

### CSV Export

- [ ] **CSV-01**: System produces a summary CSV with one row per document (type, client, date, total, reference)
- [ ] **CSV-02**: System produces a line items CSV with one row per line item (product, qty, unit price, total, source document)
- [ ] **CSV-03**: System produces a supplier comparison CSV with side-by-side supplier data and best-price flagging

### API (FastAPI)

- [ ] **API-01**: System exposes POST /extract endpoint that accepts file(s) and returns extraction results
- [ ] **API-02**: System processes uploads asynchronously, returning a job ID immediately for polling
- [ ] **API-03**: System exposes GET /health endpoint for monitoring and readiness checks
- [ ] **API-04**: System exposes GET /export endpoint to download extraction results as CSV

## v2 Requirements

### Quality & Reliability

- **QA-01**: Extraction retry logic on LLM timeout or partial response
- **QA-02**: Field-level validation (e.g., price must be numeric, date must parse)
- **QA-03**: Human review queue for low-confidence extractions

### Extended Input Support

- **EXT-01**: Support Word documents (.docx)
- **EXT-02**: Support multi-page TIFF files
- **EXT-03**: URL-based document ingestion (fetch from link)

### User Interface

- **UI-01**: Web UI for uploading documents and downloading CSVs
- **UI-02**: Extraction results preview before CSV download
- **UI-03**: Correction interface for low-confidence fields

## Out of Scope

| Feature | Reason |
|---------|--------|
| User authentication/login | Internal tool — no multi-tenant access control needed in v1 |
| Document storage/archiving | Extraction and output only; no persistence required in v1 |
| Custom field configuration UI | Fields are fixed for v1; config file is sufficient |
| Real-time streaming extraction | Async job model is sufficient; streaming adds complexity |
| Mobile support | Internal desktop tool |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INGEST-01 | Phase 1 | Pending |
| INGEST-02 | Phase 1 | Pending |
| INGEST-03 | Phase 1 | Pending |
| INGEST-04 | Phase 1 | Pending |
| OCR-01 | Phase 2 | Pending |
| OCR-02 | Phase 2 | Pending |
| OCR-03 | Phase 2 | Pending |
| OCR-04 | Phase 2 | Pending |
| LLM-01 | Phase 3 | Pending |
| LLM-02 | Phase 3 | Pending |
| LLM-03 | Phase 3 | Pending |
| LLM-04 | Phase 3 | Pending |
| COMP-01 | Phase 4 | Pending |
| COMP-02 | Phase 4 | Pending |
| COMP-03 | Phase 4 | Pending |
| CSV-01 | Phase 4 | Pending |
| CSV-02 | Phase 4 | Pending |
| CSV-03 | Phase 4 | Pending |
| API-01 | Phase 5 | Pending |
| API-02 | Phase 5 | Pending |
| API-03 | Phase 5 | Pending |
| API-04 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 22 total
- Mapped to phases: 22
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-17*
*Last updated: 2026-03-17 after initial definition*
