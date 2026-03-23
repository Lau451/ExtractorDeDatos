# Phase 4: Full API Integration - Research

**Researched:** 2026-03-23
**Domain:** FastAPI PATCH endpoint, deep merge, asyncio background task, structured error codes
**Confidence:** HIGH

## Summary

Phase 4 completes the REST API surface by adding three capabilities: a `PATCH /jobs/{id}/fields` endpoint that deep-merges user corrections into `extraction_result`; a background asyncio task that periodically evicts expired jobs; and an expanded error-code vocabulary. All three work entirely within the existing in-memory `JobStore` and asyncio patterns already established in Phases 1–3.

The deep-merge algorithm is the only genuinely new piece of code. Every other component follows patterns already visible in `src/core/job_store.py` and `src/api/routes/`. The PATCH endpoint mirrors the error-handling style of `export.py` (404/409 guards), the cleanup task mirrors background coroutine patterns in asyncio, and the error codes extend the existing `set_error()` call sites without changing the storage model.

**Primary recommendation:** Implement `patch_extraction_result()` on `JobStore` using a recursive deep-merge function (dict/list/scalar), add a FastAPI `lifespan` context manager in `main.py` for the cleanup task, and define all five error codes as module-level constants in a new `src/core/errors.py`.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- User edits are merged **directly into `extraction_result`** (overwrite in place) — no separate `user_edits` field
- Merge is **deep** (recursive): nested dicts and list elements like `line_items` are merged field-by-field, not replaced wholesale
- Original extraction values are not preserved after a PATCH — each PATCH produces the new canonical state
- Endpoint: `PATCH /jobs/{id}/fields`
- Request body: flat field map `{"fields": {"field_name": "new_value"}}`
- Semantics: **full replacement** — the `fields` dict in the request is deep-merged into the current `extraction_result`; any fields not included in the request retain their current value
- On success: returns the **full updated `JobResponse`** (not 204) so the client can confirm applied edits immediately
- Error cases: 404 if job not found, 409 if job is not in `complete` state
- **Distinct error codes per root cause**: `DOCLING_TIMEOUT`, `DOCLING_PARSE_ERROR`, `GEMINI_ERROR`, `INVALID_FILE_TYPE`, `FILE_TOO_LARGE`
- `error_code` and `error_message` already exist on the `Job` dataclass — this phase expands the vocabulary, not the storage model
- **Background asyncio task** running periodically (not lazy/on-access)
- **TTL: 1 hour** from job creation
- Expired jobs are removed silently — subsequent requests return 404

### Claude's Discretion
- Deep merge algorithm implementation (handle dict, list, scalar)
- Cleanup task startup (lifespan context vs. startup event)
- Cleanup interval frequency
- Whether to validate field names against the known schema or accept any key

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| API-03 | API exposes a PATCH /jobs/{id}/fields endpoint that accepts user-corrected field values | PATCH route pattern from existing `export.py`; `patch_extraction_result()` on JobStore; `PatchFieldsRequest` Pydantic model |
| REV-05 | Edited values are reflected in the downloaded CSV (not the originally extracted values) | Export route already reads `job.extraction_result` directly — deep merge into that dict makes corrections automatically visible at export time; no changes to `export.py` required |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | already installed | PATCH route, request body parsing, dependency injection | Project standard |
| Pydantic v2 | already installed | `PatchFieldsRequest` model validation | Project standard |
| asyncio | stdlib | Background cleanup coroutine, `asyncio.Lock` | Project standard — all JobStore methods use it |
| Python `copy` (stdlib) | stdlib | Deep copy when needed during merge | No extra dependency |

### No New Dependencies
All required capabilities (HTTP routing, async tasks, data modeling) are already present in the project. No new packages need to be installed.

**Installation:**
```bash
# No new packages required
```

---

## Architecture Patterns

### Recommended Project Structure — New Files

```
src/
├── core/
│   ├── job_store.py      # ADD: patch_extraction_result(), cleanup_expired_jobs()
│   └── errors.py         # NEW: error code constants
└── api/
    ├── models.py         # ADD: PatchFieldsRequest model
    └── routes/
        └── patch.py      # NEW: PATCH /jobs/{id}/fields route (or extend jobs.py)
```

### Pattern 1: Deep Merge Algorithm

**What:** Recursive function that merges a `patch` dict into a `base` dict. Dicts recurse, lists are handled by index (merge element-by-element if both are lists of dicts), scalars overwrite.

**When to use:** Called inside `patch_extraction_result()` to produce the new canonical `extraction_result`.

**Design decision (Claude's discretion):** Lists are merged by index. When the patch contains `"line_items": [{"unit_price": "99.00"}]`, only index 0's `unit_price` is updated; other keys in index 0 and all other list elements are preserved. This is the safest approach for the existing CSV formatter which depends on stable list structure.

**Example:**
```python
# Source: project pattern — mirrors JobStore.set_extraction_result() signature
def _deep_merge(base: dict, patch: dict) -> dict:
    """Return base with patch applied recursively. Does not mutate either argument."""
    import copy
    result = copy.deepcopy(base)
    for key, patch_val in patch.items():
        base_val = result.get(key)
        if isinstance(base_val, dict) and isinstance(patch_val, dict):
            result[key] = _deep_merge(base_val, patch_val)
        elif isinstance(base_val, list) and isinstance(patch_val, list):
            merged_list = list(base_val)
            for i, patch_item in enumerate(patch_val):
                if i < len(merged_list) and isinstance(merged_list[i], dict) and isinstance(patch_item, dict):
                    merged_list[i] = _deep_merge(merged_list[i], patch_item)
                elif i < len(merged_list):
                    merged_list[i] = patch_item
                else:
                    merged_list.append(patch_item)
            result[key] = merged_list
        else:
            result[key] = patch_val
    return result
```

### Pattern 2: JobStore.patch_extraction_result()

**What:** New method on JobStore that acquires `_lock`, calls `_deep_merge`, writes back, and updates `updated_at`. Returns `True` on success, `False` if job not found.

**When to use:** Called by the PATCH route after 404/409 guards.

**Example:**
```python
# Source: mirrors JobStore.set_extraction_result() lock pattern
async def patch_extraction_result(self, job_id: str, patch: dict) -> bool:
    async with self._lock:
        job = self._store.get(job_id)
        if job is None:
            return False
        current = job.extraction_result or {}
        job.extraction_result = _deep_merge(current, patch)
        job.updated_at = datetime.utcnow()
        return True
```

### Pattern 3: PATCH Route

**What:** `PATCH /jobs/{id}/fields` route in `src/api/routes/patch.py` (or extending `jobs.py`). Follows the same 404/409 guard pattern as `export.py`.

**When to use:** This is the main API-03 deliverable.

**Example:**
```python
# Source: mirrors export.py guard pattern
@router.patch("/jobs/{job_id}/fields")
async def patch_job_fields(job_id: str, body: PatchFieldsRequest):
    job = await job_store.get(job_id)
    if job is None:
        return JSONResponse(status_code=404, content={"error": "job_not_found", ...})
    if job.status != "complete":
        return JSONResponse(status_code=409, content={"error": "job_not_patchable", ...})
    await job_store.patch_extraction_result(job_id, body.fields)
    job = await job_store.get(job_id)  # re-fetch for response
    return {
        "job_id": job.job_id,
        "status": job.status,
        "doc_type": job.doc_type,
        "extraction_result": _serialize_extraction(job.extraction_result),
    }
```

### Pattern 4: Background Cleanup Task via Lifespan

**What:** `asyncio.create_task()` called inside FastAPI's `lifespan` context manager, running a loop that sleeps N seconds then evicts jobs older than 1 hour.

**When to use:** Preferred over `@app.on_event("startup")` — FastAPI `on_event` is deprecated in favor of `lifespan` as of FastAPI 0.95+.

**Example:**
```python
# Source: FastAPI official docs — lifespan context manager
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime, timedelta

TTL = timedelta(hours=1)
CLEANUP_INTERVAL_SECONDS = 300  # 5 minutes

async def _cleanup_loop(store: JobStore) -> None:
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
        cutoff = datetime.utcnow() - TTL
        async with store._lock:
            expired = [jid for jid, job in store._store.items() if job.created_at < cutoff]
            for jid in expired:
                del store._store[jid]

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_cleanup_loop(job_store))
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(title="DocExtract", version="0.1.0", lifespan=lifespan)
```

### Pattern 5: Error Code Constants

**What:** Module-level string constants in `src/core/errors.py`. Call sites import and use constants instead of string literals.

**Example:**
```python
# src/core/errors.py
DOCLING_TIMEOUT = "DOCLING_TIMEOUT"
DOCLING_PARSE_ERROR = "DOCLING_PARSE_ERROR"
GEMINI_ERROR = "GEMINI_ERROR"
INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
FILE_TOO_LARGE = "FILE_TOO_LARGE"
```

### Anti-Patterns to Avoid

- **Using `@app.on_event("startup")`:** Deprecated in FastAPI 0.95+. Use `lifespan` context manager.
- **Calling `asyncio.create_task()` at module import time:** Tasks need a running event loop; create them inside `lifespan`.
- **Acquiring `_lock` from outside JobStore in the cleanup loop:** All lock acquisition must happen inside JobStore methods or a dedicated cleanup helper that receives the store. Accessing `store._lock` directly from the cleanup loop is acceptable since the loop is part of the same module.
- **Deep-merging by mutating `base` in place:** Creates race conditions if the lock is released between read and write. Always deep-copy first.
- **Returning 204 on successful PATCH:** The decision requires the full `JobResponse` so the client can confirm applied edits.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Request body parsing/validation | Manual JSON parsing | Pydantic `PatchFieldsRequest(BaseModel)` | Already used everywhere; handles type errors, missing fields, extra fields automatically |
| Background task lifecycle | `threading.Thread` or `subprocess` | `asyncio.create_task()` inside `lifespan` | Single event loop — threading adds unnecessary complexity and lock contention |
| Error serialization | Custom error dict builders | Reuse `JSONResponse(status_code=..., content={...})` pattern from `export.py` | Consistent error shape across all routes |

**Key insight:** This phase is nearly pure integration work — the deep merge function is the only novel algorithm; everything else wires existing patterns together.

---

## Common Pitfalls

### Pitfall 1: Re-fetching job after patch creates a TOCTOU window

**What goes wrong:** Route calls `job_store.get()` for the 404/409 guard, then calls `patch_extraction_result()`, then calls `get()` again to build the response. Between the second and third call, the job could theoretically be evicted by the cleanup task.

**Why it happens:** Each `get()` and `patch_extraction_result()` acquires and releases the lock separately.

**How to avoid:** `patch_extraction_result()` can return the updated `Job` object directly instead of a boolean, so the route builds the response from the returned object without a second `get()` call.

**Warning signs:** Intermittent 500 errors on PATCH when cleanup interval is very short.

### Pitfall 2: Deep merge mutates shared state prematurely

**What goes wrong:** If `_deep_merge` modifies `base` in place and an exception occurs mid-merge, `extraction_result` is left in a partial state.

**Why it happens:** Iterating and writing to the same dict.

**How to avoid:** `copy.deepcopy(base)` at the start of `_deep_merge` — build the full result, then assign atomically.

### Pitfall 3: Cleanup task silently crashes

**What goes wrong:** An unhandled exception inside `_cleanup_loop` terminates the coroutine; no further cleanup happens but no error is visible.

**Why it happens:** `asyncio.create_task()` swallows exceptions unless the task is awaited.

**How to avoid:** Wrap the loop body in `try/except Exception` and log the error, then continue the loop. Only `asyncio.CancelledError` should propagate.

### Pitfall 4: `_serialize_extraction()` in PATCH response applies "Not found" to patched values

**What goes wrong:** `jobs.py` has `_serialize_extraction()` that replaces `None` with `"Not found"`. If a user PATCHes a value to `None`, the response correctly shows "Not found" — but the stored value in `extraction_result` remains `None`. The CSV export formatter receives `None` and renders it as an empty cell.

**Why it happens:** The serialization layer is only for display; storage allows `None`.

**How to avoid:** This is correct behavior — document it. If the client PATCHes a field to `None`, the CSV cell will be empty. No code change needed; just awareness.

### Pitfall 5: lifespan replaces app-level router inclusion order

**What goes wrong:** `app = FastAPI(lifespan=lifespan)` must come before `app.include_router(...)` calls. The current `main.py` creates the app first then includes routers — adding `lifespan=` to the constructor call is a one-line change.

**Why it happens:** It's easy to forget the constructor parameter when refactoring.

**How to avoid:** Add `lifespan=lifespan` to the existing `FastAPI(...)` constructor call in `main.py`.

---

## Code Examples

Verified patterns from existing codebase:

### Existing error response shape (export.py)
```python
# Source: src/api/routes/export.py — use identical shape for PATCH errors
return JSONResponse(
    status_code=404,
    content={"error": "job_not_found", "message": f"No job with ID '{job_id}'"},
)
return JSONResponse(
    status_code=409,
    content={"error": "job_not_patchable", "message": f"Job is not complete (status: {job.status})"},
)
```

### JobStore method signature pattern
```python
# Source: src/core/job_store.py — all methods follow this pattern
async def set_extraction_result(self, job_id: str, result: dict) -> None:
    async with self._lock:
        job = self._store.get(job_id)
        if job:
            job.extraction_result = result
            job.status = "complete"
            job.updated_at = datetime.utcnow()
```

### JobResponse fields (models.py) — PATCH returns this shape
```python
# Source: src/api/models.py
class JobResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[JobResultPayload] = None
    doc_type: Optional[str] = None
    extraction_result: Optional[dict] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
```

### PatchFieldsRequest model (new)
```python
# New Pydantic model to add to src/api/models.py
class PatchFieldsRequest(BaseModel):
    fields: dict  # {"field_name": "new_value"} — flat or nested
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `@app.on_event("startup")` | `lifespan` context manager | FastAPI 0.95 (2023) | `on_event` still works but emits deprecation warning; `lifespan` is the current pattern |
| `asyncio.get_event_loop()` | `asyncio.get_running_loop()` or `asyncio.create_task()` | Python 3.10+ | Use `create_task()` from within an async context; never call `get_event_loop()` from sync code |

**Deprecated/outdated:**
- `@app.on_event("startup")` / `@app.on_event("shutdown")`: Still functional but deprecated. Use `lifespan` instead.

---

## Open Questions

1. **Should PATCH validate field names against the known schema?**
   - What we know: The existing extraction schemas (Pydantic models in `src/extraction/schemas/`) define which fields are valid per doc type. The `extraction_result` is stored as `dict` from `.model_dump()`.
   - What's unclear: Accepting unknown keys is permissive but risks silently writing keys the CSV formatter ignores. Rejecting unknown keys requires loading the schema per doc_type.
   - Recommendation (Claude's discretion): Accept any key for v1 simplicity. Unknown keys are ignored by the CSV formatter so they cause no harm. Document this behavior.

2. **Cleanup interval: 5 minutes vs. shorter?**
   - What we know: TTL is 1 hour; interval is discretionary. 5 minutes means a job lives at most 65 minutes.
   - Recommendation: 5 minutes is appropriate. Lower intervals (e.g., 30 seconds) waste CPU; higher intervals (e.g., 30 minutes) mean memory usage is less predictable.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio (asyncio_mode = "auto") |
| Config file | `pyproject.toml` — `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/test_patch.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| API-03 | PATCH /jobs/{id}/fields returns 200 with updated JobResponse | integration | `pytest tests/test_patch.py::test_patch_updates_field -x` | Wave 0 |
| API-03 | PATCH returns 404 for unknown job ID | integration | `pytest tests/test_patch.py::test_patch_404 -x` | Wave 0 |
| API-03 | PATCH returns 409 when job not complete | integration | `pytest tests/test_patch.py::test_patch_409_not_complete -x` | Wave 0 |
| API-03 | Deep merge preserves fields not in patch | unit | `pytest tests/test_patch.py::test_deep_merge_preserves_untouched_fields -x` | Wave 0 |
| API-03 | Deep merge updates nested dicts | unit | `pytest tests/test_patch.py::test_deep_merge_nested_dict -x` | Wave 0 |
| API-03 | Deep merge updates list elements by index | unit | `pytest tests/test_patch.py::test_deep_merge_list_by_index -x` | Wave 0 |
| REV-05 | After PATCH, GET /jobs/{id}/export CSV reflects edited values | integration | `pytest tests/test_patch.py::test_patch_then_export_reflects_edits -x` | Wave 0 |
| TTL (implicit) | Jobs older than TTL are removed; subsequent GET returns 404 | unit | `pytest tests/test_patch.py::test_cleanup_removes_expired_jobs -x` | Wave 0 |
| Error codes | set_error() called with defined error code constants | unit | `pytest tests/test_patch.py::test_error_codes_defined -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_patch.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_patch.py` — all API-03 and REV-05 tests listed above
- [ ] No framework changes needed — `asyncio_mode = "auto"` in `pyproject.toml` already handles async tests

*(All other test infrastructure is in place: `conftest.py` with `client` fixture and `clear_job_store` autouse fixture)*

---

## Sources

### Primary (HIGH confidence)
- Direct codebase read: `src/core/job_store.py`, `src/api/models.py`, `src/api/routes/jobs.py`, `src/api/routes/export.py`, `src/main.py` — full implementation context
- Direct codebase read: `tests/conftest.py`, `tests/test_export.py` — test patterns and existing infrastructure
- `.planning/phases/04-full-api-integration/04-CONTEXT.md` — locked decisions
- `pyproject.toml` — pytest configuration confirmed

### Secondary (MEDIUM confidence)
- FastAPI lifespan documentation pattern — `@asynccontextmanager` with `asyncio.create_task()` is the documented replacement for `on_event`; verified against known FastAPI behavior as of 0.95+ (August 2023)

### Tertiary (LOW confidence)
None — all findings grounded in codebase or widely-documented FastAPI patterns.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new packages; all patterns verified in existing codebase
- Architecture: HIGH — PATCH route and cleanup task follow directly from existing patterns in `export.py` and stdlib asyncio
- Pitfalls: HIGH — TOCTOU and deep-copy pitfalls are standard concurrency issues; cleanup crash pitfall is well-known asyncio behavior

**Research date:** 2026-03-23
**Valid until:** 2026-04-23 (stable domain — FastAPI and Python asyncio patterns are stable)
