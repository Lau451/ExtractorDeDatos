---
phase: 06-product-table-extraction
plan: 02
subsystem: frontend
tags: [frontend, constants, line-items, tender-rfq, quotation, vitest]
dependency_graph:
  requires: []
  provides:
    - LINE_ITEM_KEYS with tender_rfq and quotation entries
    - DOC_TYPES_WITH_LINE_ITEMS with tender_rfq and quotation entries
    - Automated tests for P6-FE-01 and P6-FE-02
  affects:
    - frontend/src/App.tsx (routing guard now allows tender_rfq and quotation to render LineItemsTable)
tech_stack:
  added: []
  patterns:
    - TDD RED/GREEN for constant updates
    - Vitest for TypeScript constant verification
key_files:
  created:
    - frontend/src/components/LineItemsTable.test.tsx
  modified:
    - frontend/src/lib/fieldLabels.ts
    - frontend/src/lib/docTypes.ts
decisions:
  - "tender_rfq and quotation both map to 'line_items' key matching existing purchase_order/invoice/supplier_comparison pattern — no structural divergence"
metrics:
  duration: 1 min
  completed: 2026-03-24
  tasks_completed: 2
  files_changed: 3
---

# Phase 06 Plan 02: Frontend LINE_ITEM_KEYS and DOC_TYPES_WITH_LINE_ITEMS Extension Summary

**One-liner:** Extended two frontend constants to route tender_rfq and quotation through the LineItemsTable rendering path, with 4 Vitest tests proving the constants are correctly configured.

## What Was Built

Added `tender_rfq` and `quotation` to `LINE_ITEM_KEYS` (in `fieldLabels.ts`) and `DOC_TYPES_WITH_LINE_ITEMS` (in `docTypes.ts`). These two constants serve as the routing guard in `App.tsx` — `DOC_TYPES_WITH_LINE_ITEMS.has(jobData.doc_type)` gates whether `LineItemsTable` renders, and `LINE_ITEM_KEYS[jobData.doc_type]` tells it which key in the extraction result holds the items array.

Before this plan, tender/quotation documents would complete extraction (once Plan 01 ships the backend) but the frontend would silently skip rendering the line items table. After this plan, both doc types are routed correctly.

A new test file (`LineItemsTable.test.tsx`) provides non-vacuous automated verification: 4 tests assert the specific constant values rather than testing component rendering, making them fast and deterministic.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 0 | Create LineItemsTable test file (RED phase) | 15c3266 | frontend/src/components/LineItemsTable.test.tsx |
| 1 | Update LINE_ITEM_KEYS and DOC_TYPES_WITH_LINE_ITEMS | b8ea570 | frontend/src/lib/fieldLabels.ts, frontend/src/lib/docTypes.ts |

## Verification Results

```
Test Files  4 passed (4)
     Tests  22 passed (22)
  Start at  18:46:08
  Duration  1.40s
```

All 4 new LineItemsTable tests pass. No regressions in 18 pre-existing tests.

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED

- frontend/src/components/LineItemsTable.test.tsx: FOUND
- frontend/src/lib/fieldLabels.ts (tender_rfq entry): FOUND at line 75
- frontend/src/lib/docTypes.ts (tender_rfq entry): FOUND at line 5
- Commit 15c3266: FOUND
- Commit b8ea570: FOUND
