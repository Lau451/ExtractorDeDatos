# Phase 3: CSV Export - Research

**Researched:** 2026-03-22
**Domain:** Python csv stdlib, FastAPI response patterns, Pydantic v2 model introspection
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Missing data handling**
- Missing/unextracted fields render as empty cells in the CSV (not "Not found" or "N/A")
- The API response continues to show "Not found" for the UI — CSV deliberately differs for Excel usability
- Empty cells allow Excel users to filter blanks and process numeric columns without string cleanup

**Export endpoint behavior**
- `GET /jobs/{id}/export` returns the CSV file with `Content-Disposition: attachment; filename="job_{id}_{doc_type}.csv"`
- Filename convention: `job_{job_id}_{doc_type}.csv` (e.g., `job_abc123_purchase_order.csv`)
- If job is not exportable (still processing, failed, doc_type=unknown): return HTTP 409 Conflict with a JSON body explaining why
- If job does not exist: return HTTP 404 (existing pattern)
- Content-Type: `text/csv; charset=utf-8`

**Line item row layout**
- Header-only doc types (Tender/RFQ, Quotation): CSV contains only header columns — no empty line-item columns. Each doc type gets its own clean, distinct column schema (per EXP-04)
- Line-item doc types (PO, Invoice, Supplier Comparison): one row per line item with header fields repeated on every row (denormalized). Every row is self-contained for filtering/sorting/pivoting
- Documents with no extracted line items but that have a line-item schema: produce a single row with header fields and empty line-item columns

**CSV layout (carried from Phase 2)**
- One row per line item — header fields repeat on every row
- Documents with no line items produce a single row
- UTF-8 with BOM encoding (utf-8-sig) for Excel compatibility

### Claude's Discretion
- Column ordering within each doc type's CSV schema
- Column header labels (human-readable vs field names)
- CSV formatter module structure (one formatter per type vs registry pattern)
- CSV delimiter (standard comma expected, but implementation detail)
- How to handle edge case of zero line items in a line-item doc type

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| EXP-01 | User can download the extraction result as a CSV file | FastAPI `Response` with `Content-Disposition: attachment` delivers file download; verified pattern below |
| EXP-02 | CSV column order matches the predefined schema for the detected document type | Pydantic v2 `model_fields` dict preserves class declaration order in Python 3.14; column order can be derived deterministically from field iteration |
| EXP-03 | CSV file is encoded as UTF-8 with BOM (utf-8-sig) for correct display in Excel | Prepend `\ufeff` to content then encode as `utf-8`, or write with `encoding='utf-8-sig'` on file-like object; verified both produce `b'\xef\xbb\xbf'` prefix |
| EXP-04 | Each document type produces its own CSV structure (distinct column schemas) | Five formatters each derive columns from their respective Pydantic schema; line-item types (PO, Invoice, SupplierComparison) vs header-only types (TenderRFQ, Quotation) differ structurally |
| API-04 | API exposes a `GET /jobs/{id}/export` endpoint that returns the final CSV file (applying any user corrections) | New route file `src/api/routes/export.py` registered in `src/main.py`; endpoint reads job from `job_store`, validates exportability, calls formatter, returns `Response` |
</phase_requirements>

---

## Summary

Phase 3 adds a thin export layer on top of the completed Phase 2 extraction pipeline. The core work is: (1) five per-type CSV formatters that convert a stored `extraction_result` dict into correct column-ordered CSV bytes, and (2) a single new FastAPI route `GET /jobs/{id}/export` that gates access, calls the right formatter, and streams the result back as a file download.

The entire implementation uses Python's standard library `csv` module and `io.StringIO` — no additional packages are required. Pydantic v2's `model_fields` dict is ordered by class declaration (confirmed on Python 3.14), so column ordering can be derived mechanically from schema introspection. The `utf-8-sig` BOM is produced by prepending `\ufeff` before encoding.

The biggest decision this phase gives Claude discretion over is the formatter module structure. A registry pattern (`FORMATTER_REGISTRY: dict[str, Callable]`) mirroring the existing `SCHEMA_REGISTRY` is the correct choice — it avoids per-doc-type branching in the route handler and allows easy extension.

**Primary recommendation:** Use `src/export/` module with a formatter-per-type pattern unified by a `FORMATTER_REGISTRY` dict; emit CSV bytes via `io.StringIO` + `csv.writer`; return via `fastapi.responses.Response` with explicit `Content-Disposition` and `text/csv; charset=utf-8` headers.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `csv` | stdlib (Python 3.14) | CSV writing | Standard library; no install; handles quoting/escaping correctly |
| `io` | stdlib | In-memory StringIO buffer | Standard library; avoids temp files |
| `fastapi.responses.Response` | (fastapi already installed) | Return bytes with custom headers | Correct class for fixed-size binary/text responses |

### No New Packages Required

All dependencies for Phase 3 already exist in the project:
- `fastapi` — already installed (Phase 1)
- `pydantic` v2.12.5 — already installed (Phase 2)
- Python `csv` and `io` — standard library

**Installation:** No new packages to install.

**Version verification (already in project):**
- `fastapi`: installed (Phase 1)
- `pydantic`: 2.12.5 (Phase 2)
- `csv`: stdlib 1.0 (Python 3.14.2)

---

## Architecture Patterns

### Recommended Project Structure

```
src/
├── export/
│   ├── __init__.py
│   ├── formatters.py       # Five formatter functions + FORMATTER_REGISTRY
│   └── (no sub-packages needed for 5 doc types)
├── api/
│   └── routes/
│       └── export.py       # GET /jobs/{id}/export route
└── main.py                 # register export_router here
```

### Pattern 1: Formatter Registry

**What:** A dict mapping `doc_type` string to a callable `(extraction_result: dict) -> bytes`. Mirrors the existing `SCHEMA_REGISTRY` pattern.

**When to use:** Any time there are N doc types and each needs type-specific behavior but a uniform call site. The route handler does `FORMATTER_REGISTRY[job.doc_type](job.extraction_result)` — zero branching.

**Example:**

```python
# src/export/formatters.py
import csv
import io
from typing import Callable

BOM = "\ufeff"


def _make_csv_bytes(headers: list[str], rows: list[list]) -> bytes:
    """Write rows to UTF-8-with-BOM CSV bytes."""
    buf = io.StringIO()
    buf.write(BOM)
    writer = csv.writer(buf)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return buf.getvalue().encode("utf-8")


def format_purchase_order(extraction_result: dict) -> bytes:
    from src.extraction.schemas.purchase_order import PurchaseOrderResult, POLineItem

    result = PurchaseOrderResult.model_validate(extraction_result)
    header_fields = [f for f in PurchaseOrderResult.model_fields if f != "line_items"]
    item_fields = list(POLineItem.model_fields.keys())
    columns = header_fields + item_fields

    header_values = [getattr(result, f) for f in header_fields]

    if not result.line_items:
        rows = [header_values + [None] * len(item_fields)]
    else:
        rows = [
            header_values + [getattr(item, f) for f in item_fields]
            for item in result.line_items
        ]

    # None -> empty string (EXP-02 locked decision)
    rows = [[("" if v is None else v) for v in row] for row in rows]
    return _make_csv_bytes(columns, rows)


# Header-only types: simpler — no line_items expansion
def format_tender_rfq(extraction_result: dict) -> bytes:
    from src.extraction.schemas.tender_rfq import TenderRFQResult

    result = TenderRFQResult.model_validate(extraction_result)
    fields = list(TenderRFQResult.model_fields.keys())
    row = [("" if getattr(result, f) is None else getattr(result, f)) for f in fields]
    return _make_csv_bytes(fields, [row])


FORMATTER_REGISTRY: dict[str, Callable[[dict], bytes]] = {
    "purchase_order": format_purchase_order,
    "tender_rfq": format_tender_rfq,
    "quotation": format_quotation,
    "invoice": format_invoice,
    "supplier_comparison": format_supplier_comparison,
}
```

### Pattern 2: Export Route with 409 Gate

**What:** The route validates job state before calling the formatter. Non-exportable states return 409 with a JSON body (locked decision).

**When to use:** Any time an action is only valid for a subset of resource states.

**Example:**

```python
# src/api/routes/export.py
from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response
from src.core.job_store import job_store
from src.export.formatters import FORMATTER_REGISTRY

router = APIRouter()

EXPORTABLE_STATUSES = {"complete"}
EXPORTABLE_DOC_TYPES = {"purchase_order", "tender_rfq", "quotation", "invoice", "supplier_comparison"}


@router.get("/jobs/{job_id}/export")
async def export_job(job_id: str):
    job = await job_store.get(job_id)

    if job is None:
        return JSONResponse(status_code=404, content={"error": "job_not_found", "message": f"No job with ID '{job_id}'"})

    if job.status not in EXPORTABLE_STATUSES:
        return JSONResponse(status_code=409, content={"error": "job_not_exportable", "message": f"Job is not complete (status: {job.status})"})

    if job.doc_type not in EXPORTABLE_DOC_TYPES:
        return JSONResponse(status_code=409, content={"error": "job_not_exportable", "message": f"Cannot export job with doc_type '{job.doc_type}'"})

    formatter = FORMATTER_REGISTRY[job.doc_type]
    csv_bytes = formatter(job.extraction_result)
    filename = f"job_{job_id}_{job.doc_type}.csv"

    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
```

### Anti-Patterns to Avoid

- **Using `StreamingResponse` for fixed-size CSV:** `Response` is simpler for in-memory bytes that fit in RAM. `StreamingResponse` is only needed for multi-GB files or true streaming.
- **Using `encoding='utf-8-sig'` on `io.StringIO`:** `StringIO` does not accept an `encoding` argument (it operates on strings, not bytes). The BOM must be prepended as a Unicode character (`\ufeff`) before encoding the result to bytes.
- **Branching on doc_type in the route handler:** Use `FORMATTER_REGISTRY[job.doc_type]` — this keeps the route handler O(1) and extensible.
- **Including `line_items` as a column in header-only types:** The locked decision is that Tender/RFQ and Quotation CSV schemas contain ONLY header columns.
- **Using "Not found" for missing fields in CSV:** This is for the API response only (handled in `jobs.py`). CSV must use empty string `""` for `None` values.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CSV quoting/escaping | Custom string join with commas | `csv.writer` | Handles embedded commas, quotes, newlines in field values automatically (RFC 4180) |
| UTF-8 BOM | Manual byte manipulation | `\ufeff` prefix + `.encode("utf-8")` | One-liner; well-tested pattern |
| Column order derivation | Hardcoded list of column names | `model_fields.keys()` on Pydantic model | Field order guaranteed by Python dict insertion order (3.7+) and Pydantic v2 class attribute declaration order |
| Formatter dispatch | `if doc_type == "purchase_order": ...` chain | `FORMATTER_REGISTRY[doc_type]` | O(1) lookup, no branching, mirrors existing SCHEMA_REGISTRY pattern |

**Key insight:** The `csv` module handles all the hard parts of RFC 4180 compliance. Custom comma-delimited string building fails on any field value containing a comma (e.g., `"Acme Corp, LLC"` in buyer_name).

---

## Common Pitfalls

### Pitfall 1: StringIO Does Not Accept `encoding` Parameter

**What goes wrong:** `io.StringIO(encoding='utf-8-sig')` raises `TypeError` — StringIO is an in-memory string buffer, not a byte stream. The `encoding` kwarg is only for `open()` on file objects.

**Why it happens:** Confusion between `io.StringIO` (text) and `io.BytesIO` (bytes) or `open()`.

**How to avoid:** Write to `StringIO`, prepend `"\ufeff"` to the string buffer before calling `.encode("utf-8")`.

**Warning signs:** `TypeError: StringIO.__init__() got an unexpected keyword argument 'encoding'`

### Pitfall 2: `model_fields` Includes `line_items` Key

**What goes wrong:** If you iterate all `model_fields` for a line-item schema type to build columns, `line_items` appears as a column name — it is a list field, not a scalar.

**Why it happens:** `model_fields` returns ALL fields including the `line_items: list[...]` field.

**How to avoid:** Always exclude `line_items` explicitly when building header field lists:
```python
header_fields = [f for f in PurchaseOrderResult.model_fields if f != "line_items"]
```

**Warning signs:** CSV header row contains `"line_items"` as a column name; CSV cell contains `"[]"` or `"[{'item_number': ...}]"`.

### Pitfall 3: HTTP 409 on Unknown doc_type

**What goes wrong:** `job.doc_type` can be `"unknown"` (Phase 2 decision: unknown doc_type sets status to complete without extraction). `FORMATTER_REGISTRY["unknown"]` raises `KeyError`.

**Why it happens:** Jobs with unknown doc_type reach `status=complete` but have no extraction_result and no formatter.

**How to avoid:** Gate on `job.doc_type in EXPORTABLE_DOC_TYPES` (which does not include `"unknown"`) before looking up the formatter. Return 409.

**Warning signs:** `KeyError: 'unknown'` in server logs.

### Pitfall 4: `None` Values Written as the String `"None"` in CSV

**What goes wrong:** `csv.writer.writerow([None, "val"])` writes `",val"` (empty string for None) in Python 3. BUT if you build a list like `[str(v) for v in row]`, `None` becomes `"None"`.

**Why it happens:** Calling `str()` on `None` produces `"None"`, not `""`.

**How to avoid:** Use `("" if v is None else v)` for every cell value. Do NOT use `str(v)`.

**Warning signs:** CSV cells contain the literal string `"None"`.

### Pitfall 5: `extraction_result` Is None for Unknown or Error Jobs

**What goes wrong:** `formatter(job.extraction_result)` where `extraction_result is None` causes the formatter to crash on `PurchaseOrderResult.model_validate(None)`.

**Why it happens:** Jobs with `doc_type="unknown"` or that errored mid-extraction have `extraction_result=None`.

**How to avoid:** The 409 gate (Pitfall 3) prevents reaching the formatter call. Also add a None guard in the formatter as defense-in-depth.

---

## Code Examples

Verified patterns from local environment (Python 3.14.2, Pydantic 2.12.5):

### BOM Generation

```python
# Source: verified locally — io.StringIO + \ufeff prefix
import io, csv

buf = io.StringIO()
buf.write("\ufeff")               # UTF-8 BOM as Unicode character
writer = csv.writer(buf)
writer.writerow(["col1", "col2"])
writer.writerow(["val1", ""])     # empty string for None fields

csv_bytes = buf.getvalue().encode("utf-8")
# csv_bytes starts with b'\xef\xbb\xbf' — verified correct
```

### Field Order from Pydantic v2

```python
# Source: verified locally — model_fields is ordered dict in Pydantic v2 + Python 3.14
from src.extraction.schemas.purchase_order import PurchaseOrderResult, POLineItem

header_fields = [f for f in PurchaseOrderResult.model_fields if f != "line_items"]
# ['po_number', 'issue_date', 'buyer_name', 'supplier_name', 'delivery_date',
#  'currency', 'total_amount', 'payment_terms', 'shipping_address', 'notes']

item_fields = list(POLineItem.model_fields.keys())
# ['item_number', 'description', 'sku', 'quantity', 'unit', 'unit_price', 'extended_price']
```

### model_validate Round-trip

```python
# Source: verified locally — extraction_result stored as dict from .model_dump()
from src.extraction.schemas.purchase_order import PurchaseOrderResult

stored_dict = job.extraction_result   # dict from .model_dump()
result = PurchaseOrderResult.model_validate(stored_dict)
# All fields accessible as typed attributes; line_items is list[POLineItem]
```

### FastAPI Response for CSV

```python
# Source: verified locally — fastapi.responses.Response
from fastapi.responses import Response

return Response(
    content=csv_bytes,                          # bytes
    media_type="text/csv; charset=utf-8",
    headers={"Content-Disposition": f'attachment; filename="{filename}"'},
)
```

---

## Complete Column Schemas (Derived from Schemas)

Listed in declaration order (matches CSV column order):

### Purchase Order (17 columns, line-item type)

| # | Column (header fields) |
|---|----------------------|
| 1 | po_number |
| 2 | issue_date |
| 3 | buyer_name |
| 4 | supplier_name |
| 5 | delivery_date |
| 6 | currency |
| 7 | total_amount |
| 8 | payment_terms |
| 9 | shipping_address |
| 10 | notes |
| # | Column (line item fields, repeat per row) |
| 11 | item_number |
| 12 | description |
| 13 | sku |
| 14 | quantity |
| 15 | unit |
| 16 | unit_price |
| 17 | extended_price |

### Invoice (19 columns, line-item type)

| # | Column (header fields) |
|---|----------------------|
| 1 | invoice_number |
| 2 | invoice_date |
| 3 | due_date |
| 4 | issuer_name |
| 5 | issuer_address |
| 6 | recipient_name |
| 7 | recipient_address |
| 8 | currency |
| 9 | subtotal |
| 10 | tax_total |
| 11 | total_amount |
| 12 | payment_terms |
| 13 | po_reference |
| # | Column (line item fields) |
| 14 | item_number |
| 15 | description |
| 16 | quantity |
| 17 | unit |
| 18 | unit_price |
| 19 | extended_price |

### Supplier Comparison (16 columns, line-item type)

| # | Column (header fields) |
|---|----------------------|
| 1 | project_name |
| 2 | comparison_date |
| 3 | rfq_reference |
| 4 | evaluation_criteria |
| 5 | recommended_supplier |
| 6 | notes |
| # | Column (supplier row fields) |
| 7 | supplier_name |
| 8 | item_description |
| 9 | unit_price |
| 10 | total_price |
| 11 | lead_time |
| 12 | payment_terms |
| 13 | delivery_terms |
| 14 | warranty |
| 15 | compliance_notes |
| 16 | overall_score |

### Tender/RFQ (8 columns, header-only)

po_number, issue_date, issuing_organization, submission_deadline, contact_person, project_title, currency, notes

Wait — correct fields from schema:
`tender_reference, issue_date, issuing_organization, submission_deadline, contact_person, project_title, currency, notes`

### Quotation (12 columns, header-only)

`quote_number, quote_date, vendor_name, vendor_address, buyer_name, valid_until, currency, subtotal, tax_total, grand_total, payment_terms, delivery_terms`

---

## Architecture: Discretion Choices

The following are Claude's discretion items (from CONTEXT.md). These are recommendations for the planner.

### Column Header Labels

**Recommendation:** Use the Python field name as-is (snake_case). Rationale: (1) downstream CSV consumers (pivot tables, scripts) are more reliable with machine-readable headers; (2) avoids maintaining a separate label mapping; (3) user-facing label formatting belongs in Phase 5 (web UI). If human labels are needed later, a `COLUMN_LABELS` dict can be added without changing the CSV structure.

### Formatter Module Structure

**Recommendation:** Single file `src/export/formatters.py` with five formatter functions + `FORMATTER_REGISTRY` dict + shared `_make_csv_bytes` helper. The volume (5 formatters, ~200 lines total) does not justify sub-modules. If more doc types are added in v2, a `src/export/formatters/` package is the natural migration.

### CSV Delimiter

**Recommendation:** Standard comma (`,`). This is the default for `csv.writer` and the expectation for Excel on all locales (Excel detects BOM and handles comma-delimited correctly). No configuration needed.

### Zero Line Items in a Line-item Type

**Recommendation:** Produce a single row with all header fields populated and all line-item columns empty. This aligns with the locked decision ("Documents with no line items produce a single row") and ensures the CSV always has a data row (not just a header), making it easier to detect in downstream tooling.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `csv.writer` with `open(..., encoding='utf-8-sig')` | `io.StringIO` + `\ufeff` prefix + `.encode('utf-8')` | Always for in-memory | Must use StringIO for in-memory CSV; file-based approach not applicable here |
| `StreamingResponse` for all file responses | `Response` for fixed-size in-memory content | FastAPI always had both | Simpler code; `StreamingResponse` only needed for generators/large files |

---

## Open Questions

1. **Column header labels: snake_case vs human-readable**
   - What we know: CONTEXT.md marks this as Claude's discretion
   - What's unclear: Whether downstream CSV consumers (the target user's Excel workflows) prefer machine-readable or human-readable headers
   - Recommendation: Use snake_case field names (see Architecture: Discretion Choices above); human labels can be added in Phase 5 if needed

2. **Phase 4 API-03 compatibility (PATCH /jobs/{id}/fields)**
   - What we know: Phase 4 adds user field corrections; API-04 spec says export applies corrections
   - What's unclear: Phase 3 must not over-engineer the formatter to block Phase 4, but also must not build the correction mechanism itself
   - Recommendation: Phase 3 export reads `job.extraction_result` directly. Phase 4 will either update `extraction_result` in-place or add a separate `corrected_result` field. The formatter interface (`dict -> bytes`) remains identical in both cases. No Phase 3 changes needed.

---

## Validation Architecture

`nyquist_validation` is enabled in `.planning/config.json`.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio (already installed) |
| Config file | `pyproject.toml` — `[tool.pytest.ini_options]` with `asyncio_mode = "auto"`, `testpaths = ["tests"]` |
| Quick run command | `python -m pytest tests/test_export.py -x -q` |
| Full suite command | `python -m pytest tests/ -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EXP-01 | GET /jobs/{id}/export returns 200 with file attachment for a complete job | integration | `python -m pytest tests/test_export.py::test_export_complete_job -x` | Wave 0 |
| EXP-02 | CSV column order matches schema declaration order | unit | `python -m pytest tests/test_export.py::test_column_order_purchase_order -x` | Wave 0 |
| EXP-02 | All 5 doc types produce correct column schemas | unit | `python -m pytest tests/test_export.py::test_column_order_all_types -x` | Wave 0 |
| EXP-03 | CSV bytes start with UTF-8 BOM (`b'\xef\xbb\xbf'`) | unit | `python -m pytest tests/test_export.py::test_csv_has_bom -x` | Wave 0 |
| EXP-04 | Each doc type produces distinct column count and names | unit | `python -m pytest tests/test_export.py::test_distinct_schemas -x` | Wave 0 |
| API-04 | GET /jobs/{id}/export returns 404 for unknown job | integration | `python -m pytest tests/test_export.py::test_export_404 -x` | Wave 0 |
| API-04 | GET /jobs/{id}/export returns 409 for non-complete job | integration | `python -m pytest tests/test_export.py::test_export_409_not_complete -x` | Wave 0 |
| API-04 | GET /jobs/{id}/export returns 409 for unknown doc_type | integration | `python -m pytest tests/test_export.py::test_export_409_unknown_doc_type -x` | Wave 0 |
| API-04 | Content-Type header is `text/csv; charset=utf-8` | integration | `python -m pytest tests/test_export.py::test_export_content_type -x` | Wave 0 |
| API-04 | Content-Disposition filename follows `job_{id}_{doc_type}.csv` pattern | integration | `python -m pytest tests/test_export.py::test_export_filename -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/test_export.py -x -q`
- **Per wave merge:** `python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_export.py` — covers all EXP-01 through EXP-04 and API-04 test cases listed above
- [ ] `src/export/__init__.py` — empty init for new module
- [ ] `src/export/formatters.py` — formatter functions + FORMATTER_REGISTRY
- [ ] `src/api/routes/export.py` — GET /jobs/{id}/export route

*(conftest.py and shared fixtures already exist and are sufficient — `client` and `clear_job_store` fixtures are reusable as-is)*

---

## Sources

### Primary (HIGH confidence)

- Python 3.14.2 stdlib `csv` module — tested locally via `python -c "import csv; ..."` — confirmed `csv` version 1.0
- Python 3.14.2 stdlib `io.StringIO` — tested locally; confirmed `encoding` kwarg not accepted
- Pydantic 2.12.5 `model_fields` — tested locally; confirmed ordered dict preserving class declaration order
- FastAPI `Response` class — tested locally; confirmed `Content-Disposition` header passes through correctly
- BOM encoding — tested locally; `"\ufeff".encode("utf-8") == b"\xef\xbb\xbf"` confirmed

### Secondary (MEDIUM confidence)

- RFC 4180 CSV quoting behavior — `csv.writer` standard library implements this; behavior confirmed via local test showing `None` writes as empty string

### Project Context (HIGH confidence)

- `src/extraction/schemas/*.py` — read directly; all field names and ordering confirmed
- `src/core/job_store.py` — read directly; `extraction_result: Optional[dict]`, `doc_type: Optional[str]` confirmed
- `src/api/routes/jobs.py` — read directly; route pattern and `JSONResponse` usage confirmed
- `tests/conftest.py` — read directly; `client` and `clear_job_store` fixtures reusable for Phase 3 tests
- `pyproject.toml` — read directly; `asyncio_mode = "auto"` confirmed

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — no new packages; stdlib only; verified locally
- Architecture: HIGH — patterns derived directly from existing codebase conventions and verified locally
- Column schemas: HIGH — derived by running `model_fields.keys()` against live schema classes
- Pitfalls: HIGH — each pitfall verified by running the failure condition locally
- Test map: HIGH — test names are prescriptive; infrastructure already exists

**Research date:** 2026-03-22
**Valid until:** 2026-05-22 (stable domain; Python stdlib and Pydantic v2 are not fast-moving for this use case)
