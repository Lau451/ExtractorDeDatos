# Codebase Concerns

**Analysis Date:** 2026-03-18

## Project Status

**Critical Finding:** This is a pre-implementation project with no source code. All concerns are planning-stage and architectural risk areas identified from requirements.

---

## Architectural Risks

**OCR + LLM Pipeline Integration:**
- Risk: OCR quality varies dramatically across document types (scanned PDFs vs images vs selectable PDFs). LLM extraction depends heavily on OCR quality, creating a cascade failure risk.
- Impact: If OCR produces degraded text for certain document types, LLM extraction will fail silently or produce low-confidence results. Users may not realize extraction failed.
- Mitigation approach: Implement per-stage validation with explicit OCR quality scoring before LLM processing. Fail fast with clear error messages. Log all OCR output for debugging.

**LLM Provider Abstraction:**
- Risk: Requirements demand "swappable LLM provider" (GPT/Claude/Gemini) but no abstraction layer is designed yet. Hard coupling to one provider will compound technical debt.
- Impact: Switching providers or supporting fallbacks becomes a major refactor. Cost optimization (cheaper provider for simple extractions) becomes impossible.
- Mitigation approach: Design provider adapter pattern from day one. Never call LLM SDK directly—route through provider abstraction. Create comprehensive provider interface before implementation begins.

**Asynchronous Job Model:**
- Risk: Requirements specify async processing with polling (POST /extract returns job ID, GET /export polls status). No database or job queue design specified.
- Impact: Job state persistence, timeout handling, and failure recovery are undefined. Risk of lost extraction results or zombie jobs.
- Mitigation approach: Define job storage strategy (Redis, database, in-memory) before Phase 4. Implement explicit job lifecycle (queued → processing → complete/failed).

---

## Scaling & Performance Concerns

**Batch Upload Processing:**
- Risk: Requirements allow "multiple files in a single request" but no upper limit, timeout, or resource constraint is defined.
- Impact: Single batch upload could exhaust memory (loading all files at once), timeout (processing 100+ files sequentially), or overwhelm LLM quota.
- Mitigation approach: Set batch size limits (e.g., 10 files max per request). Implement per-file timeout. Queue files independently instead of processing all at once.

**LLM API Cost & Quota:**
- Risk: Every document extraction calls an LLM API (GPT/Claude/Gemini). No rate limiting, cost monitoring, or fallback is mentioned.
- Impact: Unexpected spike in usage could result in API quota exhaustion or uncontrolled costs.
- Mitigation approach: Add token counting before making API calls. Implement per-user or per-batch rate limiting. Add cost tracking/alerting. Design cheaper extraction paths for high-confidence standard documents.

**Memory Usage for Large Documents:**
- Risk: PDF/image files could be large (10+ MB). Loading entire file into memory for OCR and processing could cause OOM.
- Impact: System crashes on large documents; service becomes unreliable in production.
- Mitigation approach: Stream file processing where possible. Implement file size validation upfront. For very large PDFs, split into pages and process separately.

---

## Data Quality & Validation Gaps

**Extraction Confidence Scoring:**
- Risk: Requirements specify "confidence score per extracted field" but no minimum threshold, user notification, or fallback behavior is defined.
- Impact: Users may accept low-confidence extractions (e.g., 30% confidence price field) without realizing data quality risk.
- Mitigation approach: Set minimum confidence thresholds per field type (prices must be >80% confident). Flag low-confidence fields in output. Implement manual review queue in Phase 2.

**Field-Level Validation:**
- Risk: Requirements list v2 features including "price must be numeric, date must parse" but v1 has no validation framework.
- Impact: Garbage data flows into CSV output (malformed dates, non-numeric prices). User discovers problems during analysis, not extraction.
- Mitigation approach: Implement field validation schema in Phase 1, even if validation is optional. Define allowed formats for critical fields (date, price, quantity). Log validation failures for debugging.

**Supplier Comparison Logic:**
- Risk: COMP-03 requires "flags the lowest price per line item" but no logic for handling multi-currency prices, bulk discounts, or unit mismatches is defined.
- Impact: Comparison output could misleadingly flag "low price" without context (e.g., price in different currency or unit).
- Mitigation approach: Require explicit currency and unit fields in extracted data. Implement comparison logic to handle currency conversion or warn on unit mismatches. Don't assume prices are directly comparable.

---

## Security Considerations

**File Upload Handling:**
- Risk: System accepts arbitrary file uploads (PDF, Excel, PNG) from internal users with no validation or virus scanning mentioned.
- Impact: Malicious files could execute code (e.g., Excel macros, embedded scripts in PDFs) or corrupt the system.
- Mitigation approach: Validate file signatures/magic bytes (not just extensions). Disable auto-execution in Office documents. Consider sandboxed file processing. Add basic malware scanning for production.

**LLM API Keys in Environment:**
- Risk: Requirements mention configuration for LLM providers but no secret management strategy is defined.
- Impact: API keys could be accidentally committed, logged, or exposed in error messages.
- Mitigation approach: Use environment variables only (.env files, never committed). Implement secret masking in logs. Use short-lived tokens where possible. Document secret rotation procedures.

**Data Privacy for Extracted Content:**
- Risk: System extracts and processes sensitive business data (supplier prices, client names, tender details) with no retention or access control policy.
- Impact: Extracted data could persist in logs, error messages, or database longer than needed. No audit trail of who accessed what.
- Mitigation approach: Define data retention policy (delete extracted data after X days). Log access to sensitive extractions. Implement field-level masking in logs. Consider encryption for data at rest.

---

## Testing & Validation Gaps

**No Test Data Strategy:**
- Risk: Requirements don't specify which document types to test with first, or how to validate extraction quality.
- Impact: Implementation could succeed technically but fail to extract real-world documents correctly.
- Mitigation approach: Build test document set in Phase 1 (real examples of invoice, PO, tender, quotation, comparison docs). Define acceptance criteria per document type before implementation.

**OCR Quality Baseline:**
- Risk: No baseline OCR accuracy is defined. System could pass tests with good PDFs but fail on scanned documents.
- Impact: Feature ships with poor support for scanned documents, defeating the primary value proposition.
- Mitigation approach: Test OCR on both selectable PDFs and scanned images. Define minimum accuracy threshold (e.g., >90% character recognition). Log OCR confidence per document.

**LLM Extraction Accuracy:**
- Risk: No benchmark for extraction accuracy is defined. System could extract wrong fields or miss key data without detection.
- Impact: Users discover data quality issues after CSV download; trust in system erodes.
- Mitigation approach: Build validation dataset with known correct extractions. Measure extraction accuracy against benchmark. Track regression per release.

---

## Known Planning Oversights

**Multi-Currency Support:**
- Issue: Supplier comparison requires price comparison but no currency handling mentioned.
- Files: REQUIREMENTS.md references COMP-03 but doesn't define currency handling.
- Impact: Comparison output could be meaningless across international suppliers.
- Fix approach: Add currency field to extraction schema. Require currency in supplier comparison output. Warn if currencies differ.

**Document Type Auto-Detection:**
- Issue: LLM-03 requires "auto-detects document type" but no fallback if detection fails is defined.
- Files: REQUIREMENTS.md LLM-03 feature.
- Impact: System could fail silently if document type is ambiguous or unrecognized.
- Fix approach: If auto-detection confidence is low (<70%), ask user to specify type. Implement type-specific extraction templates as fallback.

**API Error Handling:**
- Issue: API endpoints (API-01 through API-04) are specified but error responses are not detailed.
- Files: REQUIREMENTS.md API section.
- Impact: Client integration becomes brittle; no standard error format.
- Fix approach: Define HTTP status codes for all failure modes (400 for bad file, 413 for too large, 422 for unprocessable, 500 for server errors). Return consistent JSON error response with error code and message.

**Job State Persistence:**
- Issue: GET /export polls for results but no indication of how job state persists across service restarts.
- Files: REQUIREMENTS.md API-02, API-04.
- Impact: Long-running extractions could be lost if service crashes. Users unable to retrieve results.
- Fix approach: Require durable job storage (database or Redis, not in-memory). Implement job recovery on restart. Define job retention window (e.g., 7 days).

---

## Dependencies & External Services at Risk

**OCR Library Choice:**
- Risk: No OCR library is selected yet. Choice between pytesseract (free, lower quality), commercial Tesseract, or cloud APIs (Google Vision, AWS Textract) will impact cost and accuracy.
- Impact: Switching OCR providers mid-project is expensive. Cost scaling could exceed budget if high-volume processing is required.
- Mitigation approach: Evaluate and select OCR library in Phase 1. Benchmark against test documents before committing to API-based solutions.

**PDF Processing Library:**
- Risk: PDF extraction without OCR (OCR-01: "extracts text directly from selectable PDFs") requires PDF parsing library. Malformed PDFs could crash parser.
- Impact: Single malformed PDF in batch could crash entire extraction job.
- Mitigation approach: Wrap PDF parsing in try-catch. Validate PDF integrity before processing. Fall back to OCR if text extraction fails.

**Excel Reading:**
- Risk: INGEST-02 requires .xlsx and .xls support. XLS (older binary format) is harder to parse and more corruption-prone than XLSX.
- Impact: Corrupted Excel files could crash system or hang during parsing.
- Mitigation approach: Use robust library (openpyxl for XLSX, xlrd for XLS with validation). Add file size limits for Excel. Skip corrupted sheets with warning.

---

## Phase-Specific Risks

**Phase 1 (File Ingestion + OCR):**
- Risk: Making OCR work reliably across PDF, image, and Excel is complex. Underestimating this work could delay phases 2-4.
- Impact: All downstream phases depend on clean OCR output.
- Mitigation approach: Allocate buffer time in Phase 1. Test OCR exhaustively with all document types before Phase 2 starts.

**Phase 2 (LLM Extraction):**
- Risk: LLM extraction quality depends on OCR quality from Phase 1. If OCR is poor, LLM tasks become much harder.
- Impact: Phase 2 could stall waiting for Phase 1 improvements.
- Mitigation approach: Establish minimum OCR quality bar before Phase 2 begins. Have fallback extraction logic if LLM confidence is low.

**Phase 3 (CSV Export + Supplier Comparison):**
- Risk: Supplier comparison logic (finding "lowest price") requires resolved, normalized data. If Phase 1-2 extraction is incomplete, comparison will be meaningless.
- Impact: CSV output could be incorrect or misleading.
- Mitigation approach: Enforce data normalization in Phase 2. Validate comparison logic against hand-curated examples.

**Phase 4 (API Integration):**
- Risk: API layer is last, but it's a first-class requirement. Rushing Phase 4 could introduce race conditions, state management bugs, or timeout issues.
- Impact: API becomes unreliable in production despite solid extraction logic in Phases 1-3.
- Mitigation approach: Start API design early (Phase 2). Implement job queue and state management before Phase 4 implementation begins.

---

## Recommendations for Implementation Start

1. **Front-load OCR validation** — Test OCR on real document samples from Phases 1. Define quality acceptance criteria before implementation.

2. **Design LLM provider abstraction** — Create provider interface before writing extraction logic. Never directly call LLM SDKs.

3. **Plan job persistence** — Select database/queue solution for job state before Phase 4. Implement in Phase 2 to avoid last-minute rework.

4. **Set operational limits** — Define batch size, file size, timeout, and rate limits before implementation. Implement in Phase 1.

5. **Build test document set** — Collect real invoice, PO, tender, quotation, and comparison documents from actual business context before Phase 2.

6. **Define error handling contract** — Specify HTTP status codes and error JSON format before Phase 4 API work.

---

*Concerns audit: 2026-03-18*
