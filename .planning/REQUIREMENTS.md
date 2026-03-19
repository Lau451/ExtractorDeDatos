# Requirements: DocExtract

**Defined:** 2026-03-18
**Core Value:** A procurement analyst can upload any business document and get a structured, editable CSV extract in seconds — without manual data entry.

## v1 Requirements

### File Ingestion

- [x] **ING-01**: User can upload a PDF file (text-based) and the system extracts its content
- [x] **ING-02**: User can upload a scanned PDF or image-based PDF and the system extracts text via full-page OCR
- [x] **ING-03**: User can upload an Excel file (XLSX/XLS) and the system reads its cell content
- [x] **ING-04**: User can upload an image file (PNG/JPG) and the system extracts text via OCR
- [x] **ING-05**: User can upload an HTML file and the system parses its content
- [x] **ING-06**: System rejects unsupported file types with a clear error message before processing

### Document Classification

- [ ] **CLS-01**: System automatically detects the document type (purchase order, tender/RFQ, quotation, invoice, or supplier comparison) after upload
- [ ] **CLS-02**: User can see the detected document type before extraction begins
- [ ] **CLS-03**: User can override the detected document type via a dropdown before extraction begins

### Field Extraction

- [ ] **EXT-01**: System extracts structured header fields from purchase orders (reference number, buyer, supplier, date, delivery date, total amount, currency, terms)
- [ ] **EXT-02**: System extracts structured header fields from tenders/RFQs using the predefined schema
- [ ] **EXT-03**: System extracts structured header fields from quotations using the predefined schema
- [ ] **EXT-04**: System extracts structured header fields from invoices (invoice number, issuer, recipient, issue date, due date, subtotal, taxes, total, currency)
- [ ] **EXT-05**: System extracts structured header fields from supplier comparison documents (project name, comparison date, evaluation criteria, overall recommended supplier)
- [ ] **EXT-06**: System extracts line items (multi-row tables) from purchase orders — one row per item with description, quantity, unit price, extended price
- [ ] **EXT-07**: System extracts line items from invoices — one row per item with description, quantity, unit price, extended price
- [ ] **EXT-08**: System extracts per-supplier rows from supplier comparison documents — one row per supplier with unit price, total, lead time, payment terms, delivery terms
- [ ] **EXT-09**: LLM extraction uses a pluggable provider abstraction — Gemini 2.5 Flash is the default; swapping to another provider requires only a config change
- [ ] **EXT-10**: System uses Gemini 2.5 Flash (via `google-genai` SDK) as the default extraction LLM

### Review & Correction

- [ ] **REV-01**: User can see all extracted fields displayed in a review table before downloading CSV
- [ ] **REV-02**: User can edit any extracted field value inline in the review table
- [ ] **REV-03**: Fields that could not be extracted are shown as "Not found" (not blank) in the review table
- [ ] **REV-04**: User can see extraction progress (spinner with status text) while the document is being processed
- [ ] **REV-05**: Edited values are reflected in the downloaded CSV (not the originally extracted values)

### CSV Export

- [ ] **EXP-01**: User can download the extraction result as a CSV file
- [ ] **EXP-02**: CSV column order matches the predefined schema for the detected document type
- [ ] **EXP-03**: CSV file is encoded as UTF-8 with BOM (utf-8-sig) for correct display in Excel
- [ ] **EXP-04**: Each document type produces its own CSV structure (purchase orders, tenders/RFQs, quotations, invoices, and supplier comparisons each have distinct column schemas)

### REST API

- [x] **API-01**: API exposes a POST /extract endpoint that accepts a file upload and returns a job ID immediately
- [x] **API-02**: API exposes a GET /jobs/{id} endpoint that returns the current job status (pending / processing / complete / error)
- [ ] **API-03**: API exposes a PATCH /jobs/{id}/fields endpoint that accepts user-corrected field values
- [ ] **API-04**: API exposes a GET /jobs/{id}/export endpoint that returns the final CSV file (applying any user corrections)
- [x] **API-05**: API exposes a GET /health endpoint that returns service health status

## v2 Requirements

### Quality & Trust

- **QUAL-01**: System shows per-field confidence indicators — highlights low-confidence fields for priority review
- **QUAL-02**: System records audit trail of original vs. corrected values per extraction

### Scale & Operations

- **OPS-01**: System supports batch upload (multiple files in one request)
- **OPS-02**: System persists job history across sessions (database-backed job store)
- **OPS-03**: System supports user authentication / accounts for multi-user environments

### Advanced Extraction

- **EXT-V2-01**: System supports three-way PO/invoice/receipt matching
- **EXT-V2-02**: System exposes LLM processing transparency (OCR vs. native parse, token count, model used)

## Out of Scope

| Feature | Reason |
|---------|--------|
| User authentication | Internal tool — open access acceptable for v1 |
| Persistent job history | In-memory storage sufficient for v1; no cross-session recall needed |
| Batch upload (multiple files) | 3-4x implementation complexity; single-file flow must be stable first |
| ERP / accounting system integration | CSV is the integration layer for v1 |
| Three-way PO/invoice/receipt matching | Requires persistent storage and a business rules engine |
| Per-field confidence indicators | Differentiator; deferred to v2 to keep v1 scope focused |
| Timestamped filenames | Minor UX; can be added incrementally |
| LangChain / complex LLM middleware | Gemini native `response_schema` makes this unnecessary |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ING-01 | Phase 1 | Complete |
| ING-02 | Phase 1 | Complete |
| ING-03 | Phase 1 | Complete |
| ING-04 | Phase 1 | Complete |
| ING-05 | Phase 1 | Complete |
| ING-06 | Phase 1 | Complete |
| API-01 | Phase 1 | Complete |
| API-02 | Phase 1 | Complete |
| API-05 | Phase 1 | Complete |
| CLS-01 | Phase 2 | Pending |
| CLS-02 | Phase 2 | Pending |
| CLS-03 | Phase 2 | Pending |
| EXT-01 | Phase 2 | Pending |
| EXT-02 | Phase 2 | Pending |
| EXT-03 | Phase 2 | Pending |
| EXT-04 | Phase 2 | Pending |
| EXT-05 | Phase 2 | Pending |
| EXT-06 | Phase 2 | Pending |
| EXT-07 | Phase 2 | Pending |
| EXT-08 | Phase 2 | Pending |
| EXT-09 | Phase 2 | Pending |
| EXT-10 | Phase 2 | Pending |
| EXP-01 | Phase 3 | Pending |
| EXP-02 | Phase 3 | Pending |
| EXP-03 | Phase 3 | Pending |
| EXP-04 | Phase 3 | Pending |
| API-04 | Phase 3 | Pending |
| API-03 | Phase 4 | Pending |
| REV-05 | Phase 4 | Pending |
| REV-01 | Phase 5 | Pending |
| REV-02 | Phase 5 | Pending |
| REV-03 | Phase 5 | Pending |
| REV-04 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 33 total
- Mapped to phases: 33
- Unmapped: 0 ✓

Note: Original file stated 34 requirements — actual count is 33 (ING: 6, CLS: 3, EXT: 10, REV: 5, EXP: 4, API: 5).

---
*Requirements defined: 2026-03-18*
*Last updated: 2026-03-18 — traceability updated to reflect roadmap phase assignments*
