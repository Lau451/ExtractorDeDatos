# DocExtract

## What This Is

DocExtract is a document data extraction system for business and procurement processes. It accepts files in PDF, Excel, image (PNG/JPG), and HTML formats, automatically detects the document type (purchase order, tender, quotation, invoice, or supplier comparison), extracts key structured fields using Gemini 2.5 Flash, and outputs the results as a clean CSV file. Users interact via a web UI where they can upload a document, review and edit the extracted fields, and download the final CSV.

## Core Value

A procurement analyst can upload any business document and get a structured, editable CSV extract in seconds — without manual data entry.

## Requirements

### Validated

**File Ingestion** *(Validated in Phase 1: Foundation)*
- [x] User can upload documents in PDF, Excel (XLSX/XLS), image (PNG/JPG), and HTML formats
- [x] System parses and normalizes document content using Docling
- [x] System falls back to OCR for scanned PDFs and images

**API** *(Validated in Phase 1: Foundation)*
- [x] REST API exposes upload (`POST /extract`) and status polling (`GET /jobs/{id}`) endpoints
- [x] `GET /health` returns service health status

### Active

**File Ingestion**
- [ ] User can upload documents in PDF, Excel (XLSX/XLS), image (PNG/JPG), and HTML formats
- [ ] System parses and normalizes document content using Docling
- [ ] System falls back to OCR for scanned PDFs and images

**Document Classification**
- [ ] System automatically detects document type on upload (purchase order, tender/RFQ, quotation, invoice, supplier comparison)
- [ ] User can override the detected document type before extraction

**Field Extraction**
- [ ] System extracts structured fields from purchase orders using Gemini 2.5 Flash
- [ ] System extracts structured fields from tenders/RFQs using Gemini 2.5 Flash
- [ ] System extracts structured fields from quotations using Gemini 2.5 Flash
- [ ] System extracts structured fields from invoices using Gemini 2.5 Flash
- [ ] System extracts structured fields from supplier comparison files using Gemini 2.5 Flash
- [ ] Each document type has a defined CSV schema with strict column ordering

**Review & Correction**
- [ ] User can view all extracted fields before downloading the CSV
- [ ] User can edit/correct any extracted field value inline
- [ ] Edited values are reflected in the final CSV output

**CSV Export**
- [ ] User can download the extraction result as a CSV file
- [ ] CSV column order matches the predefined schema for each document type
- [ ] Each document type produces its own CSV structure

**Web UI**
- [ ] User can upload a file via a web browser interface
- [ ] User sees extraction progress/status while the document is being processed
- [ ] User can review, edit, and download the result from the same page

**API**
- [ ] REST API exposes upload, status polling, and CSV download endpoints
- [ ] API processes one file per request (no batch uploads in v1)

### Out of Scope

- User authentication / accounts — internal tool, open access is acceptable for v1
- Batch upload (multiple files in one request) — defer to v2
- Persistent job history / past extractions — in-memory only for v1
- Real-time collaboration or shared workspaces — not needed
- Mobile app — web-first
- Celery / distributed task queue — in-memory async is sufficient for v1

## Context

- **Current State:** Phase 1 complete — FastAPI server running, Docling ingestion active, 15/15 tests passing. Phase 2 (extraction pipeline) is next.
- **Codebase:** Phase 1 implemented. `src/` contains core, api, and ingestion layers. Tests in `tests/`.
- **Docling:** User-specified library for document parsing and structure extraction. Replaces raw pdfplumber/Tesseract approach documented in codebase map.
- **LLM:** Gemini 2.5 Flash via `google-generativeai` SDK. Provider abstraction should allow future swapping.
- **CSV Schemas:** Tenders/RFQs and Quotations schemas are already defined. Purchase Orders, Invoices, and Supplier Comparison schemas need to be designed as part of this project.
- **Document scope:** Each uploaded file contains exactly one document type — no mixed documents.
- **Architecture:** Layered pipeline (ingestion → extraction → export) with FastAPI service layer. Modular design with clear separation: API, services, extractors, LLM interaction, CSV generation.

## Constraints

- **Tech Stack:** Python + FastAPI — established in planning docs, non-negotiable
- **LLM:** Gemini 2.5 Flash — primary provider for v1
- **Document Parser:** Docling — specified by user for structure-aware parsing
- **No Persistence:** v1 uses in-memory job state; results are not stored between sessions
- **Single File Per Request:** No batch processing in v1

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Docling for document parsing | Structure-aware parsing; handles PDFs, Excel, images better than raw pdfplumber+Tesseract | ✓ Implemented (Phase 1) |
| Gemini 2.5 Flash as primary LLM | User requirement; good cost/performance ratio for structured extraction tasks | — Pending |
| Pluggable LLM provider abstraction | Allow swapping Gemini for OpenAI/Claude without rewriting extractors | — Pending |
| Web UI with inline editing | Users need to review and correct extracted fields before downloading | — Pending |
| In-memory job state for v1 | Avoids database dependency; acceptable for single-user internal tool | ✓ Implemented (Phase 1) |
| One document type per file | Simplifies routing and schema selection; user confirmed documents are not mixed | — Pending |

---
*Last updated: 2026-03-19 — Phase 1 complete*
