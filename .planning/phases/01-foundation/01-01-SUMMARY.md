---
phase: 01-foundation
plan: 01
subsystem: api
tags: [fastapi, uvicorn, pydantic, docling, asyncio, job-store]

# Dependency graph
requires: []
provides:
  - FastAPI app factory at src/main.py with health router registered
  - Thread-safe in-memory JobStore with asyncio.Lock (pending -> processing -> complete | error)
  - Pydantic v2 response schemas: ExtractResponse, JobResponse, JobResultPayload, ErrorResponse, HealthResponse
  - Application settings via pydantic-settings backed by .env
  - GET /health endpoint returning {"status": "healthy"}
  - All production and dev dependencies installed (fastapi, uvicorn, docling, pytest, httpx)
affects:
  - 01-02 (ingestion pipeline uses job_store singleton and models)
  - Phase 2 (LLM extraction reads job.raw_text from job store)
  - Phase 5 (React SPA polls GET /health and GET /jobs/{id})

# Tech tracking
tech-stack:
  added:
    - fastapi==0.135.1
    - uvicorn==0.42.0
    - pydantic==2.12.5
    - pydantic-settings>=2.0 (resolved to 2.13.1)
    - python-multipart==0.0.22
    - docling==2.80.0
    - python-dotenv==1.2.2
    - pytest==9.0.2
    - pytest-asyncio==1.3.0
    - httpx==0.28.1
  patterns:
    - Module-level singleton for JobStore (job_store = JobStore())
    - pydantic-settings BaseSettings with env_file .env for config injection
    - Dataclass with field(default_factory=datetime.utcnow) for Job timestamps
    - asyncio.Lock as single lock protecting the entire in-memory dict

key-files:
  created:
    - requirements.txt
    - requirements-dev.txt
    - pyproject.toml
    - .env.example
    - src/__init__.py
    - src/api/__init__.py
    - src/api/routes/__init__.py
    - src/core/__init__.py
    - src/ingestion/__init__.py
    - src/core/config.py
    - src/core/job_store.py
    - src/api/models.py
    - src/api/routes/health.py
    - src/main.py
  modified:
    - .gitignore (added Python patterns)

key-decisions:
  - "asyncio.Lock is the single lock for entire in-memory dict - simple and correct for single-process v1"
  - "Module-level job_store singleton avoids dependency injection complexity in v1"
  - "pydantic-settings BaseSettings with env_file .env - standard config pattern"
  - "JobResultPayload as a nested model in JobResponse - preserves extensibility for Phase 2"

patterns-established:
  - "Pattern 1: Job lifecycle - create() sets pending; set_status() transitions; set_complete()/set_error() are terminal setters"
  - "Pattern 2: All JobStore methods acquire self._lock before any mutation"
  - "Pattern 3: FastAPI router defined in module, imported and registered in src/main.py via app.include_router()"

requirements-completed: [API-05]

# Metrics
duration: 5min
completed: 2026-03-19
---

# Phase 01 Plan 01: Project Scaffold and Core Infrastructure Summary

**FastAPI server with asyncio.Lock job store, pydantic-settings config, full response schema set, and GET /health endpoint — all dependencies installed including docling 2.80.0**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-19T01:16:37Z
- **Completed:** 2026-03-19T01:21:48Z
- **Tasks:** 2
- **Files modified:** 15 (14 created + 1 modified)

## Accomplishments

- Complete project scaffold with all production and dev dependencies installed (fastapi, uvicorn, docling, pytest, httpx)
- Thread-safe in-memory JobStore with asyncio.Lock supporting full job lifecycle (pending -> processing -> complete | error)
- FastAPI app factory with GET /health registered and returning {"status": "healthy"}
- All Pydantic v2 response schemas importable: ExtractResponse, JobResponse, ErrorResponse, HealthResponse

## Task Commits

Each task was committed atomically:

1. **Task 1: Create project scaffold and install dependencies** - `05d0f13` (chore)
2. **Task 2: Build core infrastructure** - `9758359` (feat)
3. **Deviation: Add Python gitignore patterns** - `4dfef22` (chore)

## Files Created/Modified

- `requirements.txt` - Production dependencies pinned to exact versions
- `requirements-dev.txt` - Dev/test dependencies extending requirements.txt
- `pyproject.toml` - pytest config with asyncio_mode = "auto"
- `.env.example` - Environment variable template for all settings
- `src/__init__.py` - Package stub
- `src/api/__init__.py` - Package stub
- `src/api/routes/__init__.py` - Package stub
- `src/core/__init__.py` - Package stub
- `src/ingestion/__init__.py` - Package stub
- `src/core/config.py` - Settings class backed by pydantic-settings + .env
- `src/core/job_store.py` - Job dataclass + JobStore with asyncio.Lock + module singleton
- `src/api/models.py` - ExtractResponse, JobResponse, JobResultPayload, ErrorResponse, HealthResponse
- `src/api/routes/health.py` - GET /health endpoint
- `src/main.py` - FastAPI app factory with health router; uvicorn entry point
- `.gitignore` - Added __pycache__, .pyc, .env, venv, dist, build patterns

## Decisions Made

- Used module-level `job_store = JobStore()` singleton to avoid dependency injection complexity in v1
- JobResultPayload as a nested model inside JobResponse preserves schema extensibility for Phase 2 (LLM extraction may add fields)
- asyncio.Lock as a single coarse-grained lock for the full dict — simple and correct for single-process v1 deployment

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added Python .gitignore patterns**
- **Found during:** Task 2 (after core infrastructure committed)
- **Issue:** __pycache__ directories appeared as untracked files; no .gitignore patterns for Python generated files
- **Fix:** Added __pycache__, *.py[cod], *.pyo, .env, .venv/, venv/, *.egg-info/, dist/, build/ to .gitignore
- **Files modified:** .gitignore
- **Verification:** git status shows __pycache__ no longer tracked
- **Committed in:** 4dfef22

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** .gitignore fix prevents generated files from polluting version control. No scope creep.

## Issues Encountered

None — all imports succeeded on first attempt, pip install completed without errors.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Job store singleton ready to import in plan 01-02 (ingestion pipeline)
- Pydantic response models ready for use in extract and jobs route handlers
- GET /health available for smoke tests in plan 01-02
- Plan 01-02 will implement: POST /extract, GET /jobs/{id}, IngestionService, DoclingAdapter

---
*Phase: 01-foundation*
*Completed: 2026-03-19*

## Self-Check: PASSED

All 15 files exist on disk. All 3 commits (05d0f13, 9758359, 4dfef22) found in git log.
