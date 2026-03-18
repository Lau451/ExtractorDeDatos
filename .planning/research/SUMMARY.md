# Project Research Summary

**Project:** DocExtract — Procurement Document Data Extraction System
**Domain:** Intelligent Document Processing (IDP) — LLM-based structured extraction from procurement documents
**Researched:** 2026-03-18
**Confidence:** HIGH (all core research verified against official sources)

## Executive Summary

DocExtract is a self-hosted IDP tool that extracts structured data from procurement documents (purchase orders, tenders, quotations, invoices, and supplier comparisons) and exports the results as CSV. The recommended architecture is a FastAPI backend using Docling for document normalization, Gemini 2.5 Flash (via the `google-genai` SDK) for structured field extraction, and a React SPA frontend with an inline-edit review UI. This stack is non-negotiable in two respects: `google-generativeai` was deprecated in November 2025 and must not be used, and LangChain adds unnecessary abstraction over Gemini's native `response_schema` support. The pipeline follows a clean layered model — Docling normalizes all formats to Markdown, the LLM receives only text, and per-document-type Pydantic schemas drive both extraction and CSV column ordering.

The product occupies a gap in the commercial IDP market: no per-page SaaS cost, supplier comparison as a first-class document type, and full schema ownership. Commercial tools (Nanonets, Rossum, Docsumo) have superior polished review UIs and batch processing, but they charge per page and lack native supplier comparison support. DocExtract's MVP must deliver the complete single-file extraction pipeline — upload, normalize, classify, extract, review, and download — before any differentiators are added.

The highest risks are operational rather than architectural. Docling can hang indefinitely on pathological PDFs (no built-in timeout), scanned PDFs are silently skipped unless OCR is force-enabled, and FastAPI closes the `UploadFile` handle before background tasks run. All three of these are invisible failures — no exception is thrown, jobs appear to succeed, but extracted data is empty or wrong. The mitigation for all three is build-time: enforce timeouts, force full-page OCR, and always read file bytes in the endpoint before handing off to a background task.

---

## Key Findings

### Recommended Stack

The stack is fully determined and all versions are current as of 2026-03-18. Python 3.10+ is the baseline — both Docling and `google-genai` require it. FastAPI 0.135.1 + Pydantic 2.12.5 handle the API layer; Pydantic v2 serves double duty as FastAPI's validation engine and as the native schema format Gemini's `response_schema` accepts. This eliminates any need for an additional schema translation layer.

Docling 2.80.0 replaces the prior multi-library stack (pdfplumber + Tesseract + openpyxl) with a single unified `DocumentConverter` that produces a `DoclingDocument` from PDF, XLSX, PNG/JPG, and HTML. Exporting to Markdown from `DoclingDocument` is the cleanest input format for Gemini — it preserves table structure and reading order. The `google-genai` 1.68.0 SDK provides async client support and native Pydantic `response_schema` integration; Gemini 2.5 Flash is the target model.

**Core technologies:**
- **Python 3.10+**: Runtime — minimum version required by both Docling and google-genai
- **FastAPI 0.135.1**: REST API layer — async-native, `UploadFile` + `BackgroundTasks` built in, OpenAPI docs automatic
- **Pydantic 2.12.5**: Data models — drives FastAPI validation AND Gemini `response_schema` from one definition; v2's Rust core is 17x faster than v1
- **Docling 2.80.0**: Document parsing — unified converter for PDF (native + OCR), XLSX, images, HTML; replaces 3-library chain
- **google-genai 1.68.0**: Gemini SDK — the only path to Gemini 2.5 Flash; predecessor `google-generativeai` is deprecated (November 2025, no new features)
- **uvicorn 0.42.0**: ASGI server — standard production runner for FastAPI with hot-reload in dev
- **pandas 2.x**: CSV export — `DataFrame.to_csv(encoding='utf-8-sig', index=False)` for Excel-compatible output
- **aiofiles 25.1.0**: Async file I/O — non-blocking temp file writes during ingestion pipeline

### Expected Features

The feature set is well-understood from the IDP market. The core value chain is: file upload → document type detection → field extraction → inline review/edit → CSV download. Every step is required for an analyst to replace manual data entry. The supplier comparison document type is unique to this product — no commercial tool handles it natively.

**Must have (table stakes):**
- Multi-format file ingestion (PDF, XLSX, PNG/JPG, HTML) — users expect all procurement formats
- Automatic document type detection (PO, tender, quotation, invoice, supplier comparison) — users must not pre-classify
- User override for detected document type — safety valve; misclassification rate ~10% at launch
- Structured field extraction for all 5 document types via Gemini 2.5 Flash — core value proposition
- Line item extraction (multi-row tables) — POs and invoices without line items are missing their most valuable data
- Inline review and edit UI before download — extracted data will have errors; correction is required before export
- CSV download with schema-correct column order — output must be deterministic and importable into ERP/Excel
- Extraction progress indicator — Gemini latency is 5–30 seconds; no feedback = perceived hang
- REST API (upload, status poll, CSV download) — enables testing and future integrations

**Should have (competitive differentiators):**
- Per-field confidence indicators — directs user review to uncertain fields; industry-standard in Mindee, extend.ai, Azure DI
- LLM provider abstraction (`LLMProvider` protocol) — protects against Gemini pricing/availability changes; one-file addition per provider
- OCR fallback transparency — surface whether OCR was used; sets accuracy expectations for scanned documents
- Extraction audit trail (original vs. corrected values) — traceability for quality analysis and user trust

**Defer (v2+):**
- User authentication / accounts — only if tool becomes multi-team or multi-tenant
- Persistent job history / dashboard — only if users need to revisit past extractions
- Batch upload (multiple files) — 3-4x implementation complexity; add only after single-file flow is stable
- ERP / accounting system integration — CSV is the integration layer for v1
- Three-way PO/invoice/receipt matching — requires persistent storage and a business rules engine

### Architecture Approach

The architecture is a classic async job pipeline exposed via REST, with a React SPA consumer. FastAPI accepts a file upload, immediately returns a `job_id`, and enqueues a `BackgroundTask` that runs the full pipeline: Docling normalization → document classification → Gemini extraction → result storage. The frontend polls `GET /jobs/{id}` until completion, then renders an inline-editable table. User edits accumulate in local React state and are flushed via `PATCH /jobs/{id}/fields` only when the user triggers CSV download — this avoids chatty per-keystroke API calls while keeping CSV generation server-authoritative.

**Major components:**
1. **React SPA** — File upload zone, status poller, inline-edit `ExtractionTable`, CSV download trigger
2. **FastAPI Service Layer** — Upload, job status, field PATCH, export, and health endpoints; owns the in-memory job store with `asyncio.Lock`
3. **Extraction Pipeline (BackgroundTask)** — Orchestrates ingestion → classify → extract → store; runs off the event loop
4. **Docling Ingestion Layer** — Single `DocumentConverter` instance (module-level, initialized once); normalizes all formats to Markdown
5. **Document Classifier** — Detects document type from normalized text; hybrid rule-based + LLM; exposes type to user before extraction
6. **LLM Provider Abstraction** — Abstract `LLMProvider` base; `GeminiProvider` implementation; swap provider by adding one file
7. **Per-Type Pydantic Schemas** — One schema per document type; drives Gemini `response_schema` and CSV column ordering via `SCHEMA_REGISTRY`
8. **CSV Formatter** — Per-type formatter dispatched from registry; returns `bytes` with `utf-8-sig` encoding

### Critical Pitfalls

All critical pitfalls are confirmed via GitHub issues and official documentation. None of them are theoretical.

1. **UploadFile closed before background task executes** — FastAPI closes the file handle at end-of-request (since v0.106.0). Always `await file.read()` in the endpoint and pass `io.BytesIO(content)` to the background task — never the `UploadFile` object. Failure mode is silent: job completes with all-null fields.

2. **Docling hangs indefinitely on certain PDFs** — Complex multi-column layouts or corrupt XRef tables can send DocLayNet into a runaway inference loop. Wrap every `DocumentConverter.convert()` in `asyncio.wait_for()` with a 120-second deadline. No timeout = jobs that never complete, no error raised.

3. **Scanned PDFs silently return empty text without explicit OCR configuration** — Docling's default PDF pipeline skips full-page OCR. Set `PdfPipelineOptions(do_ocr=True, ocr_options.force_full_page_ocr=True)` for all PDF inputs. Without this, Gemini receives empty text and returns all-null fields — again, silently.

4. **Gemini structured output guarantees syntax, not semantics** — `response_schema` ensures valid JSON conforming to the Pydantic shape; it does not prevent wrong values. Add field descriptions to each Pydantic field explaining procurement context (e.g., "the date the invoice was issued, NOT the due date"). Add a post-extraction validation layer checking date ordering (`due_date >= issue_date`) and numeric consistency (total ≈ sum of line items).

5. **Document type misclassification on visually similar documents** — PO vs. invoice, tender vs. RFQ share vocabulary. Zero-shot LLM classification achieves ~90% accuracy. Implement hybrid classification (rule-based structural signals + LLM fallback) and always expose the detected type to the user before extraction begins, with an override dropdown.

6. **In-memory job store race conditions** — Plain dict is not safe for concurrent async + background-thread access. Use `asyncio.Lock` protecting all read-modify-write operations on the job registry.

7. **Docling cold-start downloads ML models (~500MB–2GB) on first run** — Pre-download using `docling-tools models download` and set `DOCLING_ARTIFACTS_PATH`. Document this in dev setup instructions. First request in a fresh environment will otherwise timeout.

---

## Implications for Roadmap

Research from ARCHITECTURE.md defines a clear build order based on hard dependencies. Each layer is required before the next can be meaningfully built. The suggested phase structure below follows that order exactly.

### Phase 1: Foundation — File Ingestion and API Infrastructure

**Rationale:** Docling normalization is the input contract for everything else. The async job infrastructure (upload endpoint, job store with locking, background task pattern) must exist before any pipeline logic is wired in. Four of the seven critical pitfalls from PITFALLS.md must be addressed in this phase — all are invisible failure modes that corrupt everything downstream if not caught here.

**Delivers:** A running FastAPI server that accepts file uploads, stores jobs with proper async locking, runs Docling conversion in a background task with a hard timeout, handles scanned PDFs via force-OCR, and returns normalized Markdown text. No LLM calls yet.

**Features addressed:** Multi-format file ingestion (PDF, XLSX, PNG/JPG, HTML), extraction progress feedback (job status polling), REST API skeleton (upload + status endpoints), file size validation and MIME-type checking.

**Pitfalls to prevent:**
- UploadFile closed before background task (read bytes in endpoint)
- Docling hangs indefinitely (120-second timeout wrapper)
- Scanned PDFs silent empty extraction (force full-page OCR)
- Docling cold-start model download (pre-download in dev setup)
- In-memory race conditions (asyncio.Lock on job store)

**Research flag:** Standard patterns — well-documented FastAPI BackgroundTasks and Docling APIs. No additional research phase needed.

---

### Phase 2: Extraction Pipeline — Classification and Field Extraction

**Rationale:** Classification must precede extraction because Gemini's `response_schema` requires a concrete, narrow Pydantic schema (one per document type). A union schema with 40+ optional fields produces poor extraction quality. Classification therefore drives schema selection via the `SCHEMA_REGISTRY` pattern. The LLM provider abstraction must be introduced here — adding it after the fact requires rewriting all extractor classes.

**Delivers:** Full extraction pipeline: document classifier (hybrid rule-based + LLM), per-type Pydantic schemas (PO, tender, quotation, invoice, supplier comparison), `LLMProvider` protocol with `GeminiProvider` implementation, schema registry dispatch, and post-extraction validation rules for date ordering and numeric consistency.

**Features addressed:** Document type detection with user override, structured field extraction for all 5 document types, line item extraction (multi-row tables via Docling TableFormer + Gemini JSON arrays), LLM provider abstraction.

**Pitfalls to prevent:**
- Gemini semantic extraction errors (field descriptions in schemas, post-extraction validation)
- Document type misclassification (hybrid classification, user-visible type before extraction)
- Schema complexity causing Gemini 400 errors (flatten schemas, avoid deep nesting)
- Prompt injection via document content (extraction-scoping system prompt, text sanitization)

**Research flag:** Needs research during planning — per-type Pydantic schemas require careful field design (particularly supplier comparison, which has a non-standard output shape). Recommend `/gsd:research-phase` to validate schema designs against real procurement document samples before building extractors.

---

### Phase 3: Export — CSV Generation

**Rationale:** CSV formatting is isolated from the extraction logic — it reads a validated `ExtractionResult` and serializes to typed columns. Building it in isolation (against test fixture data) avoids blocking on a running extraction pipeline. Column ordering is schema-authoritative and must be consistent across all document types.

**Delivers:** Per-type CSV formatters, export dispatcher keyed by `DocumentType`, `utf-8-sig` encoding for Excel compatibility, `{doc_type}_{timestamp}.csv` filename pattern, and the `GET /jobs/{id}/export` endpoint.

**Features addressed:** CSV download with schema-correct column order, Excel-compatible encoding.

**Pitfalls to prevent:**
- CSV garbled in Excel (utf-8-sig encoding, not utf-8)
- Generic filename collisions in Downloads folder (timestamped filename)

**Research flag:** Standard patterns — pandas `to_csv` is well-documented. No research phase needed.

---

### Phase 4: Full API Integration — Field Edit and Complete Endpoint Surface

**Rationale:** With ingestion, extraction, and export all verified independently via test fixtures, this phase wires them together behind the complete FastAPI endpoint surface. The `PATCH /jobs/{id}/fields` endpoint for user edits is added here, completing the "edit before export" flow. The in-memory job store gets TTL-based cleanup to prevent memory growth.

**Delivers:** Complete REST API (upload, status poll, field PATCH, export, health), PATCH endpoint for user-edited field values, server-side edit merge into ExtractionResult before CSV generation, TTL job cleanup, and job-level error states with user-visible messages.

**Features addressed:** Complete REST API surface, edit persistence before export, error states for all failure conditions (Docling timeout, Gemini error, invalid file type, file too large).

**Pitfalls to prevent:**
- In-memory job results accumulate forever (TTL-based cleanup)
- 500 errors with stack traces reaching the user (structured error states per job)

**Research flag:** Standard patterns. No research phase needed.

---

### Phase 5: Web UI — React SPA

**Rationale:** The frontend depends only on the API contract (endpoint paths + response shapes). It can be built last with full confidence in the backend behavior, or developed in parallel against mocked responses. Building it last ensures no UI shortcuts influence backend design decisions.

**Delivers:** React SPA with Vite, upload zone (drag-and-drop), status poller with progress indicators, inline-editable `ExtractionTable` with human-readable field labels, document type display with override dropdown, and CSV download button that flushes edits before triggering export.

**Features addressed:** Review and edit UI, extraction progress indicator, user-overridable document type, CSV download trigger, human-readable field labels (not raw keys), visual indicator for null/not-found fields.

**Pitfalls to prevent:**
- No progress indicator during extraction (spinner with status text driven by polling)
- Exposing raw field keys in the review table (map to human-readable labels)
- Silent null fields in CSV (show "Not found" in review UI)
- Detected type shown after extraction (show type with override before extraction begins)
- Client-side CSV generation (always server-authoritative via PATCH + GET /export)

**Research flag:** Standard React patterns. Inline editing table patterns are well-documented. No research phase needed.

---

### Phase Ordering Rationale

- **Docling first:** It is the normalization gate. Cannot write extraction schemas without knowing what the text output looks like from real documents. Cannot test classifiers without real normalized text.
- **Schemas before provider:** Gemini's `response_schema` requires a concrete Pydantic model at call time. Define schemas first, verify they don't trigger `InvalidArgument 400`, then wire the provider.
- **Export before full API integration:** The CSV formatter is a pure function (ExtractionResult → bytes) that can be built and tested against fixture data without a running server. Building it in isolation avoids blocking on pipeline correctness.
- **Frontend last:** The React SPA only needs the API contract. Building it last means the contract is stable and tested. The Vite proxy to `localhost:8000` and typed `client.ts` wrapper make the boundary clean.
- **Pitfalls front-loaded:** All seven critical pitfalls that cause silent failures (UploadFile, Docling timeout, OCR, race conditions) are addressed in Phase 1 — before any extraction logic is written. This prevents invisible bugs from being baked into the pipeline.

### Research Flags

**Needs `/gsd:research-phase` during planning:**
- **Phase 2 (Extraction Pipeline):** The per-type Pydantic schemas require domain validation, particularly the supplier comparison schema (non-standard one-row-per-supplier output shape). Real document samples should be reviewed to validate field lists before schemas are coded. Line item flattening strategy (one CSV row per line item vs. header + items in separate columns) needs an explicit decision.

**Standard patterns (skip research-phase):**
- **Phase 1 (Foundation):** FastAPI BackgroundTasks, Docling DocumentConverter, asyncio.Lock patterns are all official-doc-verified with known implementations.
- **Phase 3 (Export):** pandas `to_csv` with utf-8-sig is a known, documented solution.
- **Phase 4 (API Integration):** REST endpoint wiring and in-memory TTL cleanup are standard patterns.
- **Phase 5 (Web UI):** React with Vite, status polling hooks, and inline table editing are well-documented patterns.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified against PyPI, official SDK docs, and deprecation notices. google-generativeai deprecation confirmed official. |
| Features | MEDIUM-HIGH | Table stakes and MVP scope are well-defined. Supplier comparison schema is the least standardized — no industry reference schema exists; requires domain validation. |
| Architecture | HIGH | Core patterns (async job, LLM provider abstraction, schema dispatch, Docling normalization gate) verified via official docs and multiple sources. Anti-patterns confirmed via real GitHub issues. |
| Pitfalls | HIGH | All critical pitfalls confirmed via GitHub issues (Docling #2635, #2047, #1630; FastAPI #10936, #11177), official API docs, and OWASP guidance. Not theoretical. |

**Overall confidence:** HIGH

### Gaps to Address

- **Supplier comparison schema field list:** No industry-standard reference exists for multi-vendor comparison documents. The field list in FEATURES.md (supplier name, unit price, total price, lead time, payment terms, warranty, delivery terms, compliance notes, overall score/rank) is based on procurement domain knowledge, not a formal standard. Validate against 2-3 real supplier comparison documents before coding the schema.

- **Line item CSV representation strategy:** Two valid approaches exist — one CSV row per line item (with header fields repeated) vs. separate header and line-item sections. This decision affects all 5 document type formatters and must be made explicitly in Phase 3 planning. Research did not surface a definitive industry preference.

- **Gemini token limits on long documents:** Documents over 50 pages may degrade extraction quality as soft attention limits are approached. No hard limit was identified — log token counts in Phase 2 and define a truncation strategy if documents over 50 pages are common in the target user's workflow.

- **Polling interval tuning:** Research recommends 1–2 second polling intervals. The optimal interval depends on actual Gemini latency in production — measure in Phase 2 and tune before Phase 5 frontend delivery.

---

## Sources

### Primary (HIGH confidence)
- [Docling PyPI — v2.80.0](https://pypi.org/project/docling/) — version, dependencies, OCR options
- [Docling official docs](https://docling-project.github.io/docling/) — supported formats, OCR configuration, full-page OCR example
- [Docling GitHub](https://github.com/docling-project/docling) — Issues #2635 (hang), #2047 (scanned PDF), #1630 (model download)
- [google-genai PyPI — v1.68.0](https://pypi.org/project/google-genai/) — version, structured output, async client
- [Google Gen AI SDK official docs](https://googleapis.github.io/python-genai/) — response_schema, Pydantic integration
- [google-generativeai deprecation — official GitHub](https://github.com/google-gemini/deprecated-generative-ai-python) — deprecated November 2025
- [Gemini structured output — Google AI for Developers](https://ai.google.dev/gemini-api/docs/structured-output) — response_schema + response_mime_type patterns
- [FastAPI PyPI — v0.135.1](https://pypi.org/project/fastapi/) — version
- [FastAPI Background Tasks — Official Docs](https://fastapi.tiangolo.com/tutorial/background-tasks/) — BackgroundTasks pattern
- [FastAPI GitHub — Discussions #10936, #11177](https://github.com/fastapi/fastapi/discussions/) — UploadFile lifecycle confirmed
- [Pydantic PyPI — v2.12.5](https://pypi.org/project/pydantic/) — version, v2 API
- [Mindee confidence scores](https://docs.mindee.com/extraction-models/optional-features/automation-confidence-score) — field-level confidence patterns
- [OWASP LLM Prompt Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html) — prompt injection mitigation

### Secondary (MEDIUM confidence)
- [Unstract IDP approaches](https://unstract.com/blog/comparing-approaches-for-using-llms-for-structured-data-extraction-from-pdfs/) — extraction architecture overview
- [Leapcell FastAPI long-running jobs](https://leapcell.io/blog/managing-background-tasks-and-long-running-operations-in-fastapi) — job ID + polling pattern
- [Nanonets PO OCR](https://nanonets.com/ocr-api/purchase-order-ocr) — competitor feature analysis
- [Docsumo IDP Trends 2025](https://www.docsumo.com/blogs/intelligent-document-processing/trends) — IDP market context
- [LandingAI Extraction Schema Best Practices](https://landing.ai/developers/extraction-schema-best-practices-get-clean-structured-data-from-your-documents) — schema design
- [google-genai GitHub Issue #1815](https://github.com/googleapis/python-genai/issues/1815) — additionalProperties schema validation bug
- [Thomas Wiegold — Invoice extraction prompts](https://thomas-wiegold.com/blog/building-reliable-invoice-extraction-prompts/) — prompt engineering for procurement docs
- [DataSci Ocean — FastAPI race conditions](https://datasciocean.com/en/other/fastapi-race-condition/) — job store locking

### Tertiary (reference only)
- [SAP Create Schema for PO Documents](https://developers.sap.com/tutorials/cp-aibus-dox-ui-schema..html) — PO field reference
- [Procycons PDF benchmark 2025](https://procycons.com/en/blogs/pdf-data-extraction-benchmark/) — Docling vs. alternatives

---
*Research completed: 2026-03-18*
*Ready for roadmap: yes*
