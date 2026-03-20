---
phase: 02-extraction-pipeline
plan: "02"
subsystem: testing
tags: [pytest, pytest-asyncio, fixtures, xfail, AsyncMock, procurement, markdown]

requires:
  - phase: 02-extraction-pipeline/02-01
    provides: Pydantic schemas and architecture patterns defined in research docs

provides:
  - Five markdown fixtures in tests/fixtures/ simulating Docling output for PO, invoice, tender/RFQ, quotation, and supplier comparison documents
  - tests/test_extraction.py with 13 xfail stubs covering CLS-01, CLS-02, EXT-01 through EXT-10
  - tests/test_doc_type_override.py with 3 xfail stubs covering CLS-03 override and re-extraction flow
  - Behavioral contracts that Plans 03 and 04 must satisfy (remove xfail and make pass)

affects: [02-extraction-pipeline/02-03, 02-extraction-pipeline/02-04]

tech-stack:
  added: []
  patterns:
    - "xfail stubs: all tests marked @pytest.mark.xfail(reason='Implementation not yet created') — suite stays green before implementation"
    - "AsyncMock pattern: all LLM calls mocked with unittest.mock.AsyncMock — no real Gemini API calls in tests"
    - "Fixture loader: load_fixture(name) helper reads from tests/fixtures/ dir by name"
    - "Fleshed-out stubs: comments converted to real assertion logic so Plans 03/04 can remove xfail and pass immediately"

key-files:
  created:
    - tests/fixtures/sample_po.md
    - tests/fixtures/sample_invoice.md
    - tests/fixtures/sample_tender.md
    - tests/fixtures/sample_quotation.md
    - tests/fixtures/sample_supplier_comparison.md
    - tests/test_extraction.py
    - tests/test_doc_type_override.py
  modified: []

key-decisions:
  - "Test stubs fleshed out with real assertion logic (not just raise NotImplementedError comments) so Plans 03/04 can remove xfail markers and have passing tests immediately"
  - "All 16 test stubs remain xfail — suite exits 0, existing 15 passing tests unaffected"

patterns-established:
  - "Wave 0 fixtures pattern: markdown files in tests/fixtures/ simulate Docling output; tests load them via load_fixture() helper"
  - "xfail contract pattern: stub defines WHAT to test; implementation plan removes xfail and makes it pass"

requirements-completed:
  - CLS-01
  - CLS-03

duration: 2min
completed: 2026-03-19
---

# Phase 02 Plan 02: Test Fixtures and Scaffolds Summary

**Five Docling-simulating markdown fixtures and 16 fleshed-out xfail test stubs covering all Phase 2 extraction requirements (CLS-01/02/03, EXT-01 through EXT-10)**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-19T20:03:49Z
- **Completed:** 2026-03-19T20:06:00Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Created 5 markdown fixture files simulating realistic Docling-processed procurement documents with field values matching the Pydantic schemas
- Created tests/test_extraction.py with 13 xfail stubs covering classification (CLS-01, CLS-02) and all 5 extraction schemas with line item tests (EXT-01 through EXT-10)
- Created tests/test_doc_type_override.py with 3 xfail stubs covering the PATCH override + re-extraction flow (CLS-03)
- Full test suite passes: 15 passed, 16 xfailed, 0 failures — no regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Create markdown test fixtures for all 5 document types** - `c6b54dd` (feat)
2. **Task 2: Create test scaffolds for extraction and doc_type override** - `a1aa01d` (feat)

## Files Created/Modified

- `tests/fixtures/sample_po.md` - Purchase order fixture with PO-2024-0847, 3 line items, header fields
- `tests/fixtures/sample_invoice.md` - Invoice fixture with INV-2024-1523, 2 line items, subtotal/tax/total
- `tests/fixtures/sample_tender.md` - Tender/RFQ fixture with RFQ-2024-0312, scope of work section
- `tests/fixtures/sample_quotation.md` - Quotation fixture with QT-2024-0198, pricing summary
- `tests/fixtures/sample_supplier_comparison.md` - Supplier comparison with 3-supplier evaluation table and scores
- `tests/test_extraction.py` - 13 xfail test stubs: 2 classify, 1 doc_type visibility, 10 extraction (header + line items for all types)
- `tests/test_doc_type_override.py` - 3 xfail test stubs: override triggers re-extraction, invalid type returns 422, unknown not allowed

## Decisions Made

- Test stubs were fleshed out with real assertion logic rather than just `raise NotImplementedError` comments. This means Plans 03 and 04 only need to remove the `@pytest.mark.xfail` decorator — the assertions are already correct and will pass once implementation exists.
- The `test_gemini_provider_uses_correct_sdk` test uses `inspect.getsource()` to assert that `google-genai` is used (not `google-generativeai`) — a static analysis approach that catches import errors without needing a live API.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All Wave 0 test infrastructure is in place: 5 fixtures + 2 test files with 16 behavioral contracts
- Plans 03 (LLM provider + extraction schemas) and 04 (API endpoints) can now be implemented — remove xfail markers as each feature is built
- Existing test suite unbroken: 15 passing tests remain green

---
*Phase: 02-extraction-pipeline*
*Completed: 2026-03-19*
