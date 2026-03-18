# Stack Research

**Domain:** Document data extraction system — procurement documents (POs, tenders, invoices, quotations, supplier comparisons)
**Researched:** 2026-03-18
**Confidence:** HIGH (all versions verified against PyPI, official docs, and Google's SDK migration announcement)

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.10+ | Runtime | Docling and google-genai both require >=3.10; type hints, match statements, and asyncio improvements used by FastAPI are stable from 3.10 onward |
| FastAPI | 0.135.1 | REST API layer | Native async/await, automatic OpenAPI docs, UploadFile with streaming, BackgroundTasks for fire-and-forget extraction jobs — the only Python framework designed for this exact pattern |
| Pydantic | 2.12.5 | Data models and validation | FastAPI's internal validation engine; v2 is 17x faster than v1 (Rust core); also the native schema format the Gemini SDK accepts for `response_schema` — one model definition drives both API validation and LLM output structure |
| Docling | 2.80.0 | Document parsing and normalization | IBM/LF AI project; handles PDF (layout + reading order), XLSX, images (PNG/JPG/TIFF), and HTML into a single `DoclingDocument` representation; replaces the pdfplumber + Tesseract + openpyxl multi-library chain; built-in OCR engine selection (EasyOCR or Tesseract) |
| google-genai | 1.68.0 | Gemini 2.5 Flash SDK | The **new** unified Google Gen AI SDK — `google-generativeai` was deprecated November 2025; `google-genai` is GA, supports `response_schema` with Pydantic models natively, supports async client, and is the only path to Gemini 2.5 Flash features |
| uvicorn | 0.42.0 | ASGI server | Standard production-grade runner for FastAPI; `uvicorn[standard]` includes watchfiles (hot reload) and httptools (performance) |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-multipart | 0.0.22 | Multipart form-data parsing | Required by FastAPI for all `UploadFile` endpoints — without it FastAPI raises a `RuntimeError` at file upload time |
| aiofiles | 25.1.0 | Async file I/O | Write temp files non-blocking during extraction pipeline; prevents blocking the event loop when saving large PDFs or images before Docling processes them |
| python-dotenv | 1.0.x | Environment variable loading | Load `GOOGLE_API_KEY`, `API_HOST`, `API_PORT` from `.env` without touching shell config; works across Windows/Linux dev environments |
| pandas | 2.x | CSV generation and export | Construct typed DataFrames from extraction results; write CSV with `to_csv(index=False)` enforcing column order per schema; `io.StringIO` approach avoids writing to disk for streaming download |
| pytest | 8.x | Unit and integration testing | Standard; use `pytest-asyncio` for async FastAPI endpoint tests |
| pytest-asyncio | 0.24.x | Async test support | Required to `await` async FastAPI routes and Docling calls in tests |
| httpx | 0.27.x | Test client for FastAPI | FastAPI's `TestClient` uses httpx under the hood; also needed if you write async test clients directly |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| uvicorn (dev mode) | Hot-reload server | Run as `uvicorn main:app --reload`; `uvicorn[standard]` installs `watchfiles` for file-change detection |
| python-dotenv | `.env` management | Call `load_dotenv()` at app startup; never commit `.env` |
| pyproject.toml | Dependency declaration | Prefer `pyproject.toml` over bare `requirements.txt`; supports `[project.optional-dependencies]` for separating test deps |

---

## Installation

```bash
# Core runtime
pip install "fastapi==0.135.1" "uvicorn[standard]==0.42.0" "pydantic==2.12.5"

# Document parsing (Docling + OCR)
pip install "docling==2.80.0"
# Docling installs EasyOCR by default for scanned pages.
# For Tesseract as OCR fallback (lighter, better on clean scans):
pip install "docling[tesserocr]"

# LLM (use google-genai, NOT google-generativeai)
pip install "google-genai==1.68.0"

# File upload and async I/O
pip install "python-multipart==0.0.22" "aiofiles==25.1.0"

# Data export
pip install "pandas>=2.0.0"

# Environment config
pip install "python-dotenv>=1.0.0"

# Dev / test dependencies
pip install -D pytest pytest-asyncio httpx
```

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `google-genai` (new SDK) | `google-generativeai` (legacy SDK) | **Never** — deprecated November 2025, no new features, critical bugs only; migrate immediately |
| Docling | pdfplumber + Tesseract + openpyxl (three separate libs) | Only if you need to avoid Docling's heavier AI model downloads (~1–2 GB for DocLayNet/TableFormer); Docling's unified output format is worth the install size for multi-format support |
| Docling (EasyOCR default) | Docling with `tesserocr` extra | Use `tesserocr` when deploying on low-memory servers or when documents are clean, high-DPI scans; EasyOCR is more accurate on noisy/distorted images but heavier |
| FastAPI `BackgroundTasks` | Celery + Redis | Only if you need persistence, retries, or distributed workers; explicitly out of scope for v1 per PROJECT.md |
| pandas for CSV | polars | Polars is 5–25x faster for large datasets but overkill here — extraction output is dozens to hundreds of rows per document, not millions; pandas has better ecosystem familiarity |
| Pydantic v2 as LLM schema | `instructor` library | `instructor` wraps the genai SDK and adds retry/validation loops; adds complexity; Gemini 2.5 Flash natively accepts Pydantic models in `response_schema` so the extra wrapper is unnecessary |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `google-generativeai` | Deprecated November 30, 2025; no Gemini 2.5 Flash feature support; development frozen to critical bug fixes only | `google-genai==1.68.0` |
| `langchain` for LLM abstraction | Adds heavy dependency tree (~50 transitive packages), abstracts away Gemini's native `response_schema`/structured output, and is unnecessary when you control the provider | Custom adapter pattern: one `LLMProvider` protocol with a `GoogleGeminiProvider` implementation |
| PyPDF2 | Unmaintained; no layout awareness; superseded by pypdf but Docling replaces both | `docling` |
| pdfplumber (standalone) | Does not handle images, XLSX, or OCR; you would need 3+ libs to match Docling's coverage | `docling` |
| pytesseract (standalone) | Requires system Tesseract binary; Docling manages OCR engine lifecycle internally via `tesserocr` optional extra | `docling[tesserocr]` |
| openpyxl (standalone) | Limited to cell-level XLSX reading; loses table structure context; Docling normalizes XLSX into the same `DoclingDocument` format as PDFs | `docling` |
| Celery | Distributed queue; requires Redis/RabbitMQ broker; explicitly excluded from v1 scope in PROJECT.md | FastAPI `BackgroundTasks` |

---

## Stack Patterns by Variant

**For the extraction pipeline (Docling → Gemini → CSV):**
- Convert document with `DocumentConverter` from `docling.document_converter`
- Export to markdown (`result.document.export_to_markdown()`) — this is the cleanest text representation for LLM prompt construction; preserves table structure and reading order better than plain text
- Pass markdown as the user-turn content to `client.models.generate_content()` with `response_schema=YourPydanticModel`
- Map validated Pydantic output directly to a `pandas.DataFrame` and call `.to_csv()`

**For FastAPI async file processing:**
- Accept `UploadFile` in the endpoint, read bytes immediately: `content = await file.read()`
- Pass a `job_id` back to the client instantly
- Add a `BackgroundTasks` function that receives the bytes (not the `UploadFile` object — the file handle closes after response)
- Store job state in a module-level `dict[str, JobState]` (sufficient for single-process v1)

**For scanned PDFs and images:**
- Docling auto-detects whether a PDF page is text-based or scanned
- For image files (PNG/JPG) passed directly, Docling routes them through OCR automatically
- Force full-page OCR mode (`PdfPipelineOptions(do_ocr=True)`) when Docling's auto-detection fails on borderline cases

**If deploying as Docker container (post-v1):**
- Use `python:3.12-slim` base image
- Docling's AI models (DocLayNet, TableFormer) are downloaded on first run; pre-download in Dockerfile to avoid cold-start delays
- `tesserocr` requires system `libtesseract-dev` — add `apt-get install libtesseract-dev` to Dockerfile

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| `docling==2.80.0` | Python >=3.10 | Requires Python 3.10+; PyTorch is a transitive dependency — expect ~1–2 GB install |
| `google-genai==1.68.0` | Python >=3.10, `pydantic>=2.0` | Accepts Pydantic v2 BaseModel directly in `response_schema`; does NOT work with Pydantic v1 |
| `fastapi==0.135.1` | `pydantic>=2.0`, `uvicorn>=0.12` | FastAPI 0.100+ requires Pydantic v2; v1 compatibility shim exists but adds overhead |
| `pydantic==2.12.5` | `fastapi>=0.100`, `google-genai>=1.0` | v2 API (`model_fields`, `model_validate`, `model_dump`) is not backward-compatible with v1 |
| `aiofiles==25.1.0` | Python >=3.8, `asyncio` | No known conflicts; use `asyncio` mode (`async with aiofiles.open(...)`) throughout |
| `pytest-asyncio==0.24.x` | `pytest>=8.0`, `asyncio` | Requires `asyncio_mode = "auto"` in `pytest.ini` or `pyproject.toml` to avoid per-test `@pytest.mark.asyncio` decoration |

---

## LLM Provider Abstraction Pattern

The PROJECT.md requires a pluggable LLM provider. The correct approach is a protocol (structural subtyping), not LangChain:

```python
# app/llm/base.py
from typing import Protocol, Type
from pydantic import BaseModel

class LLMProvider(Protocol):
    async def extract(
        self,
        text: str,
        schema: Type[BaseModel],
        system_prompt: str,
    ) -> BaseModel: ...

# app/llm/gemini.py
import google.genai as genai

class GoogleGeminiProvider:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def extract(self, text, schema, system_prompt):
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=text,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )
        return schema.model_validate_json(response.text)
```

This pattern satisfies the pluggability requirement without LangChain. Adding OpenAI or Anthropic means implementing one class with one `async def extract(...)` method.

---

## Sources

- [Docling PyPI — version 2.80.0, dependencies](https://pypi.org/project/docling/) — HIGH confidence
- [Docling Supported Formats — official docs](https://docling-project.github.io/docling/usage/supported_formats/) — HIGH confidence
- [google-genai PyPI — version 1.68.0](https://pypi.org/project/google-genai/) — HIGH confidence
- [Google Gen AI SDK official docs](https://googleapis.github.io/python-genai/) — HIGH confidence (structured output, async client, response_schema)
- [google-generativeai deprecated — official GitHub](https://github.com/google-gemini/deprecated-generative-ai-python) — HIGH confidence (deprecation confirmed November 2025)
- [FastAPI PyPI — version 0.135.1](https://pypi.org/project/fastapi/) — HIGH confidence
- [FastAPI BackgroundTasks official docs](https://fastapi.tiangolo.com/tutorial/background-tasks/) — HIGH confidence
- [Pydantic PyPI — version 2.12.5](https://pypi.org/project/pydantic/) — HIGH confidence
- [uvicorn PyPI — version 0.42.0](https://pypi.org/project/uvicorn/) — HIGH confidence
- [python-multipart PyPI — version 0.0.22](https://pypi.org/project/python-multipart/) — HIGH confidence
- [aiofiles PyPI — version 25.1.0](https://pypi.org/project/aiofiles/) — HIGH confidence
- [Gemini structured outputs — Google AI for Developers](https://ai.google.dev/gemini-api/docs/structured-output) — HIGH confidence (response_schema + Pydantic confirmed)
- [Docling OCR engine selection — force full page OCR example](https://docling-project.github.io/docling/examples/full_page_ocr/) — MEDIUM confidence (behavior verified in docs, runtime selection behavior from WebSearch)

---

*Stack research for: DocExtract — document data extraction system*
*Researched: 2026-03-18*
