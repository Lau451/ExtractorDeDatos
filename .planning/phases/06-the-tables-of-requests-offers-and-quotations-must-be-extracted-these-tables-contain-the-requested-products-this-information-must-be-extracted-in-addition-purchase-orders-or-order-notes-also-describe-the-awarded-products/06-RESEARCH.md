# Phase 6: Product Table Extraction - Research

**Researched:** 2026-03-24
**Domain:** Pydantic schema extension, CSV formatter upgrade, frontend doc-type routing
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Tender/RFQ line item fields:** Add `line_items: list[TenderLineItem]` to `TenderRFQResult`. Fields: `item_number`, `quantity`, `description` — all `Optional[str]`.
- **Quotation line item fields:** Add `line_items: list[QuotationLineItem]` to `QuotationResult`. Same three fields as Tender/RFQ. No price fields in quotation line items — totals stay in header.
- **Purchase Order:** No changes. Existing `POLineItem` schema is sufficient.
- **CSV formatter:** Tender/RFQ and Quotation switch from header-only to denormalized line-item format — same layout as PO/Invoice. Documents with no extracted line items produce a single row (header fields, empty line item columns). This overrides the Phase 3 "header-only" decision for these two doc types.
- **Frontend:** Extend `DOC_TYPES_WITH_LINE_ITEMS` set and `LINE_ITEM_KEYS` map in existing files to include `tender_rfq` and `quotation`. Same `LineItemsTable` component, no new component needed.

### Claude's Discretion

- Pydantic model names for the new line item submodels (`TenderLineItem`, `QuotationLineItem`, or alternatives).
- Column header labels in CSV (human-readable vs field names). Existing pattern uses field names as column headers — maintain consistency.
- Whether to update `LINE_ITEM_KEYS` in `fieldLabels.ts` or add entries to `docTypes.ts` — implementation detail. Current code has `LINE_ITEM_KEYS` in `fieldLabels.ts` and `DOC_TYPES_WITH_LINE_ITEMS` in `docTypes.ts` — both need updating.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

## Summary

Phase 6 is a narrow retrofit that adds `line_items` table extraction to the two remaining header-only document types: Tender/RFQ and Quotation. The Purchase Order, Invoice, and Supplier Comparison types already have full line-item support — Phase 6 makes Tender/RFQ and Quotation consistent with them.

The change touches four layers: (1) Pydantic schemas — add a submodel and `line_items` field to each; (2) CSV formatters — switch from `_format_header_only_type()` to `_format_line_item_type()` for both; (3) Gemini extraction prompt — Gemini uses the Pydantic schema via `response_schema`, so schema changes automatically change what Gemini is asked to extract (no prompt string changes needed); (4) frontend — two constant updates to include the new doc types in the line-items rendering path.

All patterns are already proven in the codebase. This phase has no novel architecture — it is a pure extension of existing, working patterns. The primary planning concern is test coverage: existing `test_export.py` tests will break once the CSV column count for `tender_rfq` and `quotation` changes from 8 and 12 to 11 and 15 respectively. Those tests must be updated to reflect the new schemas.

**Primary recommendation:** Follow the `POLineItem` / `_format_line_item_type()` pattern exactly. No design decisions are required — the pattern is locked and proven.

---

## Standard Stack

No new dependencies. All stack components are already installed.

### Core (all pre-existing)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pydantic | v2 (in use) | Schema definition and Gemini `response_schema` serialization | Project-wide pattern, Gemini requires it |
| google-genai | 1.68.0 (in use) | LLM extraction via structured output | Project standard (NOT deprecated google-generativeai) |
| Python csv + io | stdlib | CSV byte generation with UTF-8-BOM | Phase 3 decision, RFC 4180 compliant |
| React + TypeScript | in use | Frontend rendering | Project standard |
| Vitest 4.x | ^4.1.1 | Frontend unit tests | Project standard |
| pytest (asyncio_mode=auto) | in use | Backend unit + integration tests | Project standard |

### Installation
```bash
# No new packages needed
```

---

## Architecture Patterns

### Recommended Project Structure (changes only)

```
src/extraction/schemas/
├── tender_rfq.py        # ADD TenderLineItem submodel + line_items field to TenderRFQResult
├── quotation.py         # ADD QuotationLineItem submodel + line_items field to QuotationResult
├── purchase_order.py    # UNCHANGED — reference pattern
└── registry.py          # UNCHANGED — no new types

src/export/
└── formatters.py        # CHANGE format_tender_rfq and format_quotation
                         #   from _format_header_only_type to _format_line_item_type

frontend/src/lib/
├── fieldLabels.ts       # ADD tender_rfq and quotation to LINE_ITEM_KEYS
└── docTypes.ts          # ADD tender_rfq and quotation to DOC_TYPES_WITH_LINE_ITEMS

tests/
└── test_export.py       # UPDATE SAMPLE_TENDER + SAMPLE_QUOTATION dicts to include line_items
                         # UPDATE test_column_order_tender_rfq and test_column_order_quotation
                         # UPDATE test_distinct_schemas column count assertions
```

### Pattern 1: Adding a Line Item Submodel (follow POLineItem exactly)

**What:** Define a Pydantic `BaseModel` subclass with `Optional[str]` fields only, then add a `list[SubModel]` field with `default_factory=list` to the parent result model.

**When to use:** Any time a new doc type needs line item extraction.

**Example (reference — purchase_order.py):**
```python
# Source: src/extraction/schemas/purchase_order.py (existing, proven pattern)
from pydantic import BaseModel, Field
from typing import Optional

class POLineItem(BaseModel):
    item_number: Optional[str] = Field(None, description="Line item number or sequence number")
    description: Optional[str] = Field(None, description="Product name or item description")
    sku: Optional[str] = Field(None, description="SKU, part number, or item code")
    quantity: Optional[str] = Field(None, description="Ordered quantity as a string to preserve formatting")
    unit: Optional[str] = Field(None, description="Unit of measure (each, kg, box, etc.)")
    unit_price: Optional[str] = Field(None, description="Price per unit in the document currency")
    extended_price: Optional[str] = Field(None, description="Line total = quantity × unit price")

class PurchaseOrderResult(BaseModel):
    # ... header fields ...
    line_items: list[POLineItem] = Field(default_factory=list, description="List of ordered line items")
```

**For Phase 6:** `TenderLineItem` and `QuotationLineItem` need only three fields: `item_number`, `quantity`, `description`.

### Pattern 2: Switching a Formatter from Header-Only to Line-Item

**What:** Replace the `_format_header_only_type(ModelClass, extraction_result)` call with `_format_line_item_type(ModelClass, LineItemClass, extraction_result)` in the public formatter function.

**Example (reference — existing format_purchase_order):**
```python
# Source: src/export/formatters.py (existing, proven pattern)
def format_purchase_order(extraction_result: dict) -> bytes:
    return _format_line_item_type(PurchaseOrderResult, POLineItem, extraction_result)

# Phase 6 target — change format_tender_rfq:
# BEFORE:
def format_tender_rfq(extraction_result: dict) -> bytes:
    return _format_header_only_type(TenderRFQResult, extraction_result)

# AFTER:
def format_tender_rfq(extraction_result: dict) -> bytes:
    return _format_line_item_type(TenderRFQResult, TenderLineItem, extraction_result)
```

The `_format_line_item_type` helper already handles: zero line items (single row, empty line-item cells), header field repetition per row, and None-to-empty-cell conversion.

### Pattern 3: Frontend Doc-Type Routing Extension

**What:** Two constant updates. No component changes needed.

**fieldLabels.ts — LINE_ITEM_KEYS (current):**
```typescript
// Source: frontend/src/lib/fieldLabels.ts (existing)
export const LINE_ITEM_KEYS: Record<string, string> = {
  purchase_order: 'line_items',
  invoice: 'line_items',
  supplier_comparison: 'line_items',
};
// Add: tender_rfq: 'line_items', quotation: 'line_items'
```

**docTypes.ts — DOC_TYPES_WITH_LINE_ITEMS (current):**
```typescript
// Source: frontend/src/lib/docTypes.ts (existing)
export const DOC_TYPES_WITH_LINE_ITEMS = new Set([
  'purchase_order',
  'invoice',
  'supplier_comparison',
]);
// Add: 'tender_rfq', 'quotation'
```

App.tsx uses `LINE_ITEM_KEYS[jobData.doc_type]` to determine the `lineItemKey` passed to `ReviewTable` (which excludes the key from header rendering) and uses `DOC_TYPES_WITH_LINE_ITEMS.has(jobData.doc_type)` as the guard for rendering `LineItemsTable`. Both must be updated.

### Anti-Patterns to Avoid

- **Using float/int field types in Pydantic submodels:** All line item fields must be `Optional[str]`. Non-string types cause Gemini `InvalidArgument` 400 errors. This is a locked Phase 2 decision.
- **Modifying `FORMATTER_REGISTRY`:** The registry auto-derives from function definitions. The keys `tender_rfq` and `quotation` already exist in `FORMATTER_REGISTRY` — only the function bodies change.
- **Modifying `registry.py`:** The schema registry already maps all five doc types. Adding `line_items` to the Pydantic models automatically changes what Gemini extracts via `response_schema`. No registry change needed.
- **Creating a new component for tender/quotation line items:** The `LineItemsTable` component is generic (accepts `items: Record<string, unknown>[]`). It renders any fields found in the first item object. No new component is needed.
- **Adding field labels for the new line item fields:** `item_number`, `quantity`, and `description` already exist in `FIELD_LABELS` in `fieldLabels.ts`. No new labels needed.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Line-item CSV formatting | Custom formatter | `_format_line_item_type()` | Already handles zero items, None cells, header repetition |
| Gemini schema prompt | Manually construct JSON schema | Pydantic model via `response_schema` | Already wired — schema changes propagate automatically |
| Frontend table rendering | New component | Existing `LineItemsTable` | It's generic — works for any `Record<string, unknown>[]` |
| Column ordering | Hardcoded list | `model_fields` iteration order | Phase 3 decision — Pydantic field declaration order drives CSV column order |

**Key insight:** Every mechanism needed for this phase already exists. The task is configuration and extension, not new construction.

---

## Common Pitfalls

### Pitfall 1: Forgetting to Update Both Frontend Constants

**What goes wrong:** Developer updates `LINE_ITEM_KEYS` but not `DOC_TYPES_WITH_LINE_ITEMS` (or vice versa). The `LineItemsTable` guard in `App.tsx` depends on `DOC_TYPES_WITH_LINE_ITEMS.has(...)` — if this is not updated, the table never renders even if `LINE_ITEM_KEYS` has the new doc type.

**Why it happens:** The two constants live in different files (`fieldLabels.ts` and `docTypes.ts`) and serve different roles. Both are required.

**How to avoid:** Update both constants in the same commit/task. Verify with a frontend test that `tender_rfq` and `quotation` render a `LineItemsTable`.

### Pitfall 2: Breaking Existing test_export.py Tests

**What goes wrong:** Existing tests assert specific column counts for `tender_rfq` (8) and `quotation` (12). After adding 3 line-item columns, the counts become 11 and 15. `test_distinct_schemas` also asserts all five doc types have unique column counts — this remains true but the assertion values change.

**Why it happens:** The test fixtures `SAMPLE_TENDER` and `SAMPLE_QUOTATION` don't include `line_items` keys, and column count assertions are hardcoded.

**How to avoid:** Update `SAMPLE_TENDER` and `SAMPLE_QUOTATION` to include `line_items: []` (empty list). Update column-count assertions in `test_column_order_tender_rfq`, `test_column_order_quotation`, and `test_distinct_schemas`. Also update `test_header_only_single_row` if it still applies to tender (with zero line items, behavior is the same as before — single data row — so the test may pass with minimal changes, but the description should be updated).

### Pitfall 3: CSV Column Order Mismatch with Schema Field Order

**What goes wrong:** Pydantic model field declaration order determines CSV column order (Phase 3 decision). If `line_items` is declared in the middle of the schema rather than at the end, header columns and line-item columns will interleave.

**Why it happens:** `_format_line_item_type` explicitly excludes `line_items` from header fields (`[f for f in model_class.model_fields if f != "line_items"]`) then appends item fields — so physical position in the model doesn't matter. But for consistency with PO and Invoice, `line_items` should be the last field declared.

**How to avoid:** Declare `line_items` as the last field in both `TenderRFQResult` and `QuotationResult`.

### Pitfall 4: PATCH /fields Endpoint and line_items Key

**What goes wrong:** When the frontend saves edits to tender/quotation line items, it calls `api.patchFields(jobId, { line_items: updatedItems })`. The backend `_deep_merge` must handle the `line_items` key in the patch dict. Since the key name is `line_items` for all doc types and `_deep_merge` is generic, this should work without changes — but worth verifying.

**How to avoid:** Confirm that `_deep_merge` in `src/api/routes/patch.py` (or equivalent) handles list replacement correctly for the new doc types. Since all three types use the same `line_items` key, the existing PATCH logic applies unchanged.

---

## Code Examples

### New TenderLineItem Submodel
```python
# To add at top of src/extraction/schemas/tender_rfq.py
class TenderLineItem(BaseModel):
    item_number: Optional[str] = Field(None, description="Line item number or sequence number")
    quantity: Optional[str] = Field(None, description="Requested quantity as a string")
    description: Optional[str] = Field(None, description="Product name or item description")
```

### Updated TenderRFQResult (add line_items as last field)
```python
class TenderRFQResult(BaseModel):
    tender_reference: Optional[str] = Field(None, description="Tender or RFQ reference number")
    issue_date: Optional[str] = Field(None, description="Date the tender was issued")
    issuing_organization: Optional[str] = Field(None, description="Organization issuing the tender")
    submission_deadline: Optional[str] = Field(None, description="Deadline for submitting responses")
    contact_person: Optional[str] = Field(None, description="Contact name for the tender")
    project_title: Optional[str] = Field(None, description="Project or scope title described in the tender")
    currency: Optional[str] = Field(None, description="Currency specified for bids")
    notes: Optional[str] = Field(None, description="Additional notes, conditions, or requirements")
    line_items: list[TenderLineItem] = Field(default_factory=list, description="List of requested line items")
```

### Updated format_tender_rfq in formatters.py
```python
# Import addition at top of formatters.py:
from src.extraction.schemas.tender_rfq import TenderRFQResult, TenderLineItem

# Function body change:
def format_tender_rfq(extraction_result: dict) -> bytes:
    """Format a TenderRFQ extraction result as CSV bytes."""
    return _format_line_item_type(TenderRFQResult, TenderLineItem, extraction_result)
```

### Updated SAMPLE_TENDER fixture in test_export.py
```python
SAMPLE_TENDER = {
    "tender_reference": "TND-001",
    "issue_date": "2024-01-05",
    "issuing_organization": "Gov Agency",
    "submission_deadline": "2024-02-05",
    "contact_person": "John Doe",
    "project_title": "Road Repair",
    "currency": "USD",
    "notes": "Urgent",
    "line_items": [
        {
            "item_number": "1",
            "quantity": "100",
            "description": "Asphalt mix",
        }
    ],
}
```

### Updated column count expectations in test_export.py
```python
# test_column_order_tender_rfq — expected columns after Phase 6:
expected = [
    "tender_reference", "issue_date", "issuing_organization",
    "submission_deadline", "contact_person", "project_title",
    "currency", "notes",
    "item_number", "quantity", "description",  # 3 new columns
]
assert len(rows[0]) == 11  # was 8

# test_column_order_quotation — expected columns after Phase 6:
expected = [
    "quote_number", "quote_date", "vendor_name", "vendor_address",
    "buyer_name", "valid_until", "currency", "subtotal", "tax_total",
    "grand_total", "payment_terms", "delivery_terms",
    "item_number", "quantity", "description",  # 3 new columns
]
assert len(rows[0]) == 15  # was 12

# test_distinct_schemas — updated counts:
assert counts["tender_rfq"] == 11   # was 8
assert counts["quotation"] == 15    # was 12
# 17, 19, 16, 11, 15 — all still distinct
```

### Updated Frontend Constants
```typescript
// frontend/src/lib/fieldLabels.ts — LINE_ITEM_KEYS addition:
export const LINE_ITEM_KEYS: Record<string, string> = {
  purchase_order: 'line_items',
  invoice: 'line_items',
  supplier_comparison: 'line_items',
  tender_rfq: 'line_items',    // ADD
  quotation: 'line_items',     // ADD
};

// frontend/src/lib/docTypes.ts — DOC_TYPES_WITH_LINE_ITEMS addition:
export const DOC_TYPES_WITH_LINE_ITEMS = new Set([
  'purchase_order',
  'invoice',
  'supplier_comparison',
  'tender_rfq',    // ADD
  'quotation',     // ADD
]);
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Tender/RFQ: header-only CSV | Denormalized line-item CSV | Phase 6 | CSV column count: 8 → 11 |
| Quotation: header-only CSV | Denormalized line-item CSV | Phase 6 | CSV column count: 12 → 15 |
| Frontend line items: PO + Invoice + SupplierComparison only | All five doc types | Phase 6 | `LineItemsTable` renders for tender/quotation too |

**Deprecated/outdated after Phase 6:**
- `test_header_only_single_row`: Test name and description are stale — tender_rfq will still produce a single row when `line_items` is empty, but it is no longer a "header-only" formatter. Rename the test.
- `_format_header_only_type` usage for `tender_rfq` and `quotation`: Both calls are replaced by `_format_line_item_type`.

---

## Open Questions

1. **`test_header_only_single_row` test fate**
   - What we know: This test uses `format_tender_rfq(SAMPLE_TENDER)` and asserts exactly 2 rows (header + 1 data). After Phase 6, with `SAMPLE_TENDER` containing one `line_items` entry, the result will be 3 rows (header + 1 data), breaking the assertion.
   - What's unclear: Should the test be renamed and updated to use an empty `line_items` list to test the zero-line-item fallback path, or removed entirely since `test_zero_line_items_single_row` covers that pattern for PO?
   - Recommendation: Update the test: set `line_items: []` in SAMPLE_TENDER for this specific test case, rename it `test_zero_line_items_produces_single_row_tender`, and assert the zero-line-item path.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework (backend) | pytest with asyncio_mode=auto |
| Config file (backend) | pyproject.toml |
| Quick run command | `pytest tests/test_export.py tests/test_extraction.py -x -q` |
| Full suite command | `pytest tests/ -x -q` |
| Framework (frontend) | Vitest ^4.1.1 |
| Config file (frontend) | frontend/vite.config.ts |
| Quick run command (frontend) | `cd frontend && npx vitest run --reporter=verbose` |

### Phase Requirements → Test Map

| Behavior | Test Type | Automated Command | File Exists? |
|----------|-----------|-------------------|-------------|
| TenderLineItem schema: 3 Optional[str] fields | unit | `pytest tests/test_extraction.py -x -q` | Partial — test_tender_extraction exists but doesn't assert line_items (update needed) |
| QuotationLineItem schema: 3 Optional[str] fields | unit | `pytest tests/test_extraction.py -x -q` | Partial — test_quotation_extraction exists but doesn't assert line_items (update needed) |
| format_tender_rfq: denormalized line-item CSV, correct columns | unit | `pytest tests/test_export.py::test_column_order_tender_rfq -x` | Yes (update column list + count) |
| format_quotation: denormalized line-item CSV, correct columns | unit | `pytest tests/test_export.py::test_column_order_quotation -x` | Yes (update column list + count) |
| format_tender_rfq: zero line items → single row | unit | `pytest tests/test_export.py -x -q` | Yes (update SAMPLE_TENDER fixture usage) |
| format_quotation: zero line items → single row | unit | `pytest tests/test_export.py -x -q` | Yes (update SAMPLE_QUOTATION fixture usage) |
| test_distinct_schemas: all 5 doc types distinct column counts | unit | `pytest tests/test_export.py::test_distinct_schemas -x` | Yes (update count assertions: 11, 15) |
| Frontend renders LineItemsTable for tender_rfq | unit/component | `cd frontend && npx vitest run` | No — Wave 0 gap |
| Frontend renders LineItemsTable for quotation | unit/component | `cd frontend && npx vitest run` | No — Wave 0 gap |

### Sampling Rate
- **Per task commit:** `pytest tests/test_export.py tests/test_extraction.py -x -q`
- **Per wave merge:** `pytest tests/ -x -q && cd frontend && npx vitest run`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] Frontend test for `tender_rfq` LineItemsTable rendering — new test in `frontend/src/components/LineItemsTable.test.tsx` or `ReviewTable.test.tsx`
- [ ] Frontend test for `quotation` LineItemsTable rendering

*(Existing backend test infrastructure covers all phase requirements — only updates to existing tests are needed, not new test files)*

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection: `src/extraction/schemas/purchase_order.py` — POLineItem pattern
- Direct code inspection: `src/export/formatters.py` — `_format_line_item_type` and `_format_header_only_type` helpers
- Direct code inspection: `frontend/src/lib/fieldLabels.ts` — `LINE_ITEM_KEYS` constant
- Direct code inspection: `frontend/src/lib/docTypes.ts` — `DOC_TYPES_WITH_LINE_ITEMS` constant
- Direct code inspection: `frontend/src/App.tsx` — line items rendering guard logic
- Direct code inspection: `tests/test_export.py` — all existing column count assertions

### Secondary (MEDIUM confidence)
- `.planning/phases/06-*/06-CONTEXT.md` — locked implementation decisions (gathered 2026-03-24)
- `.planning/STATE.md` — accumulated project decisions, especially Phase 2 Optional[str] rule and Phase 3 CSV layout

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; all patterns directly observed in codebase
- Architecture: HIGH — all patterns are direct copies/extensions of existing proven code
- Pitfalls: HIGH — all pitfalls derived from direct code inspection of tests and constants that will break

**Research date:** 2026-03-24
**Valid until:** 2026-04-24 (stable — no external dependencies change)
