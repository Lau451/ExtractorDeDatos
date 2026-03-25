---
phase: 7
slug: csv-export-rules-enforcement
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-24
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (asyncio_mode=auto, pyproject.toml) |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `pytest tests/test_export.py -x -q` |
| **Full suite command** | `pytest tests/ -q` |
| **Estimated runtime** | ~10 seconds |

Frontend:
| Property | Value |
|----------|-------|
| **Framework** | Vitest + jsdom (vite.config.ts) |
| **Config file** | `frontend/vite.config.ts` |
| **Quick run command** | `cd frontend && npx vitest run --reporter=verbose` |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_export.py -x -q`
- **After every plan wave:** Run `pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | normalize_cell None→"Not found" | unit | `pytest tests/test_export.py::test_normalize_none_is_not_found -x` | ❌ W0 | ⬜ pending |
| 07-01-02 | 01 | 1 | Amount normalization | unit | `pytest tests/test_export.py::test_normalize_amount_fields -x` | ❌ W0 | ⬜ pending |
| 07-01-03 | 01 | 1 | Date normalization DD/MM/YYYY | unit | `pytest tests/test_export.py::test_normalize_date_fields -x` | ❌ W0 | ⬜ pending |
| 07-01-04 | 01 | 1 | Unparseable amount fallback | unit | `pytest tests/test_export.py::test_normalize_amount_fallback -x` | ❌ W0 | ⬜ pending |
| 07-01-05 | 01 | 1 | Unparseable date fallback | unit | `pytest tests/test_export.py::test_normalize_date_fallback -x` | ❌ W0 | ⬜ pending |
| 07-01-06 | 01 | 1 | Text whitespace stripping | unit | `pytest tests/test_export.py::test_normalize_text_whitespace -x` | ❌ W0 | ⬜ pending |
| 07-01-07 | 01 | 1 | Formatter uses normalization | unit | `pytest tests/test_export.py::test_formatter_normalization_applied -x` | ❌ W0 | ⬜ pending |
| 07-02-01 | 02 | 1 | Export filename convention | integration | `pytest tests/test_export.py::test_export_filename_convention -x` | ❌ W0 | ⬜ pending |
| 07-02-02 | 02 | 1 | X-Export-Warnings header | integration | `pytest tests/test_export.py::test_export_warnings_header -x` | ❌ W0 | ⬜ pending |
| 07-02-03 | 02 | 1 | HTTP 200 with missing mandatory fields | integration | `pytest tests/test_export.py::test_export_warnings_still_200 -x` | ❌ W0 | ⬜ pending |
| 07-02-04 | 02 | 1 | No warnings when complete | integration | `pytest tests/test_export.py::test_export_no_warnings_when_complete -x` | ❌ W0 | ⬜ pending |
| 07-02-05 | 02 | 1 | Existing test updated | unit | `pytest tests/test_export.py::test_none_values_are_not_found -x` | Modify existing | ⬜ pending |
| 07-03-01 | 03 | 2 | Frontend warning toast | unit (Vitest) | `cd frontend && npx vitest run src/App.test.tsx` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_export.py` — New test functions for `normalize_cell` unit tests
- [ ] `tests/test_export.py` — New integration tests for filename convention and `X-Export-Warnings` header
- [ ] `tests/test_export.py` — Update `test_none_values_are_empty_cells` → rename and assert `"Not found"`
- [ ] `frontend/src/App.test.tsx` — Vitest test for warning state in `handleDownloadCSV`

*No new test infrastructure required — pytest + Vitest are already configured.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CORS expose_headers works in browser | X-Export-Warnings readable | Browser CORS policy enforcement | 1. Start dev server 2. Click Download CSV with missing fields 3. Verify warning toast appears |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
