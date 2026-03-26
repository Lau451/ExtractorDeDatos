---
phase: 08-offers-quotes-line-items-only
verified: 2026-03-26T23:30:00Z
status: passed
score: 5/5 must-haves verified
re_verification: true
  previous_status: passed
  previous_score: 5/5
  gaps_closed:
    - "Period-as-thousands-separator quantities like '1.000' normalize to '1000', not '1'"
    - "Period-as-thousands-separator with unit suffix like '1.000 pcs' normalizes to '1000'"
    - "Multi-group thousands like '1.000.000' normalizes to '1000000'"
    - "Existing wrong assertion on '100.000' fixed to expect '100000'"
  gaps_remaining: []
  regressions: []
---

# Phase 8: Offers/Quotes Line Items Only — Verification Report

**Phase Goal:** Narrow tender/RFQ and quotation document types to line items only — strip all header fields from schemas, produce 3-column CSV (item_number, quantity, description), add quantity normalization (including thousands-separator handling), and hide ReviewTable in frontend for these types.
**Verified:** 2026-03-26T23:30:00Z
**Status:** passed
**Re-verification:** Yes — after gap closure (plan 08-03 fixed thousands-separator handling in normalize_quantity)

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | Tender/RFQ and quotation CSVs produce exactly 3 columns: item_number, quantity, description | VERIFIED | `format_tender_rfq` and `format_quotation` both call `_format_line_items_only(TenderLineItem / QuotationLineItem, ...)`. `TenderLineItem` and `QuotationLineItem` each have exactly 3 model fields. Tests `test_column_order_tender_rfq` and `test_column_order_quotation` assert `rows[0] == ["item_number", "quantity", "description"]` and `len(rows[0]) == 3`. 50 tests in test_export.py pass. |
| 2 | Quantity values are normalized: unit suffixes stripped, trailing .0 stripped, non-integer floats preserved, AND period-as-thousands-separator handled correctly | VERIFIED | `normalize_quantity()` in `formatters.py` (lines 80-97) uses regex alternation: `\d{1,3}(?:\.\d{3})+` matched first (thousands), then `\d+(?:\.\d+)?` (decimal). Direct checks: "1.000"→"1000", "1.000 pcs"→"1000", "1.000.000"→"1000000", "10.000"→"10000", "100.000"→"100000", "3.00"→"3", "5.0"→"5", "3.5"→"3.5", "5 kg"→"5". All 10 pass. |
| 3 | Zero line items produces one data row with "Not found" in all 3 cells | VERIFIED | `_format_line_items_only` handles empty `raw_line_items`. Tests `test_zero_line_items_produces_single_row_tender` and `test_zero_line_items_produces_single_row_quotation` pass. |
| 4 | Frontend hides ReviewTable (header fields section) for tender_rfq and quotation doc types | VERIFIED | `App.tsx` line 167: `{!LINE_ITEMS_ONLY_DOC_TYPES.has(jobData.doc_type ?? '') && (<ReviewTable .../>)}`. `LINE_ITEMS_ONLY_DOC_TYPES = new Set(['tender_rfq', 'quotation'])` in `docTypes.ts`. 10/10 vitest tests pass. |
| 5 | All other doc types (purchase_order, invoice, supplier_comparison) are completely unchanged | VERIFIED | `format_purchase_order`, `format_invoice`, `format_supplier_comparison` still call `_format_line_item_type`. `test_distinct_schemas` asserts purchase_order=17 cols, invoice=19 cols, supplier_comparison=16 cols. Full pytest suite: 93 passed, 0 failed. |

**Score:** 5/5 truths verified

---

## Gap Closure Verification (Plan 08-03)

### Must-Haves from 08-03-PLAN.md Frontmatter

| Truth | Status | Evidence |
|-------|--------|---------|
| "1.000" normalizes to "1000", not "1" | VERIFIED | `normalize_cell("quantity", "1.000")` returns `"1000"`. Thousands regex `\d{1,3}(?:\.\d{3})+` matches before decimal path. |
| "1.000 pcs" normalizes to "1000" | VERIFIED | `normalize_cell("quantity", "1.000 pcs")` returns `"1000"`. Thousands match strips period, unit suffix left behind the numeric match boundary. |
| "1.000.000" normalizes to "1000000" | VERIFIED | `normalize_cell("quantity", "1.000.000")` returns `"1000000"`. Multi-group `(?:\.\d{3})+` greedily matches both `.000` groups. |
| "5.0" and "3.00" still collapse to "5" and "3" | VERIFIED | Single/two-digit fractional parts fall through to decimal path. `float(5.0) == int(5.0)` → `"5"`. Confirmed by direct execution. |
| "3.5" and "2.75" preserved as-is | VERIFIED | Non-integer decimals returned unchanged by decimal path. Confirmed by direct execution. |

### Artifact: src/export/formatters.py

`normalize_quantity` (lines 80-97) contains the two-stage regex approach exactly as specified in the plan:
- Line 83: `m_thousands = re.match(r"^(\d{1,3}(?:\.\d{3})+)", stripped)`
- Line 85: `return m_thousands.group(1).replace(".", "")`
- Line 87: `m_std = re.match(r"^(\d+(?:\.\d+)?)", stripped)`

### Artifact: tests/test_export.py

New test function `test_normalize_quantity_thousands_separator` (lines 598-602) added:
- `normalize_cell("quantity", "1.000") == "1000"`
- `normalize_cell("quantity", "1.000 pcs") == "1000"`
- `normalize_cell("quantity", "1.000.000") == "1000000"`
- `normalize_cell("quantity", "10.000") == "10000"`

Fixed assertion in `test_normalize_quantity_strips_trailing_zero` (line 595):
- Was: `assert normalize_cell("quantity", "100.000") == "100"` (wrong — this is thousands, not trailing zeros)
- Now: `assert normalize_cell("quantity", "100.000") == "100000"` (correct)

---

## Required Artifacts (Full Phase)

### Plan 01 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/extraction/schemas/tender_rfq.py` | TenderRFQResult with ONLY line_items field | VERIFIED | `TenderRFQResult` has exactly one field: `line_items: list[TenderLineItem]`. All header fields absent. |
| `src/extraction/schemas/quotation.py` | QuotationResult with ONLY line_items field | VERIFIED | `QuotationResult` has exactly one field: `line_items: list[QuotationLineItem]`. All header fields absent. |
| `src/export/formatters.py` | `_format_line_items_only`, `normalize_quantity`, `_is_quantity_field`, `_QUANTITY_FIELD_NAMES`, MANDATORY_FIELDS updated | VERIFIED | All constructs confirmed present. `normalize_quantity` now locale-aware (thousands vs. decimal). |
| `tests/test_export.py` | Quantity normalization tests including thousands-separator coverage | VERIFIED | `test_normalize_quantity_thousands_separator` added; wrong assertion on "100.000" fixed. 50 tests pass. |

### Plan 02 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `frontend/src/lib/docTypes.ts` | `LINE_ITEMS_ONLY_DOC_TYPES` constant exported | VERIFIED | `export const LINE_ITEMS_ONLY_DOC_TYPES = new Set(['tender_rfq', 'quotation']);` |
| `frontend/src/App.tsx` | Conditional ReviewTable rendering based on doc type | VERIFIED | Guard at line 167. DocTypeBar, LineItemsTable, Download CSV unguarded. |
| `frontend/src/lib/docTypes.test.ts` | Vitest tests verifying LINE_ITEMS_ONLY_DOC_TYPES membership and App.tsx guard | VERIFIED | 10 tests pass. |

### Plan 03 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/export/formatters.py` | Locale-aware normalize_quantity distinguishing thousands from decimals | VERIFIED | Two-stage regex at lines 83 and 87. Thousands pattern matched first. Direct execution confirms all 10 normalization cases. |
| `tests/test_export.py` | Test coverage for thousands-separator patterns containing "1.000" | VERIFIED | `test_normalize_quantity_thousands_separator` contains 4 assertions. Wrong assertion on "100.000" fixed. |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/export/formatters.py` | `src/extraction/schemas/tender_rfq.py` | `from src.extraction.schemas.tender_rfq import TenderLineItem` | WIRED | Import confirmed. `TenderLineItem` used in `format_tender_rfq`. |
| `src/export/formatters.py` | `src/extraction/schemas/quotation.py` | `from src.extraction.schemas.quotation import QuotationLineItem` | WIRED | Import confirmed. `QuotationLineItem` used in `format_quotation`. |
| `normalize_cell` | `normalize_quantity` | `_is_quantity_field` dispatch in `normalize_cell` | WIRED | `if _is_quantity_field(field_name): return normalize_quantity(s)` confirmed in formatters.py. |
| `frontend/src/App.tsx` | `frontend/src/lib/docTypes.ts` | `import { LINE_ITEMS_ONLY_DOC_TYPES }` | WIRED | Import confirmed at App.tsx line 14. `LINE_ITEMS_ONLY_DOC_TYPES.has(...)` called at line 167. |
| `tests/test_export.py` | `src/export/formatters.py` | `normalize_cell` calling `normalize_quantity` for quantity fields | WIRED | `test_normalize_quantity_thousands_separator` calls `normalize_cell("quantity", ...)` which dispatches to `normalize_quantity`. 93/93 tests pass. |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| P8-SCHEMA-01 | 08-01-PLAN.md | Strip TenderRFQResult and QuotationResult to line_items only | SATISFIED | Both schemas have exactly one field (`line_items`). Header fields removed. |
| P8-CSV-01 | 08-01-PLAN.md | Produce 3-column CSV (item_number, quantity, description) for tender_rfq and quotation | SATISFIED | `_format_line_items_only` helper produces 3-column output. Tests assert column count == 3. |
| P8-NORM-01 | 08-01-PLAN.md | Normalize quantity field: strip unit suffixes, strip trailing .0, preserve non-integer floats, handle thousands-separator | SATISFIED | `normalize_quantity()` implements all four rules. 6 quantity normalization test functions cover all cases including thousands separator. |
| P8-FE-01 | 08-02-PLAN.md | Hide ReviewTable for tender_rfq and quotation doc types in frontend review phase | SATISFIED | Guard at App.tsx line 167. 10/10 vitest tests pass. |

---

## Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| None | — | — | — |

Scan performed on all 5 modified files across plans 01-03. No TODO/FIXME/placeholder comments, no empty return stubs, no console.log-only handlers found.

---

## Human Verification Required

### 1. ReviewTable hidden in live UI for tender/quotation

**Test:** Upload a real tender or RFQ document. Observe the review phase.
**Expected:** Only LineItemsTable and Download CSV button appear — no header fields section (ReviewTable) rendered above the line items.
**Why human:** Conditional JSX rendering is structurally verified by vitest source-text assertions, but actual DOM rendering depends on the full React render tree and runtime doc_type values from the API.

### 2. Quantity normalization in end-to-end extraction with European thousands

**Test:** Upload a tender document where an LLM-extracted quantity uses European thousands-separator notation (e.g., "1.000" meaning one thousand, or "10.000" meaning ten thousand). Download the CSV.
**Expected:** CSV quantity cell shows "1000" and "10000" respectively, not "1" and "10".
**Why human:** LLM extraction output format is non-deterministic; can only confirm normalization fires correctly on real European-locale documents via live test.

---

## Gaps Summary

No gaps. All 5 observable truths verified across plans 01-03. All 9 artifacts substantive and wired. All 5 key links confirmed. All 4 phase requirement IDs satisfied.

Plan 08-03 gap closure fully effective:
- `normalize_quantity` now uses two-stage regex: `\d{1,3}(?:\.\d{3})+` (thousands, matched first) then `\d+(?:\.\d+)?` (decimal)
- All 10 normalization edge cases confirmed correct by direct Python execution
- 93 backend tests pass (0 failed), up from 92 in the initial phase verification (1 new thousands-separator test function added)
- No regressions in other doc types

---

_Verified: 2026-03-26T23:30:00Z_
_Verifier: Claude (gsd-verifier)_
