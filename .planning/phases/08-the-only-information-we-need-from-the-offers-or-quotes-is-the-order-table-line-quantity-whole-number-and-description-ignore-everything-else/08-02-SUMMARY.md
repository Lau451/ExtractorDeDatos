---
phase: 08-offers-quotes-line-items-only
plan: 02
subsystem: frontend
tags: [ui, doc-types, conditional-rendering, vitest]
dependency_graph:
  requires: []
  provides: [LINE_ITEMS_ONLY_DOC_TYPES constant, ReviewTable conditional guard]
  affects: [frontend/src/App.tsx, frontend/src/lib/docTypes.ts]
tech_stack:
  added: []
  patterns: [Set membership guard for conditional JSX rendering, structural source-text vitest assertions]
key_files:
  created:
    - frontend/src/lib/docTypes.test.ts
  modified:
    - frontend/src/lib/docTypes.ts
    - frontend/src/App.tsx
decisions:
  - LINE_ITEMS_ONLY_DOC_TYPES as a Set<string> in docTypes.ts — single source of truth for which doc types skip header fields UI
  - Structural vitest assertions read App.tsx source text to verify guard placement — catches guard omission/inversion that tsc alone cannot detect
metrics:
  duration: 2 min
  completed: "2026-03-26"
  tasks_completed: 2
  files_changed: 3
requirements:
  - P8-FE-01
---

# Phase 8 Plan 02: Hide ReviewTable for tender_rfq and quotation Summary

Hide the ReviewTable (header fields section) for tender_rfq and quotation doc types using a Set-based guard in App.tsx, with vitest tests confirming membership correctness and structural guard placement.

## What Was Built

- `LINE_ITEMS_ONLY_DOC_TYPES = new Set(['tender_rfq', 'quotation'])` exported from `frontend/src/lib/docTypes.ts`
- `ReviewTable` in `App.tsx` wrapped in `{!LINE_ITEMS_ONLY_DOC_TYPES.has(jobData.doc_type ?? '') && (...)}` — hidden for tender/quotation, visible for all other types
- `frontend/src/lib/docTypes.test.ts` with 10 vitest tests: 7 unit membership tests + 3 structural source-text assertions

## Tasks Completed

| Task | Description | Commit |
|------|-------------|--------|
| 1 | Add LINE_ITEMS_ONLY_DOC_TYPES constant and guard ReviewTable rendering | 8d4ed19 |
| 2 | Add vitest tests verifying ReviewTable guard logic | 4ff498f |

## Verification

- `npx tsc --noEmit` — passes with zero errors
- `npx vitest run src/lib/docTypes.test.ts` — 10/10 tests pass
  - LINE_ITEMS_ONLY_DOC_TYPES includes tender_rfq and quotation
  - LINE_ITEMS_ONLY_DOC_TYPES excludes purchase_order, invoice, supplier_comparison
  - Set has exactly 2 members
  - All members are valid doc types
  - App.tsx contains `!LINE_ITEMS_ONLY_DOC_TYPES.has(` before ReviewTable
  - No ReviewTable occurrence without the guard
  - DocTypeBar is NOT guarded by LINE_ITEMS_ONLY_DOC_TYPES

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED

- frontend/src/lib/docTypes.ts — FOUND
- frontend/src/App.tsx — FOUND
- frontend/src/lib/docTypes.test.ts — FOUND
- Commit 8d4ed19 — FOUND
- Commit 4ff498f — FOUND
