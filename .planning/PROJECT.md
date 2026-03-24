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

**Review & Correction** *(Validated in Phase 4: full-api-integration)*
- [x] User can view all extracted fields before downloading the CSV
- [x] User can edit/correct any extracted field value inline
- [x] Edited values are reflected in the final CSV output

**CSV Export** *(Validated in Phase 3: csv-export)*
- [x] User can download the extraction result as a CSV file
- [x] CSV column order matches the predefined schema for each document type
- [x] Each document type produces its own CSV structure

**Web UI** *(Validated in Phase 5: web-ui)*
- [x] User can upload a file via a web browser interface
- [x] User sees extraction progress/status while the document is being processed
- [x] User can review, edit, and download the result from the same page

**API** *(CSV download validated in Phase 3: csv-export)*
- [x] REST API exposes upload, status polling, and CSV download endpoints
- [ ] API processes one file per request (no batch uploads in v1)

### Out of Scope

- User authentication / accounts — internal tool, open access is acceptable for v1
- Batch upload (multiple files in one request) — defer to v2
- Persistent job history / past extractions — in-memory only for v1
- Real-time collaboration or shared workspaces — not needed
- Mobile app — web-first
- Celery / distributed task queue — in-memory async is sufficient for v1

## Context

- **Current State:** Phase 5 complete — React + Vite + Tailwind + shadcn/ui frontend with full upload→processing→review→done flow. UploadZone, ProgressView, EditableCell, ReviewTable, LineItemsTable, DocTypeBar, CSV download, and FastAPI static serving all implemented. 18/18 frontend tests + 61/61 backend tests passing. All 5 milestones complete — v1.0 milestone done.
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
| Web UI with inline editing | Users need to review and correct extracted fields before downloading | ✓ Implemented (Phase 5) |
| In-memory job state for v1 | Avoids database dependency; acceptable for single-user internal tool | ✓ Implemented (Phase 1) |
| One document type per file | Simplifies routing and schema selection; user confirmed documents are not mixed | — Pending |

---
*Last updated: 2026-03-24 — Phase 5 complete (web-ui). Full React frontend implemented. 18/18 frontend + 61/61 backend tests passing. v1.0 milestone complete.*
