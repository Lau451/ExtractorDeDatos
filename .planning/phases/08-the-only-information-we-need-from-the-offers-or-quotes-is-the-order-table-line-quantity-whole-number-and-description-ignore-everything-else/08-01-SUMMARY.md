---
phase: 08-offers-quotes-line-items-only
plan: 01
subsystem: extraction-schemas + csv-export
tags: [schema, csv, normalization, tdd]
dependency_graph:
  requires: []
  provides: [3-column-tender-csv, 3-column-quotation-csv, quantity-normalization]
  affects: [src/extraction/schemas/tender_rfq.py, src/extraction/schemas/quotation.py, src/export/formatters.py]
tech_stack:
  added: []
  patterns: [TDD red-green, schema stripping, field-name dispatch normalization]
key_files:
  created: []
  modified:
    - src/extraction/schemas/tender_rfq.py
    - src/extraction/schemas/quotation.py
    - src/export/formatters.py
    - tests/test_export.py
    - tests/test_extraction.py
decisions:
  - TenderRFQResult and QuotationResult stripped to line_items only — header fields discarded at schema level, not at formatter level
  - normalize_quantity uses exact field-name match (_QUANTITY_FIELD_NAMES tuple) rather than substring, preventing false matches on fields like quantity_unit
  - MANDATORY_FIELDS for tender_rfq and quotation set to [] — no header fields to enforce
  - TenderRFQResult and QuotationResult no longer imported in formatters.py — only LineItem models needed
metrics:
  duration: 6 min
  completed_date: "2026-03-25"
  tasks_completed: 2
  files_modified: 5
---

# Phase 08 Plan 01: Strip Tender/Quotation Schemas to Line Items Only — Summary

**One-liner:** Stripped TenderRFQResult and QuotationResult to line_items-only, rewrote formatters to produce 3-column CSV (item_number, quantity, description), and added quantity normalization (unit suffix stripping + trailing .0 removal).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| RED | TDD failing tests for quantity normalization + 3-column layout | 278e216 | tests/test_export.py |
| 1 | Strip schemas + rewrite formatters + add quantity normalization | 72c45e9 | tender_rfq.py, quotation.py, formatters.py |
| 2 | Update test fixtures and assertions for 3-column layout | 5449cfe | tests/test_export.py, tests/test_extraction.py |

## What Was Built

- **TenderRFQResult**: Removed 8 header fields (tender_reference, issue_date, issuing_organization, submission_deadline, contact_person, project_title, currency, notes). Now contains only `line_items: list[TenderLineItem]`.
- **QuotationResult**: Removed 12 header fields (quote_number, quote_date, vendor_name, vendor_address, buyer_name, valid_until, currency, subtotal, tax_total, grand_total, payment_terms, delivery_terms). Now contains only `line_items: list[QuotationLineItem]`.
- **formatters.py**: Added `_QUANTITY_FIELD_NAMES`, `_is_quantity_field()`, `normalize_quantity()`, `_format_line_items_only()`. Updated `format_tender_rfq` and `format_quotation` to use the new helper. Updated `MANDATORY_FIELDS` to `[]` for both types. Removed unused `TenderRFQResult` and `QuotationResult` imports.
- **tests/test_export.py**: Updated SAMPLE_TENDER and SAMPLE_QUOTATION fixtures, updated column order and count assertions, updated distinct_schemas test, updated zero-items and line-item row tests. Added 11 new test functions covering quantity normalization, 3-column output, and mandatory fields contract.
- **tests/test_extraction.py**: Rewrote test_tender_extraction and test_quotation_extraction to reflect stripped schemas (line_items only).

## Verification

- `pytest tests/test_export.py`: 49 passed
- `pytest` (full suite): 92 passed, 0 failed
- Manual: `tender: columns=['item_number', 'quantity', 'description'], data=['1', '5', 'Test']`
- Manual: `quotation: columns=['item_number', 'quantity', 'description'], data=['1', '10', 'Item']`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test_extraction.py tests that referenced removed header fields**
- **Found during:** Task 2 verification (full pytest run)
- **Issue:** `test_tender_extraction` and `test_quotation_extraction` in tests/test_extraction.py created TenderRFQResult/QuotationResult with header fields (e.g., `tender_reference="RFQ-2024-0312"`) and asserted on those fields. After schema stripping, Pydantic raised `AttributeError: 'TenderRFQResult' object has no attribute 'tender_reference'`.
- **Fix:** Rewrote both tests to use line_items-only constructor matching the new schema contract. Assertions now verify `line_items` list structure and line item fields.
- **Files modified:** tests/test_extraction.py
- **Commit:** 5449cfe

## Self-Check: PASSED

All 5 modified files exist on disk. All 3 task commits verified in git history. Full test suite: 92 passed, 0 failed.
