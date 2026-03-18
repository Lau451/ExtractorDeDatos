# Feature Research

**Domain:** Intelligent Document Processing (IDP) — Procurement Document Extraction
**Researched:** 2026-03-18
**Confidence:** MEDIUM-HIGH (IDP landscape well-documented; supplier comparison schema less standardized)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Multi-format file ingestion (PDF, image, Excel, HTML) | Every IDP product supports PDF at minimum; procurement docs arrive in all formats | MEDIUM | Docling handles all four. OCR fallback needed for scanned PDFs/images. |
| Automatic document type detection | Users should not have to tell the system what kind of document they uploaded | MEDIUM | Classification prompt to Gemini before extraction; user override required as safety valve. |
| Structured field extraction per document type | Core value prop — without this, the tool is just an OCR viewer | HIGH | Separate extractor per doc type (PO, tender, quotation, invoice, supplier comparison). Gemini 2.5 Flash with typed JSON schema. |
| Line-item extraction (not just header fields) | POs, invoices, and quotations all contain multi-row tables of goods/services | HIGH | Docling TableFormer handles table structure. LLM must emit array of line-item objects. Flattening to CSV rows is non-trivial. |
| Review UI before download | Extracted data has errors; users need to correct before using | MEDIUM | Inline-editable table. Every modern IDP product (Rossum, Docsumo, Nanonets) has this. |
| CSV download | Procurement teams live in Excel/CSV; output must be portable | LOW | Trivial once schema is defined. Column order must match predefined schema. |
| Extraction progress feedback | LLM calls take 5-30 seconds; blank screen = confusion | LOW | Polling status endpoint + spinner/progress indicator in UI. |
| User-overridable document type | Auto-detection will sometimes be wrong; user must be able to correct | LOW | Dropdown before triggering extraction. |
| Per-document-type CSV schema | A PO schema is fundamentally different from an invoice schema | MEDIUM | Tenders and Quotations schemas already exist. PO, Invoice, Supplier Comparison need design. |
| Defined header + line-item field split | Industry-standard pattern: header fields appear once, line items repeat per row | MEDIUM | Header fields as single CSV row vs. one row per line item is a key schema decision. |

---

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Per-field confidence indicators | Shows users which fields the LLM was uncertain about, directing review effort | MEDIUM | Gemini can be prompted to return a confidence score alongside each field value. Color-code LOW/MEDIUM/HIGH in UI. Industry standard in Mindee, extend.ai, Azure Document Intelligence. |
| Structured schema-driven extraction (not free-form) | Deterministic column order and field names; downstream tools (ERP, Excel) can rely on the output shape | MEDIUM | Schema-as-code approach. Each doc type has a Python dataclass or Pydantic model defining the output contract. |
| OCR fallback transparency | Tell user when OCR was used vs. native text parsing; sets accuracy expectations | LOW | Log whether Docling used native text or OCR for a given document. Surface in UI. |
| Supplier comparison matrix output | Unique to procurement use case — extracts multiple vendor bids into a single comparison row per supplier | HIGH | The hardest document type. Input may be a multi-sheet Excel or a structured table. Output enables side-by-side price/spec analysis without manual work. |
| LLM provider abstraction | Allows swapping Gemini for OpenAI/Anthropic without rewriting extractors | MEDIUM | Defined interface: `extract(doc_text, schema) -> dict`. Implementation selects provider. Protects against API pricing/availability changes. |
| Extraction audit trail (field-level) | Shows original extracted value alongside user-corrected value in the CSV | LOW | Add `_original` shadow columns or a separate audit CSV. Useful for quality analysis. Adds value for teams that need traceability. |

---

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Batch upload (multiple files at once) | Procurement teams process many documents | Multiplies complexity: parallel LLM calls, per-file status tracking, partial failure handling, ZIP download. Adds 3-4x implementation work for v1. | Explicitly out of scope for v1. Process one file at a time; iterate quickly. Add in v2 after single-file flow is stable. |
| Persistent job history / dashboard | "I want to see my past extractions" | Requires a database, session management, and a history UI. Turns an internal tool into a SaaS product prematurely. | In-memory only for v1. If history is needed, users download CSV and keep it themselves. |
| Real-time streaming extraction | "Show fields appearing as they extract" | LLM streaming for structured JSON is unreliable — partial JSON is not parseable until complete. Complex UI state management. | Show a spinner until extraction completes, then render the full result. |
| User authentication / accounts | "Only certain users should access this" | Adds auth middleware, token management, session storage — none of which relates to the core extraction pipeline. | Internal tool on internal network. No auth for v1. Defer to v2 if multi-tenant use emerges. |
| Template-based extraction (per-vendor templates) | "Our supplier always sends the same format" | Template management UI is a product in itself. Breaks generalization — Gemini handles format variation natively. | Schema-driven extraction with field descriptions handles format variation without templates. |
| Three-way PO/invoice/receipt matching | "Automatically match invoices to POs" | Requires persistent storage, cross-document linking, business rules engine. Core use case is extraction, not workflow automation. | Extract each document independently. Let the user reconcile in their ERP/Excel. |
| ERP integration (SAP, Dynamics, etc.) | "Push extracted data directly to our system" | Each ERP has a different API, auth, and data model. Becomes an integration project, not an extraction tool. | CSV output is the integration layer. Users import CSV into their ERP manually. |
| Mobile / responsive design optimization | "I want to upload from my phone" | Procurement document workflows are desktop-first. Mobile adds CSS complexity for zero incremental user value. | Web-first desktop UI. Responsive layout is acceptable but not optimized for mobile. |

---

## Feature Dependencies

```
File Upload
    └──requires──> Document Parsing (Docling)
                       └──requires──> Document Type Detection
                                          └──requires──> Field Extraction (Gemini)
                                                             └──requires──> Review UI
                                                                                └──requires──> CSV Download

Line Item Extraction
    └──requires──> Field Extraction (Gemini)
    └──requires──> Table Structure Parsing (Docling TableFormer)

Confidence Indicators
    └──enhances──> Review UI
    └──requires──> Field Extraction (Gemini) [confidence scores in prompt response]

OCR Fallback
    └──enhances──> File Upload [handles scanned PDFs and images]
    └──requires──> Document Parsing (Docling OCR mode)

LLM Provider Abstraction
    └──enhances──> Field Extraction
    └──conflicts──> Hard-coded Gemini SDK calls [must route through interface, not direct]

Extraction Progress Feedback
    └──requires──> Async job model (in-memory)
    └──enhances──> Review UI [user sees status before result loads]

Supplier Comparison Extraction
    └──requires──> Field Extraction (Gemini)
    └──requires──> Multi-sheet Excel parsing (Docling XLSX support)
    └──has extra complexity──> Output schema is non-standard (one row per supplier bid)
```

### Dependency Notes

- **File Upload requires Document Parsing:** Ingestion is the entry point; all downstream features depend on Docling producing clean text/structure.
- **Line Item Extraction requires both Gemini and Docling TableFormer:** Table structure must be preserved through the parsing stage so the LLM receives rows and columns, not flattened text.
- **Confidence Indicators require prompt engineering:** Gemini must be instructed to return confidence alongside values; this is a prompt-level decision, not a separate API call.
- **LLM Provider Abstraction conflicts with direct SDK usage:** If code calls `google.generativeai` directly in extractor classes, swapping providers requires a rewrite. The abstraction interface must be introduced from day one.
- **Supplier Comparison is the hardest dependency chain:** It requires multi-sheet Excel support, a non-standard output schema, and domain knowledge about what a "supplier comparison" looks like across different document styles.

---

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed for a procurement analyst to replace manual data entry.

- [ ] PDF, Excel (XLSX/XLS), image (PNG/JPG), and HTML file upload — without this, most documents cannot be ingested
- [ ] Document type detection (PO, tender, quotation, invoice, supplier comparison) — user should not need to pre-classify
- [ ] User override for detected document type — safety valve for misclassifications
- [ ] Structured field extraction for all 5 document types via Gemini 2.5 Flash — the core value prop
- [ ] Line item extraction (multi-row tables) — POs and invoices without line items are missing their most valuable data
- [ ] Inline review and edit UI before download — extracted data will have errors; correction must happen before export
- [ ] CSV download with schema-correct column order — output must be deterministic and importable
- [ ] Extraction progress indicator — LLM latency requires feedback to avoid perceived hangs
- [ ] REST API (upload, status poll, CSV download) — enables future integrations and testing without UI

### Add After Validation (v1.x)

Features to add once core pipeline is proven stable.

- [ ] Per-field confidence indicators — add once extraction accuracy is measured in the wild; requires prompt tuning
- [ ] OCR fallback transparency — surface whether OCR was used; useful once users report accuracy issues with scanned docs
- [ ] Extraction audit trail (original vs. corrected values) — add when users ask "what did the system get wrong?"
- [ ] Batch upload (2-5 files) — add when single-file flow is stable and users express the need repeatedly

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] User authentication / accounts — only if tool becomes multi-team or multi-tenant
- [ ] Persistent job history / dashboard — only if users need to revisit past extractions
- [ ] ERP / accounting system integration (SAP, Dynamics, QuickBooks) — only if CSV import proves too slow for users
- [ ] Three-way PO/invoice matching — only if the tool evolves into a procurement workflow product
- [ ] Custom extraction schema builder (no-code) — only if different teams need different fields

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Multi-format file ingestion | HIGH | MEDIUM | P1 |
| Document type detection | HIGH | MEDIUM | P1 |
| Field extraction (all 5 doc types) | HIGH | HIGH | P1 |
| Line item extraction | HIGH | HIGH | P1 |
| Review and edit UI | HIGH | MEDIUM | P1 |
| CSV download | HIGH | LOW | P1 |
| Extraction progress feedback | MEDIUM | LOW | P1 |
| User type override | MEDIUM | LOW | P1 |
| REST API | MEDIUM | LOW | P1 |
| Per-field confidence indicators | MEDIUM | MEDIUM | P2 |
| LLM provider abstraction | LOW (user) / HIGH (maintainer) | MEDIUM | P2 |
| OCR transparency | LOW | LOW | P2 |
| Extraction audit trail | MEDIUM | LOW | P2 |
| Batch upload | MEDIUM | HIGH | P3 |
| Persistent job history | LOW | HIGH | P3 |
| ERP integration | MEDIUM | HIGH | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

| Feature | Nanonets / Parseur | Rossum / Docsumo | DocExtract (Our Approach) |
|---------|-------------------|-----------------|--------------------------|
| Multi-format ingestion | PDF, image, email | PDF, image, email | PDF, Excel, image, HTML via Docling |
| Document type detection | Model-per-type, manual setup | Auto-classify with training | Zero-shot via Gemini prompt |
| Line item extraction | Yes — trained models | Yes — trained models | Yes — Docling tables + Gemini JSON |
| Review / correction UI | Yes — full validation UI | Yes — full validation UI | Inline edit table, same-page |
| Confidence scores | Yes — field-level | Yes — field-level | Optional (v1.x), prompt-based |
| CSV / structured export | Yes | Yes | Yes — schema-strict column order |
| Batch processing | Yes | Yes | No (v1 deliberate) |
| ERP integration | Yes (paid tiers) | Yes (paid tiers) | No (CSV is the integration) |
| Supplier comparison support | Not native | Not native | Yes — dedicated doc type |
| Cost model | Per-page SaaS fee | Per-page SaaS fee | Self-hosted, no per-page cost |

**Key insight:** Commercial IDP tools are trained on millions of documents and have polished review UIs, but they charge per-page and don't have native supplier comparison support. DocExtract's advantage is zero marginal cost per document (internal Gemini quota), supplier comparison as a first-class type, and full ownership of the extraction schema.

---

## Document Type Field Reference

Standard fields expected per document type, based on industry patterns. Schemas with an asterisk (*) are already defined.

### Purchase Order (PO)
**Header:** PO number, issue date, buyer name/entity, vendor name, vendor address, billing address, shipping address, payment terms, delivery date, currency, total amount, notes.
**Line items:** Item number, description/product name, SKU/part number, quantity, unit, unit price, line total, tax rate, tax amount.

### Tender / RFQ *
**Header:** Tender reference, issue date, issuing organization, submission deadline, contact person, project/scope title, currency, notes.
**Line items:** Item number, description, specification, required quantity, unit, estimated budget (optional).

### Quotation *
**Header:** Quote number, quote date, vendor name, vendor address, buyer name, valid until date, currency, subtotal, tax total, grand total, payment terms, delivery terms.
**Line items:** Item number, description, quantity, unit, unit price, discount, line total, tax.

### Invoice
**Header:** Invoice number, invoice date, due date, vendor name, vendor address, buyer name, buyer address, currency, subtotal, tax total, grand total, payment terms, PO reference (if present), bank details.
**Line items:** Item number, description, quantity, unit, unit price, line total, tax rate, tax amount.

### Supplier Comparison
**Header:** Comparison date, buyer organization, RFQ/tender reference, evaluation criteria, notes.
**Per-supplier row:** Supplier name, item/service description, unit price, total price, lead time, payment terms, warranty, delivery terms, compliance notes, overall score/rank.

---

## Sources

- [Docling GitHub — IBM Research](https://github.com/docling-project/docling) — HIGH confidence (official repo)
- [Nanonets Purchase Order OCR API](https://nanonets.com/ocr-api/purchase-order-ocr) — MEDIUM confidence
- [Parseur Purchase Order OCR](https://parseur.com/extract-data/purchase-order-ocr) — MEDIUM confidence
- [Unstract Purchase Order OCR Guide 2026](https://unstract.com/blog/guide-to-purchase-order-ocr/) — MEDIUM confidence
- [Mindee Confidence Score](https://docs.mindee.com/extraction-models/optional-features/automation-confidence-score) — HIGH confidence (official docs)
- [extend.ai Confidence Scores](https://docs.extend.ai/product/extraction/confidence-scores) — HIGH confidence (official docs)
- [LandingAI Extraction Schema Best Practices](https://landing.ai/developers/extraction-schema-best-practices-get-clean-structured-data-from-your-documents) — MEDIUM confidence
- [Algodocs Purchase Order Data Extraction 2025 Guide](https://www.algodocs.com/purchase-order-data-extraction-2025-guide/) — MEDIUM confidence
- [Docsumo IDP Trends 2025](https://www.docsumo.com/blogs/intelligent-document-processing/trends) — MEDIUM confidence
- [SpecLens AI-Powered Specification Comparison](https://www.speclens.ai/) — MEDIUM confidence (competitor reference)
- [SAP Create Schema for Purchase Order Documents](https://developers.sap.com/tutorials/cp-aibus-dox-ui-schema..html) — HIGH confidence (official SAP docs)

---

*Feature research for: Intelligent Document Processing — Procurement Document Extraction (DocExtract)*
*Researched: 2026-03-18*
