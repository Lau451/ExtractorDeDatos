# DocExtract — Business Document Data Extraction System

## What This Is

An internal data extraction system that processes business documents (tenders, quotation requests, purchase orders, invoices, and supplier comparisons) in PDF, Excel, and image (PNG) formats. It uses OCR to extract raw text and an LLM (GPT/Claude/Gemini) to identify and structure key fields, then outputs results as CSV for use by procurement and operations teams. The system is designed to integrate with a FastAPI backend.

## Core Value

Procurement and ops teams can upload any business document — regardless of layout or format — and get structured, usable data out as CSV without manual data entry.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Accept PDF, Excel, and PNG files as input
- [ ] Use OCR to extract raw text from PDFs and images
- [ ] Use LLM (GPT/Claude/Gemini) to extract structured fields: client/supplier name, line items + prices, dates + deadlines, reference numbers
- [ ] Support all document types: tenders, quotation requests, purchase orders, invoices, supplier comparisons
- [ ] Accept existing supplier comparison documents and extract all suppliers from them
- [ ] Generate supplier comparison output from multiple uploaded quotes
- [ ] Output two CSV formats: summary (one row per document) and line items (one row per line item)
- [ ] Support single-file and batch upload modes
- [ ] Expose functionality via FastAPI-compatible API

### Out of Scope

- Real-time streaming extraction — batch completion is sufficient
- User authentication/login — internal tool, not a multi-tenant SaaS
- Document storage/archiving — extraction and output only
- Custom field configuration UI — fields are fixed for v1

## Context

- Documents come from many different suppliers and clients with inconsistent layouts — no reliable template structure to rely on
- OCR handles scanned/image-based PDFs and PNG files; LLM handles interpretation of raw extracted text
- The system needs to handle all five document types with a single consistent extraction pipeline
- Supplier comparison feature works in two directions: ingesting an existing comparison doc, and synthesizing a new one from multiple uploaded quotes
- FastAPI integration is a first-class requirement, not an afterthought — the system should be designed as a service from day one

## Constraints

- **LLM provider**: Must support swappable LLM backend (GPT/Claude/Gemini) — no hard coupling to one provider
- **Output format**: CSV is the required output; no database persistence needed in v1
- **Input formats**: PDF, Excel (.xlsx/.xls), PNG — other formats out of scope for v1

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| OCR + LLM pipeline | Handles inconsistent layouts across many document types and suppliers | — Pending |
| Two CSV output modes | Summary for tracking; line items for detailed analysis | — Pending |
| FastAPI as integration target | Standard Python web framework for ML/data services | — Pending |

---
*Last updated: 2026-03-17 after initialization*
