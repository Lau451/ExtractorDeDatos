---
phase: 6
slug: product-table-extraction
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-24
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework (backend)** | pytest with asyncio_mode=auto |
| **Config file (backend)** | pyproject.toml |
| **Quick run command** | `pytest tests/test_export.py tests/test_extraction.py -x -q` |
| **Full suite command** | `pytest tests/ -x -q && cd frontend && npx vitest run --reporter=verbose` |
| **Framework (frontend)** | Vitest ^4.1.1 |
| **Config file (frontend)** | frontend/vite.config.ts |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_export.py tests/test_extraction.py -x -q`
- **After every plan wave:** Run `pytest tests/ -x -q && cd frontend && npx vitest run --reporter=verbose`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | EXT-02 | unit | `pytest tests/test_extraction.py -x -q` | Partial (update) | ⬜ pending |
| 06-01-02 | 01 | 1 | EXT-03 | unit | `pytest tests/test_extraction.py -x -q` | Partial (update) | ⬜ pending |
| 06-02-01 | 02 | 1 | EXT-02 | unit | `pytest tests/test_export.py::test_column_order_tender_rfq -x` | ✅ (update) | ⬜ pending |
| 06-02-02 | 02 | 1 | EXT-03 | unit | `pytest tests/test_export.py::test_column_order_quotation -x` | ✅ (update) | ⬜ pending |
| 06-03-01 | 03 | 2 | EXT-02/03 | unit | `cd frontend && npx vitest run --reporter=verbose` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/src/components/LineItemsTable.test.tsx` — test that `tender_rfq` and `quotation` render line items table
- [ ] Update `tests/test_export.py` fixtures — add `line_items` to `SAMPLE_TENDER` and `SAMPLE_QUOTATION`

*Existing backend test infrastructure covers most phase requirements — updates to existing tests plus one new frontend test.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Gemini extracts line items from real tender PDF | EXT-02 | Requires LLM call with real document | Upload a tender PDF, verify `line_items` populated in extraction result |
| Gemini extracts line items from real quotation PDF | EXT-03 | Requires LLM call with real document | Upload a quotation PDF, verify `line_items` populated in extraction result |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
