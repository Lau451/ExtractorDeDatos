---
phase: 08-offers-quotes-line-items-only
plan: 03
subsystem: testing
tags: [python, pytest, tdd, normalization, csv]

requires:
  - phase: 08-02
    provides: normalize_quantity function and test_export.py with initial quantity tests

provides:
  - Locale-aware normalize_quantity that distinguishes period-as-thousands-separator from decimal point
  - Full test coverage for European thousands-separator patterns (1.000, 10.000, 1.000.000)

affects: [export, formatters, csv-generation]

tech-stack:
  added: []
  patterns:
    - "TDD Red-Green: write failing tests first, then fix implementation"
    - "Regex alternative ordering: thousands-separator pattern matched before decimal pattern"

key-files:
  created: []
  modified:
    - src/export/formatters.py
    - tests/test_export.py

key-decisions:
  - "Thousands-separator heuristic: 1-3 leading digits followed by one or more .NNN groups — matches European convention without ambiguity"
  - "Regex alternative ordering: m_thousands checked before m_std — thousands pattern is unambiguous so first-match wins correctly"

patterns-established:
  - "Pattern: Use regex alternation ordering to resolve ambiguity — more specific pattern first"

requirements-completed: []

duration: 2min
completed: 2026-03-26
---

# Phase 08 Plan 03: Thousands-Separator Quantity Normalization Summary

**Locale-aware normalize_quantity using regex alternation to distinguish European thousands-separator (1.000 -> 1000) from decimal point (3.5 -> 3.5)**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-26T23:05:39Z
- **Completed:** 2026-03-26T23:07:30Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Fixed wrong assertion in test_normalize_quantity_strips_trailing_zero (100.000 is thousands, not trailing zeros)
- Added test_normalize_quantity_thousands_separator covering 1.000, 1.000 pcs, 1.000.000, 10.000 cases
- Replaced normalize_quantity with locale-aware version: thousands pattern matched first via `\d{1,3}(?:\.\d{3})+`, then standard decimal fallback

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix tests first (RED) — add thousands-separator cases and fix wrong assertion** - `cbf69f1` (test)
2. **Task 2: Fix normalize_quantity to handle thousands separators (GREEN)** - `5ed9e3d` (feat)

_Note: TDD tasks have two commits (test RED -> feat GREEN)_

## Files Created/Modified

- `src/export/formatters.py` - normalize_quantity rewritten with thousands-separator heuristic
- `tests/test_export.py` - Fixed wrong assertion on 100.000, added 4 new thousands-separator test cases

## Decisions Made

- Thousands-separator heuristic uses `\d{1,3}(?:\.\d{3})+` regex — 1-3 leading digits followed by one or more .NNN groups. This is unambiguous: no real decimal value has exactly 3 trailing digits in normal business quantities.
- Regex alternative ordering ensures thousands pattern is matched first — avoids decimal path swallowing ambiguous inputs.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - RED phase confirmed on first run, GREEN phase passed all 93 tests on first run.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- UAT gaps from 08-UAT.md (tests 3 and 4) are now closed
- All 93 tests pass with zero failures
- Phase 08 gap closure complete

---
*Phase: 08-offers-quotes-line-items-only*
*Completed: 2026-03-26*
