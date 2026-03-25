# Phase 8: Offers/Quotes Line Items Only - Research

**Researched:** 2026-03-25
**Domain:** Pydantic schema reduction, CSV formatter surgery, quantity string normalization, React conditional rendering
**Confidence:** HIGH

## Summary

Phase 8 is a surgical narrowing of the tender_rfq and quotation document types. Both types currently carry 8–12 header fields (reference number, dates, totals, vendor info, etc.) that the user has decided are irrelevant. The goal is to reduce their schemas to a single field — `line_items` — producing a 3-column CSV (item_number, quantity, description) and hiding the header-fields section in the frontend review table.

The implementation touches four layers: (1) Pydantic schemas in `src/extraction/schemas/`, (2) CSV formatters in `src/export/formatters.py`, (3) the Gemini extraction prompt path (indirectly, via schema change), and (4) the frontend `App.tsx` review rendering guard. All four layers have been fully read and their current state is understood. No new libraries are needed — the changes are pure refactors within the existing codebase.

The quantity normalization rule (strip unit suffixes, then strip trailing `.0`) is the only net-new algorithmic logic. It is a pure string transformation that fits cleanly into the existing `normalize_cell` dispatch pattern.

**Primary recommendation:** Implement in two plans — Plan 1: backend (schemas + formatter + quantity normalization + tests), Plan 2: frontend (ReviewTable guard + App.tsx logic + frontend tests). Keep plans independent so backend can be validated with pytest before frontend is touched.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**CSV output scope**
- Tender/RFQ and quotation CSVs produce **3 columns only**: `item_number`, `quantity`, `description`
- All header columns are omitted entirely from the CSV — this replaces the Phase 6 denormalized layout for these two types
- Other doc types (purchase_order, invoice, supplier_comparison) are unchanged
- If zero line items are extracted: produce **one data row** with `"Not found"` in all 3 fields (consistent with Phase 7 None → "Not found")

**Quantity normalization to whole number**
- **Strip trailing `.0`**: `"3.00"` → `"3"`, `"5.0"` → `"5"`. Do NOT round — `"3.5"` stays `"3.5"` (only strip when it's already an integer value with a decimal suffix)
- **Strip non-numeric suffix**: extract the leading numeric part — `"5 kg"` → `"5"`, `"10 pcs"` → `"10"`. Strip is applied before the `.0` stripping step
- **Unparseable strings**: keep the original value unchanged (never lose data)
- **None/missing quantity**: export as `"Not found"` (Phase 7 rule applies)
- This normalization applies only to the `quantity` field in line items, not to quantity fields in other doc types

**Extraction scope — narrow schemas and Gemini prompts**
- **Remove header fields** from `TenderRFQResult` and `QuotationResult` Pydantic schemas — only `line_items: list[TenderLineItem]` / `list[QuotationLineItem]` remains
- Gemini is no longer asked to extract tender reference, issue date, vendor name, totals, etc. for these two doc types — narrower prompt reduces token cost and extraction noise
- `TenderLineItem` and `QuotationLineItem` schemas are unchanged (item_number, quantity, description)

**Frontend review table**
- For tender/RFQ and quotation, the review table shows **only the line items table** (no header fields section)
- The header fields section (`ReviewTable` / key-value pairs) is hidden for these doc types
- `LineItemsTable` remains the same component, already handles the 3-field layout
- The doc type display and override dropdown are unchanged (still shown at the top)

### Claude's Discretion
- How to detect "integer-valued float string" for the `.0` strip (e.g., check if `float(s) == int(float(s))`)
- Whether to apply quantity normalization inside `normalize_cell` (via a new `_is_quantity_field` helper) or in a dedicated `normalize_quantity` function
- Whether the header-field removal from schemas is a breaking schema change that requires updating Gemini extraction tests

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

## Standard Stack

### Core (no new libraries)

| Layer | File | What Changes | Confidence |
|-------|------|--------------|------------|
| Pydantic schema | `src/extraction/schemas/tender_rfq.py` | Remove 8 header fields from `TenderRFQResult`; keep `TenderLineItem` and `line_items` field | HIGH |
| Pydantic schema | `src/extraction/schemas/quotation.py` | Remove 12 header fields from `QuotationResult`; keep `QuotationLineItem` and `line_items` field | HIGH |
| CSV formatter | `src/export/formatters.py` | New `_format_line_items_only()` helper; replace `format_tender_rfq` / `format_quotation`; add `normalize_quantity()`; update `MANDATORY_FIELDS` | HIGH |
| Frontend | `frontend/src/App.tsx` | Add guard: hide `<ReviewTable>` when doc_type is tender_rfq or quotation | HIGH |
| Tests | `tests/test_export.py` | Update `SAMPLE_TENDER` / `SAMPLE_QUOTATION`, update column-order tests, add quantity normalization tests | HIGH |

### No New Dependencies

Installation: none required.

## Architecture Patterns

### Recommended Project Structure (unchanged)

```
src/
├── extraction/
│   └── schemas/
│       ├── tender_rfq.py      # MODIFY: strip header fields
│       └── quotation.py       # MODIFY: strip header fields
└── export/
    └── formatters.py          # MODIFY: new helper + normalize_quantity
frontend/src/
├── App.tsx                    # MODIFY: conditional ReviewTable rendering
└── lib/
    └── docTypes.ts            # No change needed
```

### Pattern 1: Line-Items-Only Formatter Helper

The existing `_format_line_item_type()` helper handles header+items. A new `_format_line_items_only()` helper covers the items-only case:

```python
# Source: analysis of src/export/formatters.py
def _format_line_items_only(item_model_class, extraction_result: dict) -> bytes:
    """Format a doc type that has ONLY line_items — no header fields.

    Produces 3 columns: item_number, quantity, description.
    If zero line items: one row with 'Not found' in all 3 cells.
    """
    item_fields = list(item_model_class.model_fields.keys())
    raw_line_items = extraction_result.get("line_items") or []

    if not raw_line_items:
        rows = [[normalize_cell(f, None) for f in item_fields]]
    else:
        rows = [
            [normalize_cell(item_fields[i], item.get(item_fields[i]))
             for i in range(len(item_fields))]
            for item in raw_line_items
        ]

    return _make_csv_bytes(item_fields, rows)
```

**Key observation:** The new helper does NOT call `model_class.model_validate()` on a full result model — it reads `line_items` directly from the raw dict. This avoids the need to construct the stripped `TenderRFQResult` model just to extract the list.

**Alternative:** Call `model_validate()` on the stripped schema then iterate `result.line_items`. Either approach works; the direct dict approach is simpler since the stripped schema has only one field.

### Pattern 2: Quantity Normalization in normalize_cell

The existing `normalize_cell` dispatches by field name keyword. Quantity normalization follows the same pattern:

```python
# Source: analysis of src/export/formatters.py normalize_cell()
_QUANTITY_FIELD_NAMES = ("quantity",)


def _is_quantity_field(name: str) -> bool:
    return name in _QUANTITY_FIELD_NAMES


def normalize_quantity(value: str) -> str:
    """Strip unit suffix, then strip trailing .0 for integer-valued floats.

    Examples:
      "5 kg"   -> "5"
      "3.00"   -> "3"
      "3.5"    -> "3.5"   (non-integer float: preserved)
      "N/A"    -> "N/A"   (unparseable: preserved)
    """
    import re
    # Step 1: strip non-numeric suffix — keep leading numeric part
    m = re.match(r"^(\d+(?:\.\d+)?)", value.strip())
    if not m:
        return value  # unparseable: return as-is
    numeric_part = m.group(1)
    # Step 2: strip trailing .0 only when it's an integer-valued float
    try:
        as_float = float(numeric_part)
        if as_float == int(as_float):
            return str(int(as_float))
        return numeric_part
    except ValueError:
        return value  # fallback: return original
```

**Placement in normalize_cell:** Add a new dispatch branch after the amount/date checks:

```python
def normalize_cell(field_name: str, value) -> str:
    if value is None:
        return "Not found"
    s = str(value)
    if not s.strip():
        return "Not found"
    if _is_amount_field(field_name):
        return _normalize_amount(s)
    if _is_date_field(field_name):
        return _normalize_date(s)
    if _is_quantity_field(field_name):       # NEW
        return normalize_quantity(s)         # NEW
    return _normalize_text(s)
```

**Important scope constraint:** `_is_quantity_field` uses exact name matching (`name in _QUANTITY_FIELD_NAMES`), NOT substring matching. This prevents quantity normalization from accidentally triggering on hypothetical future fields like `quantity_unit` or `min_quantity`. The field name in all relevant schemas is exactly `"quantity"`.

### Pattern 3: Frontend ReviewTable Guard

`App.tsx` currently always renders `<ReviewTable>` for the review phase. The guard is a simple doc_type check:

```typescript
// Source: analysis of frontend/src/App.tsx review phase rendering
const HEADER_ONLY_DOC_TYPES = new Set(['tender_rfq', 'quotation']);

// In review phase JSX — replace the unconditional ReviewTable with:
{!HEADER_ONLY_DOC_TYPES.has(jobData.doc_type ?? '') && (
  <ReviewTable
    data={jobData.extraction_result ?? {}}
    lineItemKey={LINE_ITEM_KEYS[jobData.doc_type ?? ''] ?? null}
    onFieldSave={handleFieldSave}
  />
)}
```

The `LineItemsTable` rendering block in App.tsx already handles the case where the array has items — it checks `Array.isArray(...)` and `length > 0`. For tender/quotation with zero items, the backend now returns a "Not found" sentinel row, so the array will always have at least one entry when the job is complete.

**Note:** The `handleFieldSave` callback only patches scalar header fields. For tender/quotation, there are no header fields to patch — only `handleLineItemsSave` applies. No changes needed to the PATCH API since the payload is generic `{ [field]: value }`.

### Pattern 4: MANDATORY_FIELDS Update

`MANDATORY_FIELDS` in `formatters.py` currently has non-empty lists for `tender_rfq` and `quotation`. Since these types no longer have mandatory header fields, the entries must be set to empty lists (or removed — `check_mandatory_fields` already returns `[]` for unknown keys, but explicit empty list is clearer):

```python
MANDATORY_FIELDS: dict[str, list[str]] = {
    "purchase_order": ["po_number", "issue_date", "buyer_name", "supplier_name"],
    "tender_rfq": [],    # no header fields remain
    "quotation": [],     # no header fields remain
    "invoice": ["invoice_number", "invoice_date", "issuer_name"],
    "supplier_comparison": ["project_name", "comparison_date", "rfq_reference"],
}
```

### Anti-Patterns to Avoid

- **Calling `_format_line_item_type()` with stripped schemas:** `_format_line_item_type()` reads `model_class.model_fields` to build header_fields list. With the stripped schema it would produce `header_fields = []` and still work, but the intent is clearer with a dedicated helper.
- **Using substring matching for `_is_quantity_field`:** Would incorrectly activate on unrelated field names in future doc types. Use exact name set membership.
- **Rounding non-integer floats:** `"3.5"` must stay `"3.5"`. Only strip when `float(s) == int(float(s))`.
- **Modifying `TenderLineItem` or `QuotationLineItem`:** These are unchanged. The phase only removes header fields from the *result* models.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Integer-valued float detection | Custom string parser | `float(s) == int(float(s))` | Already handles `"3.00"`, `"5.0"`, `"100.000"` in one expression |
| Leading numeric extraction | Custom tokenizer | `re.match(r"^(\d+(?:\.\d+)?)", s)` | Handles integer and decimal prefixes; returns None for non-numeric starts |
| Pydantic extra-field tolerance | Schema migration | Pydantic v2 default behavior: extra fields are ignored in `model_validate()` | In-memory jobs that were extracted with the old schema will silently drop header fields when re-validated — no migration needed |

## Common Pitfalls

### Pitfall 1: Existing Test Data for tender_rfq / quotation Contains Header Fields

**What goes wrong:** `SAMPLE_TENDER` and `SAMPLE_QUOTATION` in `tests/test_export.py` include header fields (tender_reference, issue_date, vendor_name, etc.). After the schema change, `model_validate()` on the stripped schema silently ignores those extra keys (Pydantic v2 default). The formatter output will change to 3 columns.

**Why it happens:** Tests were written against the old schema. Column-count assertions (`assert len(rows[0]) == 11`, `assert len(rows[0]) == 15`) and column-order assertions will break.

**How to avoid:** Update the test fixtures and assertions as part of Plan 1. The new column count for both types is 3. The `test_distinct_schemas` test currently asserts all 5 types have distinct counts — after the change, tender_rfq and quotation both produce 3 columns, breaking that uniqueness assertion. Either relax the assertion to check only the 3 unaffected types, or replace it with explicit count checks per type.

**Warning signs:** `assert len(set(counts.values())) == 5` will fail with `len == 4` because tender_rfq and quotation both produce 3 columns.

### Pitfall 2: test_tender_line_item_rows and test_quotation_line_item_rows Become Stale

**What goes wrong:** `test_tender_line_item_rows` asserts `rows[1][ref_idx] == "TND-001"` where `ref_idx = rows[0].index("tender_reference")`. After the schema change, "tender_reference" is no longer a column — the `index()` call will raise `ValueError`.

**How to avoid:** Rewrite these tests to assert against the new 3-column layout: verify columns are `["item_number", "quantity", "description"]` and check item values.

### Pitfall 3: zero-items "Not found" Row — Sentinel vs. Empty Array

**What goes wrong:** The frontend `LineItemsTable` guard in App.tsx checks `length > 0` before rendering. With the old formatters a zero-items extraction yielded an empty list. The backend now emits a "Not found" sentinel row in the CSV, but the `extraction_result` in the job store still contains `line_items: []` (that's what Gemini extracted). The sentinel row is a CSV output concern only — the job store retains the raw empty list.

**Implication:** The LineItemsTable in App.tsx will not render for tender/quotation when Gemini extracts zero items, because the `line_items` array is empty. This is acceptable behavior: the user sees the DocTypeBar and the Download CSV button, and the CSV itself contains the "Not found" sentinel row. No frontend change is needed for this edge case.

**How to avoid:** Understand the separation — sentinel rows are a formatter concern, not a job-store concern.

### Pitfall 4: MANDATORY_FIELDS Warning Header for tender/quotation

**What goes wrong:** With the old `MANDATORY_FIELDS` entries, a tender/quotation export would produce `X-Export-Warnings` if tender_reference / quote_number / vendor_name were missing. After removing header fields from the schema, Gemini will no longer extract those fields, so they will always be absent — if `MANDATORY_FIELDS` is not updated, every tender/quotation export will emit warnings.

**How to avoid:** Set `MANDATORY_FIELDS["tender_rfq"] = []` and `MANDATORY_FIELDS["quotation"] = []` as part of Plan 1 formatter changes.

### Pitfall 5: Frontend handleFieldSave on Header-less Doc Types

**What goes wrong:** If the user somehow triggers a field save on a tender/quotation (e.g., through a stale component state), `api.patchFields()` would be called with a header field that no longer exists in the schema. Pydantic's `_deep_merge` in the PATCH handler would silently accept the extra key (since `extraction_result` is stored as `dict`, not validated through the schema at patch time).

**Impact:** Low risk. The ReviewTable is hidden for tender/quotation so there is no UI path to trigger this. No defensive code needed.

## Code Examples

### Updated TenderRFQResult schema

```python
# src/extraction/schemas/tender_rfq.py — after Phase 8
from pydantic import BaseModel, Field
from typing import Optional


class TenderLineItem(BaseModel):
    item_number: Optional[str] = Field(None, description="Line item number or sequence number")
    quantity: Optional[str] = Field(None, description="Requested quantity as a string")
    description: Optional[str] = Field(None, description="Product name or item description")


class TenderRFQResult(BaseModel):
    line_items: list[TenderLineItem] = Field(default_factory=list, description="List of requested line items")
```

### Updated QuotationResult schema

```python
# src/extraction/schemas/quotation.py — after Phase 8
from pydantic import BaseModel, Field
from typing import Optional


class QuotationLineItem(BaseModel):
    item_number: Optional[str] = Field(None, description="Line item number or sequence number")
    quantity: Optional[str] = Field(None, description="Quoted quantity as a string")
    description: Optional[str] = Field(None, description="Product name or item description")


class QuotationResult(BaseModel):
    line_items: list[QuotationLineItem] = Field(default_factory=list, description="List of quoted line items")
```

### Updated format_tender_rfq / format_quotation

```python
# src/export/formatters.py — after Phase 8
def format_tender_rfq(extraction_result: dict) -> bytes:
    """Format a TenderRFQ extraction result as CSV bytes — 3 columns only."""
    return _format_line_items_only(TenderLineItem, extraction_result)


def format_quotation(extraction_result: dict) -> bytes:
    """Format a Quotation extraction result as CSV bytes — 3 columns only."""
    return _format_line_items_only(QuotationLineItem, extraction_result)
```

### Updated test column assertions

```python
# tests/test_export.py — after Phase 8
def test_column_order_tender_rfq():
    result = format_tender_rfq(SAMPLE_TENDER)
    rows = _parse_csv(result)
    assert rows[0] == ["item_number", "quantity", "description"]
    assert len(rows[0]) == 3


def test_column_order_quotation():
    result = format_quotation(SAMPLE_QUOTATION)
    rows = _parse_csv(result)
    assert rows[0] == ["item_number", "quantity", "description"]
    assert len(rows[0]) == 3
```

### Quantity normalization unit tests

```python
# tests/test_export.py — new tests for Phase 8
def test_normalize_quantity_strips_unit_suffix():
    assert normalize_cell("quantity", "5 kg") == "5"
    assert normalize_cell("quantity", "10 pcs") == "10"
    assert normalize_cell("quantity", "3 boxes") == "3"


def test_normalize_quantity_strips_trailing_zero():
    assert normalize_cell("quantity", "3.00") == "3"
    assert normalize_cell("quantity", "5.0") == "5"
    assert normalize_cell("quantity", "100.000") == "100"


def test_normalize_quantity_preserves_non_integer_float():
    assert normalize_cell("quantity", "3.5") == "3.5"
    assert normalize_cell("quantity", "2.75") == "2.75"


def test_normalize_quantity_preserves_unparseable():
    assert normalize_cell("quantity", "N/A") == "N/A"
    assert normalize_cell("quantity", "TBD") == "TBD"


def test_normalize_quantity_none_is_not_found():
    assert normalize_cell("quantity", None) == "Not found"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| tender_rfq / quotation: 11/15 columns with header fields | tender_rfq / quotation: 3 columns, line items only | Phase 8 | Simpler CSV, no header noise |
| No quantity normalization | Quantity: strip unit suffix + strip `.0` | Phase 8 | Cleaner integer quantities |
| ReviewTable always shown | ReviewTable hidden for tender/quotation | Phase 8 | Cleaner review UI for these types |

**Deprecated/outdated after Phase 8:**
- `TenderRFQResult` header fields (tender_reference, issue_date, issuing_organization, submission_deadline, contact_person, project_title, currency, notes): removed
- `QuotationResult` header fields (quote_number, quote_date, vendor_name, vendor_address, buyer_name, valid_until, currency, subtotal, tax_total, grand_total, payment_terms, delivery_terms): removed
- `MANDATORY_FIELDS["tender_rfq"]` and `MANDATORY_FIELDS["quotation"]` non-empty lists: replaced with `[]`

## Open Questions

1. **`test_distinct_schemas` assertion uniqueness**
   - What we know: After Phase 8, tender_rfq and quotation both produce 3 columns, breaking the `len(set(counts.values())) == 5` assertion
   - What's unclear: Should the test be deleted, split into individual count assertions, or kept with relaxed uniqueness?
   - Recommendation: Replace with explicit `assert counts["tender_rfq"] == 3` and `assert counts["quotation"] == 3` assertions; keep the distinct-count check only for the three unchanged types (PO=17, invoice=19, supplier_comparison=16)

2. **`test_zero_line_items_produces_single_row_tender` behavior**
   - What we know: With the new formatter, zero line items produces one data row with "Not found" in all 3 cells
   - What's unclear: Current test just checks `len(rows) == 2` — this behavior is preserved, so the test passes. But the test was written for the old schema where header fields filled the row. With the new schema the row will have only 3 cells, all "Not found".
   - Recommendation: Update the test to assert cell content (not just row count) matches the new 3-column "Not found" layout.

3. **Gemini extraction test coverage for stripped schemas**
   - What we know: Gemini is now given a schema with only `line_items` — it will no longer attempt to extract header fields
   - What's unclear: The existing Gemini extraction mock tests (`test_extraction.py`) mock the provider entirely so they pass regardless of schema changes. No live extraction test will break.
   - Recommendation: No test updates needed for extraction tests. The planner should note this as a "no-op" for that test file.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest + anyio (existing) |
| Config file | `pytest.ini` (existing) |
| Quick run command | `pytest tests/test_export.py -x -q` |
| Full suite command | `pytest -x -q` |

### Phase Requirements → Test Map

| Area | Behavior | Test Type | Automated Command | File Exists? |
|------|----------|-----------|-------------------|-------------|
| tender_rfq CSV columns | Only item_number, quantity, description | unit | `pytest tests/test_export.py::test_column_order_tender_rfq -x` | Update existing |
| quotation CSV columns | Only item_number, quantity, description | unit | `pytest tests/test_export.py::test_column_order_quotation -x` | Update existing |
| Zero items → "Not found" row | 1 data row with "Not found" | unit | `pytest tests/test_export.py::test_zero_line_items_produces_single_row_tender -x` | Update existing |
| Quantity normalization — unit suffix | "5 kg" → "5" | unit | `pytest tests/test_export.py::test_normalize_quantity_strips_unit_suffix -x` | New (Wave 0) |
| Quantity normalization — trailing .0 | "3.00" → "3" | unit | `pytest tests/test_export.py::test_normalize_quantity_strips_trailing_zero -x` | New (Wave 0) |
| Quantity normalization — non-integer | "3.5" → "3.5" | unit | `pytest tests/test_export.py::test_normalize_quantity_preserves_non_integer_float -x` | New (Wave 0) |
| Quantity normalization — unparseable | "N/A" → "N/A" | unit | `pytest tests/test_export.py::test_normalize_quantity_preserves_unparseable -x` | New (Wave 0) |
| MANDATORY_FIELDS tender/quotation empty | No warnings header | unit | `pytest tests/test_export.py -k "mandatory" -x` | Update existing |
| Frontend ReviewTable hidden | No ReviewTable for tender/quotation | unit | `npx vitest run --reporter=verbose` | New (Wave 0) |

### Sampling Rate

- **Per task commit:** `pytest tests/test_export.py -x -q`
- **Per wave merge:** `pytest -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] New quantity normalization test functions in `tests/test_export.py` (5 new test functions)
- [ ] Updated column-order test assertions in `tests/test_export.py` for tender_rfq and quotation
- [ ] Frontend test for ReviewTable conditional rendering in `frontend/src/App.test.tsx` or `ReviewTable.test.tsx` (if vitest coverage is desired)

## Sources

### Primary (HIGH confidence)

- Direct code read: `src/extraction/schemas/tender_rfq.py` — current TenderRFQResult with 8 header fields
- Direct code read: `src/extraction/schemas/quotation.py` — current QuotationResult with 12 header fields
- Direct code read: `src/export/formatters.py` — normalize_cell dispatch pattern, _format_line_item_type, MANDATORY_FIELDS
- Direct code read: `tests/test_export.py` — all existing test assertions for tender/quotation
- Direct code read: `frontend/src/App.tsx` — review phase rendering, ReviewTable placement
- Direct code read: `frontend/src/components/ReviewTable.tsx` — filters by lineItemKey, renders all other fields
- Direct code read: `frontend/src/components/LineItemsTable.tsx` — renders items array, derives columns from first item
- Direct code read: `src/llm/gemini.py` — EXTRACT_PROMPT passes schema as `response_schema`; schema change automatically narrows Gemini output
- Direct code read: `.planning/phases/08-.../08-CONTEXT.md` — all locked decisions

### Secondary (MEDIUM confidence)

- Pydantic v2 documentation (training knowledge, confirmed by existing usage pattern): extra fields are ignored in `model_validate()` by default; no `model_config = ConfigDict(extra='ignore')` is needed explicitly.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all files read directly; no external library research needed
- Architecture: HIGH — patterns derived from existing code, not speculation
- Pitfalls: HIGH — identified by tracing all call sites that reference tender_rfq/quotation schema fields
- Quantity normalization algorithm: HIGH — decision locked in CONTEXT.md; algorithm is straightforward regex + float comparison

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (stable internal codebase, no external dependencies changing)
