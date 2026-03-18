# Technology Stack

**Analysis Date:** 2026-03-18

## Languages

**Primary:**
- Python 3.10+ - Backend and document processing pipeline
- JavaScript/TypeScript - Tooling and automation (GSD framework hooks)

**Secondary:**
- Bash - Build and deployment scripts
- JSON - Configuration

## Runtime

**Environment:**
- Python 3.10+ (target runtime for main application)
- Node.js (for GSD orchestration framework only, not production code)

**Package Manager:**
- pip (Python dependency management)
- npm (Node.js dependencies for development tooling)
- Lockfile: Not yet created (project in initialization phase)

## Frameworks

**Core:**
- FastAPI 0.104+ - REST API framework for async document processing service (Phase 4)
- Pydantic 2.0+ - Data validation and configuration management (Phase 2)

**Document Processing:**
- PyPDF2 or pdfplumber - PDF text extraction from text-based PDFs (Phase 1)
- Tesseract OCR / pytesseract - Optical character recognition for scanned PDFs and images (Phase 1)
- openpyxl - Excel file reading and cell value extraction (Phase 1)
- Pillow (PIL) - Image processing for PNG and image file handling (Phase 1)

**LLM Integration:**
- openai (GPT) - OpenAI API client for LLM extraction (Phase 2)
- anthropic (Claude) - Anthropic API client for Claude integration (Phase 2, pluggable)
- google-generativeai (Gemini) - Google Generative AI client for Gemini integration (Phase 2, pluggable)

**CSV & Data Export:**
- pandas - DataFrames and CSV generation for output formats (Phase 3)

**Testing & Development:**
- pytest 7.0+ - Unit and integration testing framework
- pytest-asyncio - Async test support for FastAPI endpoints
- unittest (standard library) - Fallback testing support

## Key Dependencies

**Critical:**
- FastAPI - Enables async REST API for job queuing and extraction pipeline (Phase 4 blocker)
- Pydantic - Ensures data validation across extraction fields, document types, and configuration (Phase 2-3)
- pytesseract / Tesseract - Required for OCR on scanned documents and images (Phase 1 blocker)

**Infrastructure:**
- python-multipart - FastAPI file upload support (Phase 4)
- uvicorn 0.24+ - ASGI server for FastAPI application (Phase 4)
- aiofiles - Async file I/O for non-blocking file operations (Phase 4)
- python-dotenv - Environment variable loading from .env files (All phases)

**Document Processing Chain:**
- pdfplumber - Preferred PDF text extraction (superior to PyPDF2, Phase 1)
- openpyxl - Excel cell-level reading (Phase 1)
- Pillow - Image format support and preprocessing for OCR (Phase 1)

**LLM Abstraction:**
- langchain or custom adapter pattern - Pluggable LLM provider abstraction (Phase 2)

## Configuration

**Environment:**
- .env file (not committed) - Runtime configuration for API keys, LLM provider selection, OCR settings
- config.json (optional) - Application configuration for field extraction prompts and document type definitions
- Environment variables for:
  - `LLM_PROVIDER` - One of: "openai", "anthropic", "google"
  - `OPENAI_API_KEY` - OpenAI API credentials (if using GPT)
  - `ANTHROPIC_API_KEY` - Anthropic API credentials (if using Claude)
  - `GOOGLE_API_KEY` - Google API credentials (if using Gemini)
  - `TESSERACT_PATH` - System path to Tesseract OCR binary (Windows: C:\Program Files\Tesseract-OCR, Linux: /usr/bin/tesseract)
  - `API_HOST` - FastAPI server host (default: 0.0.0.0)
  - `API_PORT` - FastAPI server port (default: 8000)

**Build:**
- requirements.txt - Python dependencies and pinned versions
- Optional: pyproject.toml for modern Python packaging (if using Poetry/Setuptools)

## Platform Requirements

**Development:**
- Python 3.10+ with pip
- Tesseract OCR engine (system binary, not Python package)
  - Windows: Download installer from GitHub/UB-Mannheim/tesseract
  - Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
  - macOS: `brew install tesseract`
- Git for version control
- Text editor or IDE (VS Code, PyCharm, etc.)

**Production:**
- Python 3.10+ runtime
- Tesseract OCR engine installed on server
- FastAPI-compatible ASGI server (uvicorn for development, gunicorn+uvicorn for production)
- Cloud deployment target: Docker container (not yet defined in roadmap, likely Phase 5+)
  - Dockerfile to be created during Phase 4 implementation

## Async & Job Processing

**Model:**
- FastAPI async request handlers for immediate job ID return (Phase 4)
- Background task execution for long-running extraction (Phase 4)
- Optional: Redis or in-memory job queue for future scaling

**Future Considerations:**
- Celery for distributed task processing (post-v1)
- PostgreSQL for persistent job tracking (post-v1)
- Currently: In-memory job storage acceptable for v1

---

*Stack analysis: 2026-03-18*
*Status: Pre-implementation (Phase 1 planning)*
*Last updated: Initial technology selection based on v1 requirements and 4-phase roadmap*
