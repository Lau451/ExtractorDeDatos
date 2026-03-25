# Phase 7: CSV Export Rules Enforcement - Research

**Researched:** 2026-03-24
**Domain:** Python CSV post-processing, FastAPI response headers, React fetch API
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Value normalization:**
- Numeric amount fields — Strip currency symbols and thousand separators so cells contain pure numbers. E.g., `"$1,234.50"` → `"1234.50"`. If stripping produces a value that cannot be parsed as a number, keep the original value unchanged.
- Date fields — Normalize extracted date strings to DD/MM/YYYY format. If parsing fails, keep the original value unchanged.
- None → "Not found" — Fields that were not extracted (None/null) export as the string `"Not found"` instead of a blank cell.
- Text whitespace — All text cells have leading/trailing whitespace stripped and internal multi-spaces compressed to a single space.
- Currency field — Drop currency symbols entirely from amount cells. The dedicated `currency` / `currency_code` field already carries the currency.
- Field type detection — Determined by field-name patterns, not explicit config per field:
  - Amount fields: names containing `amount`, `price`, `total`, `subtotal`, `tax`
  - Date fields: names containing `date` or ending with `_at`
  - All other fields: text normalization only (whitespace stripping)

**Mandatory field enforcement:**
- Warn but allow download. Export returns HTTP 200. If any mandatory fields are empty/"Not found", include `X-Export-Warnings` response header (comma-separated missing field names).
- Frontend: after "Download CSV" click, if `X-Export-Warnings` present in response, show warning toast/banner listing missing fields.
- No pre-flight check endpoint.
- `MANDATORY_FIELDS` dict in `src/export/` co-located with formatters.

**Download filename convention:**
- Format: `{doc_type}_{export_date}.csv` where `{export_date}` is today's date in `YYYY-MM-DD`.
- Examples: `purchase_order_2026-03-24.csv`, `tender_rfq_2026-03-24.csv`
- Underscores only (no hyphens).
- Set via `Content-Disposition` header in export endpoint.

### Claude's Discretion
- Exact list of mandatory fields per doc type (user approved: key identity fields — document number, issuer, date)
- Whether normalization lives as a standalone `normalize_cell(field_name, value)` function or is inlined into each formatter
- Test fixture strategy for normalization edge cases

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

## Summary

Phase 7 tightens the CSV export layer by adding three capabilities: value normalization (amount/date/text), mandatory field warnings, and descriptive filenames. All work occurs in two existing files: `src/export/formatters.py` (normalization logic and `MANDATORY_FIELDS` config) and `src/api/routes/export.py` (headers). The frontend `handleDownloadCSV` in `App.tsx` must change from `window.open(url, '_blank')` to a `fetch()` call so headers can be inspected for `X-Export-Warnings`.

The codebase is a clean Python/FastAPI backend with a React/TypeScript frontend. All schema fields are `Optional[str]` — no native numeric types — which means normalization must parse strings throughout. The existing `_format_line_item_type` and `_format_header_only_type` helpers are the correct insertion points for normalization. No new dependencies are required.

**Primary recommendation:** Implement normalization as a standalone `normalize_cell(field_name: str, value) -> str` function in `src/export/formatters.py`, called from both `_format_line_item_type` and `_format_header_only_type` to replace the inline `(None → "")` logic. This is the minimal-change, maximally-testable approach.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python `csv` (stdlib) | 3.11+ | CSV writing | Already in use — no new dependency |
| Python `re` (stdlib) | 3.11+ | Regex for currency/whitespace stripping | Already available |
| Python `datetime` (stdlib) | 3.11+ | Date parsing/formatting | Available; no third-party needed |
| FastAPI `Response` | 0.115+ | Setting response headers | Already used in export.py |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `dateutil.parser` (python-dateutil) | 2.9+ | Fuzzy date parsing | Useful if stdlib `datetime.strptime` patterns are too rigid |

**Installation:** No new packages required. `python-dateutil` is likely already installed as a transitive dependency (very common), but can be verified. Using stdlib `datetime` with multiple `strptime` format attempts is sufficient and adds zero dependencies.

**Version verification:** Not applicable — no new packages introduced.

---

## Architecture Patterns

### Where Changes Live

```
src/
└── export/
    ├── formatters.py       # normalize_cell(), MANDATORY_FIELDS, updated helpers
    └── (no new modules needed unless size warrants splitting)

src/api/routes/
└── export.py              # Content-Disposition filename, X-Export-Warnings header

frontend/src/
└── App.tsx                # handleDownloadCSV: fetch() instead of window.open()
```

### Pattern 1: Standalone normalize_cell function

**What:** A single function `normalize_cell(field_name: str, value) -> str` that dispatches to the appropriate normalization path based on field name patterns.

**When to use:** Called from both `_format_line_item_type` and `_format_header_only_type` to replace the existing `("" if v is None else v)` inline expression.

**Example:**
```python
import re
from datetime import datetime

_AMOUNT_KEYWORDS = ("amount", "price", "total", "subtotal", "tax")
_DATE_KEYWORDS = ("date",)
_DATE_SUFFIXES = ("_at",)

def _is_amount_field(name: str) -> bool:
    return any(kw in name for kw in _AMOUNT_KEYWORDS)

def _is_date_field(name: str) -> bool:
    return any(kw in name for kw in _DATE_KEYWORDS) or any(
        name.endswith(s) for s in _DATE_SUFFIXES
    )

# Ordered from most-specific to least; add formats as needed
_DATE_FORMATS = [
    "%d/%m/%Y", "%d-%m-%Y",
    "%Y-%m-%d", "%Y/%m/%d",
    "%d %B %Y", "%d %b %Y",
    "%B %d, %Y", "%b %d, %Y",
]

def _normalize_amount(value: str) -> str:
    """Strip currency symbols and thousand separators; keep original if result is non-numeric."""
    # Remove currency symbols and whitespace around them
    cleaned = re.sub(r"[^\d.,-]", "", value).replace(",", "")
    # Validate it parses as float
    try:
        float(cleaned)
        return cleaned
    except ValueError:
        return value  # keep original

def _normalize_date(value: str) -> str:
    """Parse and reformat to DD/MM/YYYY; keep original if parsing fails."""
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    return value  # keep original

def _normalize_text(value: str) -> str:
    """Strip leading/trailing whitespace; compress internal multi-spaces."""
    return re.sub(r" +", " ", value.strip())

def normalize_cell(field_name: str, value) -> str:
    """Normalize a single cell value for CSV export."""
    if value is None:
        return "Not found"
    s = str(value)
    if not s.strip():
        return "Not found"
    if _is_amount_field(field_name):
        return _normalize_amount(s)
    if _is_date_field(field_name):
        return _normalize_date(s)
    return _normalize_text(s)
```

### Pattern 2: Updated _format_line_item_type

**What:** Replace the existing `[("" if v is None else v) for v in row]` with `normalize_cell` calls.

**Example:**
```python
# Before (Phase 3)
clean_rows = [
    [("" if v is None else v) for v in row]
    for row in raw_rows
]

# After (Phase 7)
# header_fields and item_fields are column name lists
all_fields = header_fields + item_fields
clean_rows = [
    [normalize_cell(all_fields[i], v) for i, v in enumerate(row)]
    for row in raw_rows
]
```

### Pattern 3: MANDATORY_FIELDS config

**What:** A module-level dict mapping doc_type → list of required field names.

**Example:**
```python
MANDATORY_FIELDS: dict[str, list[str]] = {
    "purchase_order": ["po_number", "issue_date", "buyer_name", "supplier_name"],
    "tender_rfq": ["tender_reference", "issue_date", "issuing_organization"],
    "quotation": ["quote_number", "quote_date", "vendor_name"],
    "invoice": ["invoice_number", "invoice_date", "issuer_name"],
    "supplier_comparison": ["project_name", "comparison_date", "rfq_reference"],
}
```

**Derivation rationale:**
- `purchase_order`: `po_number` (document ID), `issue_date` (date), `buyer_name`, `supplier_name` (parties)
- `tender_rfq`: `tender_reference` (document ID), `issue_date` (date), `issuing_organization` (issuer)
- `quotation`: `quote_number` (document ID), `quote_date` (date), `vendor_name` (issuer)
- `invoice`: `invoice_number` (document ID), `invoice_date` (date), `issuer_name` (issuer)
- `supplier_comparison`: `project_name` (identity), `comparison_date` (date), `rfq_reference` (link to source)

### Pattern 4: Export endpoint with headers

**What:** Check mandatory fields after formatting, compute filename with today's date, attach both headers.

**Example:**
```python
from datetime import date

async def export_job(job_id: str):
    # ... existing guards ...
    formatter = FORMATTER_REGISTRY[job.doc_type]
    csv_bytes = formatter(job.extraction_result)

    # Descriptive filename
    today = date.today().strftime("%Y-%m-%d")
    filename = f"{job.doc_type}_{today}.csv"

    # Mandatory field check — inspect normalized extraction_result
    warnings = _check_mandatory_fields(job.doc_type, job.extraction_result)
    response_headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
    }
    if warnings:
        response_headers["X-Export-Warnings"] = ",".join(warnings)

    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers=response_headers,
    )
```

### Pattern 5: Mandatory field check helper

**What:** A `_check_mandatory_fields(doc_type, extraction_result)` function that checks the raw extraction_result dict (before normalization) for missing/None fields.

**Example:**
```python
def _check_mandatory_fields(doc_type: str, extraction_result: dict) -> list[str]:
    """Return list of mandatory field names that are missing or None."""
    required = MANDATORY_FIELDS.get(doc_type, [])
    missing = []
    for field in required:
        val = extraction_result.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            missing.append(field)
    return missing
```

### Pattern 6: Frontend fetch-based download with header inspection

**What:** Replace `window.open(url, '_blank')` with a `fetch()` call that inspects `X-Export-Warnings` header and triggers a programmatic download.

**Example:**
```typescript
const handleDownloadCSV = async (currentJobId: string, currentJobData: JobResponse) => {
    const res = await fetch(api.exportUrl(currentJobId));
    const warnings = res.headers.get('X-Export-Warnings');
    if (warnings) {
        // Surface warning banner/toast with missing fields
        setExportWarnings(warnings.split(',').map(w => w.trim()));
    }
    // Programmatic download
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `export_${currentJobId}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    setPhase({ tag: 'done', jobId: currentJobId, jobData: currentJobData });
};
```

### Anti-Patterns to Avoid

- **Inline normalization per doc type:** Repeating the normalize logic in each of the five formatters creates divergence risk. A single `normalize_cell()` called from the two shared helpers avoids this.
- **Modifying `_make_csv_bytes`:** That helper takes generic lists — normalization should happen before it, in the helpers that build rows.
- **Pre-flight endpoint for mandatory fields:** The CONTEXT.md decision is to use a response header. No separate endpoint.
- **window.open for download with header inspection:** `window.open` gives no access to response headers. Must use `fetch()`.
- **Checking mandatory fields after normalization:** Check the raw dict (None vs. not-None), not the normalized output — avoids confusion when normalization returns "Not found" for a non-mandatory field.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Currency symbol stripping | Custom character allowlist | `re.sub(r"[^\d.,-]", "", value)` | Handles all Unicode currency symbols in one pattern |
| Date parsing | Single `strptime` format | Multiple format loop over `_DATE_FORMATS` | LLM output uses wildly varied date formats |
| Blob download trigger | DOM manipulation variations | Standard `URL.createObjectURL` + anchor click | Cross-browser, no library needed |

**Key insight:** All normalization is string manipulation — no new libraries are needed.

---

## Common Pitfalls

### Pitfall 1: `submission_deadline` and `valid_until` not matched by date patterns

**What goes wrong:** The field `submission_deadline` (tender_rfq) and `valid_until` (quotation) contain date values but their names don't match `*date*` or `*_at`. They receive text normalization only (whitespace strip), not date normalization.

**Why it happens:** The decision says date fields are those with `date` in the name or ending with `_at`. Neither `submission_deadline` nor `valid_until` matches.

**How to avoid:** This is intentional per the locked decisions — don't add special cases. Document this in code comments so future maintainers don't try to "fix" it.

**Warning signs:** Test assertions comparing `submission_deadline` output format will show the original format unchanged — that is correct behavior.

### Pitfall 2: `X-Expose-Headers` CORS header required for browser fetch to read custom headers

**What goes wrong:** When the React frontend calls `fetch()` and attempts `res.headers.get('X-Export-Warnings')`, the browser blocks reading custom headers unless the server's CORS response includes `Access-Control-Expose-Headers: X-Export-Warnings`.

**Why it happens:** By default, CORS only exposes a small set of "safe" response headers (Content-Type, Content-Length, etc.). Custom headers like `X-Export-Warnings` are blocked by the browser unless explicitly exposed.

**How to avoid:** Add `expose_headers=["X-Export-Warnings"]` to the FastAPI CORS middleware config. Check `src/main.py` for where `CORSMiddleware` is configured.

**Warning signs:** `res.headers.get('X-Export-Warnings')` returns `null` in the browser even when the server sets the header — visible in browser DevTools Network tab where the header appears on the server response but not in JS.

### Pitfall 3: Amount normalization over-eagerness with mixed-content strings

**What goes wrong:** A value like `"USD 1,234"` — after stripping non-numeric characters — becomes `"1234"` but so does `"Ref-1234"` → `"1234"`. The amount regex must be applied only to fields identified as amount fields.

**Why it happens:** The pattern `re.sub(r"[^\d.,-]", "", value)` strips all non-numeric characters indiscriminately.

**How to avoid:** Only apply `_normalize_amount` when `_is_amount_field(field_name)` is True. The field-name pattern guard (`amount`, `price`, `total`, `subtotal`, `tax`) prevents this from running on text fields. This is already enforced by `normalize_cell`'s dispatch logic.

**Warning signs:** Fields like `po_reference` or `shipping_address` containing numbers lose their non-numeric characters.

### Pitfall 4: Empty string vs. None — both should become "Not found"

**What goes wrong:** After Phase 4's PATCH endpoint, some fields may be `""` (empty string) rather than `None` if the user cleared a field value. `normalize_cell` checking only `if value is None` misses this case.

**Why it happens:** PATCH deep merge can set fields to `""`.

**How to avoid:** In `normalize_cell`, check both `None` and empty-after-strip: `if value is None or not str(value).strip(): return "Not found"`.

### Pitfall 5: Existing test `test_none_values_are_empty_cells` will FAIL after Phase 7

**What goes wrong:** The existing test `tests/test_export.py::test_none_values_are_empty_cells` asserts that `notes=None` renders as `""` (empty string). Phase 7 changes this to `"Not found"`. That test will fail.

**Why it happens:** Phase 3 established `None → ""`. Phase 7 overrides to `None → "Not found"`.

**How to avoid:** Update that test (and the test data/fixtures in `SAMPLE_*` dicts that have `None` values) during Phase 7 implementation.

### Pitfall 6: window.open replaced by fetch — need to handle async download in App.tsx

**What goes wrong:** The current `handleDownloadCSV` is synchronous. The new version using `fetch()` must be async, and the function signature and call site must be updated.

**Why it happens:** `fetch()` is Promise-based.

**How to avoid:** Make `handleDownloadCSV` an `async` function. Update the `onClick` handler: `onClick={() => { void handleDownloadCSV(phase.jobId, jobData); }}` to avoid unhandled promise warnings.

---

## Code Examples

### Verified normalization patterns

```python
# Amount normalization — strips $, €, £, commas; validates numeric
import re

def _normalize_amount(value: str) -> str:
    cleaned = re.sub(r"[^\d.,-]", "", value).replace(",", "")
    try:
        float(cleaned)
        return cleaned
    except ValueError:
        return value

# Tests:
# "$1,234.50" → "1234.50"
# "€ 5.000,00" → with EU comma-as-decimal this may need refinement (see Open Questions)
# "N/A" → "N/A" (kept, float() fails)
```

```python
# Date normalization — try multiple formats, reformat to DD/MM/YYYY
from datetime import datetime

_DATE_FORMATS = [
    "%d/%m/%Y", "%d-%m-%Y",
    "%Y-%m-%d", "%Y/%m/%d",
    "%d %B %Y", "%d %b %Y",
    "%B %d, %Y", "%b %d, %Y",
    "%m/%d/%Y",  # US format last — ambiguous
]

def _normalize_date(value: str) -> str:
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    return value
```

```python
# Text whitespace normalization
import re

def _normalize_text(value: str) -> str:
    return re.sub(r" +", " ", value.strip())
```

### CORS expose headers (FastAPI)

```python
# In src/main.py — add expose_headers to existing CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Export-Warnings"],  # Required for browser fetch to read this header
)
```

---

## Current Codebase State (What Exists and What Changes)

### Files to modify

| File | Current state | Change required |
|------|--------------|-----------------|
| `src/export/formatters.py` | `None → ""` in both helpers | Add `normalize_cell()`, `MANDATORY_FIELDS`, update both helpers |
| `src/api/routes/export.py` | Filename = `job_{job_id}_{doc_type}.csv`; no warnings | Filename = `{doc_type}_{date}.csv`; add `X-Export-Warnings` header logic |
| `src/main.py` | CORSMiddleware config (unknown) | Add `expose_headers=["X-Export-Warnings"]` |
| `frontend/src/App.tsx` | `handleDownloadCSV` uses `window.open` | Change to `fetch()`, inspect headers, show warning |
| `tests/test_export.py` | `test_none_values_are_empty_cells` asserts `""` | Update to assert `"Not found"` |

### Files NOT to modify

- All five schema files in `src/extraction/schemas/` — field names are the source of truth for type detection; no changes needed
- `src/export/formatters.py`'s `_make_csv_bytes` helper — normalization inserts before it, not inside it
- Frontend components (ReviewTable, LineItemsTable, etc.) — only App.tsx download handler changes

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (asyncio_mode=auto, pyproject.toml) |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `pytest tests/test_export.py -x -q` |
| Full suite command | `pytest tests/ -q` |

Frontend:
| Property | Value |
|----------|-------|
| Framework | Vitest + jsdom (vite.config.ts) |
| Config file | `frontend/vite.config.ts` |
| Quick run command | `cd frontend && npx vitest run --reporter=verbose` |

### Phase Requirements → Test Map

| Behavior | Test Type | Automated Command | File Exists? |
|----------|-----------|-------------------|-------------|
| `normalize_cell` None → "Not found" | unit | `pytest tests/test_export.py::test_normalize_none_is_not_found -x` | Wave 0 |
| Amount field normalization ("$1,234.50" → "1234.50") | unit | `pytest tests/test_export.py::test_normalize_amount_fields -x` | Wave 0 |
| Date field normalization to DD/MM/YYYY | unit | `pytest tests/test_export.py::test_normalize_date_fields -x` | Wave 0 |
| Unparseable amount kept as-is | unit | `pytest tests/test_export.py::test_normalize_amount_fallback -x` | Wave 0 |
| Unparseable date kept as-is | unit | `pytest tests/test_export.py::test_normalize_date_fallback -x` | Wave 0 |
| Text whitespace stripped | unit | `pytest tests/test_export.py::test_normalize_text_whitespace -x` | Wave 0 |
| `format_purchase_order` uses normalization | unit | `pytest tests/test_export.py::test_formatter_normalization_applied -x` | Wave 0 |
| Export endpoint filename = `{doc_type}_{date}.csv` | integration | `pytest tests/test_export.py::test_export_filename_convention -x` | Wave 0 |
| Export endpoint `X-Export-Warnings` on missing mandatory fields | integration | `pytest tests/test_export.py::test_export_warnings_header -x` | Wave 0 |
| Export HTTP 200 even with missing mandatory fields | integration | `pytest tests/test_export.py::test_export_warnings_still_200 -x` | Wave 0 |
| Export no `X-Export-Warnings` header when all mandatory fields present | integration | `pytest tests/test_export.py::test_export_no_warnings_when_complete -x` | Wave 0 |
| Existing `test_none_values_are_empty_cells` updated | unit | `pytest tests/test_export.py::test_none_values_are_not_found -x` | Modify existing |
| Frontend warning toast shown when header present | unit (Vitest) | `cd frontend && npx vitest run src/App.test.tsx` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_export.py -x -q`
- **Per wave merge:** `pytest tests/ -q`
- **Phase gate:** Full pytest suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] New test functions for `normalize_cell` unit tests — to be added to `tests/test_export.py`
- [ ] New integration tests for filename convention and `X-Export-Warnings` header — to be added to `tests/test_export.py`
- [ ] Update `test_none_values_are_empty_cells` → rename and assert `"Not found"`
- [ ] `frontend/src/App.test.tsx` — Vitest test for warning state in `handleDownloadCSV` (if frontend tests are in scope for this phase)

Note: No new test infrastructure required — pytest + Vitest are already configured.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `None → ""` in formatters | `None → "Not found"` | Phase 7 | Consistent with review table display (REV-03 already shows "Not found") |
| `filename = "job_{job_id}_{doc_type}.csv"` | `filename = "{doc_type}_{date}.csv"` | Phase 7 | Human-readable, datestamped downloads |
| No export warnings | `X-Export-Warnings` header | Phase 7 | Non-blocking quality signal to user |
| `window.open(url, '_blank')` download | `fetch()` + blob download | Phase 7 | Required to read response headers in browser |

---

## Open Questions

1. **EU decimal format (`"5.000,00"` → should be `5000.00`)**
   - What we know: European locales use `.` as thousands separator and `,` as decimal separator
   - What's unclear: LLM may produce either format; the current pattern `re.sub(r"[^\d.,-]", "", value).replace(",", "")` converts `"5.000,00"` to `"5.000.00"` which `float()` rejects, so it falls back to the original — correct failsafe behavior
   - Recommendation: Accept this limitation; document it. The fallback-to-original rule ensures no data is silently corrupted. If EU formats are common in practice, a smarter parser can be added later.

2. **CORS middleware location and existing config**
   - What we know: `src/main.py` exists and mounts FastAPI routers; CORSMiddleware is likely configured there
   - What's unclear: Whether `expose_headers` is already set, and what the existing `allow_origins` setting is
   - Recommendation: Read `src/main.py` at implementation time and add `expose_headers=["X-Export-Warnings"]` without disturbing existing CORS settings.

3. **Frontend warning UI component**
   - What we know: Phase 5 used shadcn/ui components (Button, Badge, Table, Input, Select); no toast/banner component was mentioned
   - What's unclear: Whether a toast library (e.g., Sonner, which shadcn recommends) is installed, or a simple inline banner is preferred
   - Recommendation: Implement as a simple inline warning banner (a styled `<div>`) in the review phase — no new library dependency. This matches the minimal-dependency philosophy of the project.

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection: `src/export/formatters.py` — full formatter implementation, current None handling
- Direct code inspection: `src/api/routes/export.py` — current Content-Disposition and response structure
- Direct code inspection: all five schema files — field names as source of truth for type detection
- Direct code inspection: `frontend/src/App.tsx` — current `handleDownloadCSV` implementation
- Direct code inspection: `tests/test_export.py` — existing tests that will need updating
- Direct code inspection: `pyproject.toml`, `frontend/vite.config.ts` — test runner configuration

### Secondary (MEDIUM confidence)
- MDN CORS: `Access-Control-Expose-Headers` requirement for custom headers in browser fetch — standard browser security behavior, well-documented

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new libraries; all stdlib Python and existing FastAPI patterns
- Architecture: HIGH — normalization insertion point is clear from code inspection; headers are standard FastAPI
- Pitfalls: HIGH — CORS expose-headers is a known cross-origin gotcha; None/empty-string duality verified from PATCH code; test breakage identified from existing test_export.py
- Mandatory fields: HIGH — field names derived directly from schema inspection

**Research date:** 2026-03-24
**Valid until:** 2026-04-24 (stable codebase; no fast-moving dependencies)
