---
phase: 8
slug: offers-quotes-line-items-only
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + anyio (existing) |
| **Config file** | `pytest.ini` (existing) |
| **Quick run command** | `pytest tests/test_export.py -x -q` |
| **Full suite command** | `pytest -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_export.py -x -q`
- **After every plan wave:** Run `pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 1 | tender_rfq CSV columns | unit | `pytest tests/test_export.py::test_column_order_tender_rfq -x` | Update existing | ⬜ pending |
| 08-01-02 | 01 | 1 | quotation CSV columns | unit | `pytest tests/test_export.py::test_column_order_quotation -x` | Update existing | ⬜ pending |
| 08-01-03 | 01 | 1 | Zero items → "Not found" row | unit | `pytest tests/test_export.py::test_zero_line_items_produces_single_row_tender -x` | Update existing | ⬜ pending |
| 08-01-04 | 01 | 1 | Quantity norm — unit suffix | unit | `pytest tests/test_export.py::test_normalize_quantity_strips_unit_suffix -x` | New (Wave 0) | ⬜ pending |
| 08-01-05 | 01 | 1 | Quantity norm — trailing .0 | unit | `pytest tests/test_export.py::test_normalize_quantity_strips_trailing_zero -x` | New (Wave 0) | ⬜ pending |
| 08-01-06 | 01 | 1 | Quantity norm — non-integer | unit | `pytest tests/test_export.py::test_normalize_quantity_preserves_non_integer_float -x` | New (Wave 0) | ⬜ pending |
| 08-01-07 | 01 | 1 | Quantity norm — unparseable | unit | `pytest tests/test_export.py::test_normalize_quantity_preserves_unparseable -x` | New (Wave 0) | ⬜ pending |
| 08-01-08 | 01 | 1 | MANDATORY_FIELDS empty | unit | `pytest tests/test_export.py -k "mandatory" -x` | Update existing | ⬜ pending |
| 08-02-01 | 02 | 1 | Frontend ReviewTable hidden | unit | `npx vitest run --reporter=verbose` | New (Wave 0) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] New quantity normalization test functions in `tests/test_export.py` (4 new test functions)
- [ ] Updated column-order test assertions in `tests/test_export.py` for tender_rfq and quotation
- [ ] Frontend test for ReviewTable conditional rendering (if vitest coverage is desired)

*Existing infrastructure covers framework installation — pytest and vitest already configured.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual layout of review table | Frontend ReviewTable hidden for tender/quotation | Visual rendering check | Upload a tender PDF, verify review shows only line items table, no header fields section |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
