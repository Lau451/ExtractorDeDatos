# External Integrations

**Analysis Date:** 2026-03-18

## APIs & External Services

**LLM Providers (Phase 2, swappable via configuration):**
- OpenAI (GPT-4 / GPT-3.5-turbo) - Primary LLM for field extraction and document type detection
  - SDK/Client: `openai` Python package
  - Auth: Environment variable `OPENAI_API_KEY`
  - Usage: Extraction of structured fields (client name, line items, prices, dates, reference numbers) from document text
  - Endpoint: OpenAI REST API (https://api.openai.com/v1)

- Anthropic (Claude 3.5 / Claude 3 / Claude 2) - Alternative LLM provider (pluggable)
  - SDK/Client: `anthropic` Python package
  - Auth: Environment variable `ANTHROPIC_API_KEY`
  - Usage: Drop-in replacement for OpenAI via configuration
  - Endpoint: Anthropic REST API (https://api.anthropic.com)

- Google (Gemini 2.0 / Gemini 1.5) - Alternative LLM provider (pluggable)
  - SDK/Client: `google-generativeai` Python package
  - Auth: Environment variable `GOOGLE_API_KEY`
  - Usage: Drop-in replacement for OpenAI via configuration
  - Endpoint: Google Generative AI API

**Configuration:**
- Set `LLM_PROVIDER` environment variable to switch providers
- No code changes required to swap LLM providers (Phase 2 requirement)
- All providers must accept same input (extracted document text) and return same output (structured fields with confidence scores)

## Data Storage

**Databases:**
- None (v1 is stateless)
- In-memory job tracking acceptable for v1 (job ID → extraction status and results)
- Future (Phase 5+): PostgreSQL for persistent job history and document archival

**File Storage:**
- Local filesystem only (v1)
- Uploads directory: `uploads/` (temporary storage during processing)
- Outputs directory: `outputs/` (CSV files for download)
- Both directories cleared after successful download (no persistence requirement in v1)
- Future (Phase 5+): S3 or Azure Blob Storage for document archival

**Caching:**
- None (v1)
- Future: Redis for LLM response caching if working with duplicate documents

## Authentication & Identity

**Auth Provider:**
- Custom (none in v1)
- No user authentication required (internal tool, single team)
- Future (v2+): Optional API key validation if exposed to external systems

## Monitoring & Observability

**Error Tracking:**
- Not integrated (v1)
- Future: Sentry or Datadog for production monitoring
- Currently: Structured logging to stdout/files sufficient

**Logs:**
- Approach: Python logging module with configurable levels
- Output: stdout (development), files (production ready)
- Structured logging for job lifecycle (upload → extraction → completion or failure)
- Error logging for LLM failures, OCR failures, file format errors
- Timestamp, job ID, and operation type in all log messages

## CI/CD & Deployment

**Hosting:**
- Not yet defined (Phase 5 concern)
- Target: Docker containerization with ASGI server (uvicorn)
- Deployment platform: Not specified (AWS Lambda, Docker on EC2, GCP Cloud Run, or on-premise all viable)

**CI Pipeline:**
- Not yet set up (pre-implementation)
- Recommended (future): GitHub Actions or similar for:
  - Linting (flake8, black)
  - Unit tests (pytest)
  - Integration tests (pytest with mock LLMs)
  - Dependency scanning

## Environment Configuration

**Required env vars (Phase 1-4):**
- `LLM_PROVIDER` - One of: "openai", "anthropic", "google" (Phase 2)
- `OPENAI_API_KEY` - If using OpenAI (if LLM_PROVIDER="openai")
- `ANTHROPIC_API_KEY` - If using Anthropic (if LLM_PROVIDER="anthropic")
- `GOOGLE_API_KEY` - If using Google (if LLM_PROVIDER="google")
- `TESSERACT_PATH` - Path to Tesseract OCR executable
  - Windows example: `C:\Program Files\Tesseract-OCR\tesseract.exe`
  - Linux example: `/usr/bin/tesseract`
  - macOS example: `/usr/local/bin/tesseract`
- `API_HOST` - Server bind address (default: 0.0.0.0)
- `API_PORT` - Server port (default: 8000)

**Secrets location:**
- `.env` file (not committed to git, created locally per environment)
- .gitignore includes: `.env`, `.env.local`, `*.pem`, `*.key`
- Production: Secrets manager (environment-specific: AWS Secrets Manager, Azure Key Vault, etc.)

## Webhooks & Callbacks

**Incoming:**
- None (v1)
- Future: Potential webhook for extraction completion notifications

**Outgoing:**
- None (v1)
- Future: Potential webhooks to notify external systems when extraction completes

## File Format Support (Input Integration)

**Phase 1 Formats:**
- PDF (text-based) - Extracted via pdfplumber text layer
- PDF (scanned/image-based) - Extracted via Tesseract OCR
- Excel (.xlsx, .xls) - Extracted via openpyxl
- PNG / JPEG / TIFF (images) - Extracted via Tesseract OCR with Pillow preprocessing

**Future Formats (Phase 2, v2 scope):**
- DOCX (Word documents)
- Multi-page TIFF
- URL-based document ingestion (fetch and process from HTTP link)

## CSV Output Integration (Output Format)

**Phase 3 Exports:**
- Summary CSV: One row per document (document type, client/supplier name, date, total value, reference number)
- Line Items CSV: One row per extracted line item (product description, quantity, unit price, total price, source document)
- Supplier Comparison CSV: Side-by-side supplier data with best-price flagging per line item

**Download Mechanism (Phase 4):**
- GET /export endpoint serves CSV files as downloadable attachments
- Optional: In-memory streaming for large datasets (post-v1 optimization)

## Content Processing Pipeline (Internal Integration)

**Data Flow:**
1. User uploads file(s) → FastAPI POST /extract endpoint
2. File ingestion module routes based on format (Phase 1)
3. Text extraction module produces raw text (Phase 1)
   - PDF text layer OR Tesseract OCR OR Excel cell reader
4. LLM extraction module (Phase 2)
   - Text → LLM provider API → Structured fields + confidence scores
5. Comparison logic (Phase 3)
   - Synthesize supplier comparison from individual documents
6. CSV export module (Phase 3)
   - Generate all three CSV formats
7. Job completion → Client polls GET /status or /export (Phase 4)

## Summary of External Dependencies

**Critical API Integrations:**
- At least one LLM provider (OpenAI, Anthropic, or Google required)
- Tesseract OCR system binary (required for Phase 1)

**Pluggable Providers:**
- LLM provider selection via `LLM_PROVIDER` config (Phase 2)
- All three providers (OpenAI, Anthropic, Google) must behave identically to application

**No External Dependencies (v1):**
- No database required
- No file storage service (local filesystem only)
- No authentication provider
- No monitoring/observability integration
- No CI/CD automation
- No container registry

---

*Integration audit: 2026-03-18*
*Status: Pre-implementation (Phase 1 planning)*
*Last updated: Technology selection based on v1 requirements and 4-phase roadmap*
