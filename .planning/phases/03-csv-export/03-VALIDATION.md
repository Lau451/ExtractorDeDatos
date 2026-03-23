---
phase: 3
slug: csv-export
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-22
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `pytest.ini` or `pyproject.toml [tool.pytest]` |
| **Quick run command** | `pytest tests/test_export.py -x -q` |
| **Full suite command** | `pytest tests/ -x -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_export.py -x -q`
- **After every plan wave:** Run `pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| W0-test-stub | 01 | 0 | EXP-01..04, API-04 | unit stub | `pytest tests/test_export.py -x -q` | ❌ W0 | ⬜ pending |
| formatter-base | 01 | 1 | EXP-01, EXP-03 | unit | `pytest tests/test_export.py -x -q` | ❌ W0 | ⬜ pending |
| po-formatter | 01 | 1 | EXP-02, EXP-04 | unit | `pytest tests/test_export.py::test_purchase_order_csv -x -q` | ❌ W0 | ⬜ pending |
| invoice-formatter | 01 | 1 | EXP-02, EXP-04 | unit | `pytest tests/test_export.py::test_invoice_csv -x -q` | ❌ W0 | ⬜ pending |
| supplier-formatter | 01 | 1 | EXP-02, EXP-04 | unit | `pytest tests/test_export.py::test_supplier_comparison_csv -x -q` | ❌ W0 | ⬜ pending |
| tender-formatter | 01 | 1 | EXP-02, EXP-04 | unit | `pytest tests/test_export.py::test_tender_rfq_csv -x -q` | ❌ W0 | ⬜ pending |
| quotation-formatter | 01 | 1 | EXP-02, EXP-04 | unit | `pytest tests/test_export.py::test_quotation_csv -x -q` | ❌ W0 | ⬜ pending |
| export-route | 02 | 2 | API-04 | integration | `pytest tests/test_export.py::test_export_endpoint -x -q` | ❌ W0 | ⬜ pending |
| 409-gate | 02 | 2 | API-04 | integration | `pytest tests/test_export.py::test_export_409 -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_export.py` — stubs for EXP-01, EXP-02, EXP-03, EXP-04, API-04

*Existing infrastructure (`tests/conftest.py`, pytest, FastAPI test client) covers all other phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CSV opens without garbled characters in Excel | EXP-03 | Requires Excel or LibreOffice to verify BOM rendering | Open downloaded CSV in Excel; verify no `ï»¿` prefix; columns render correctly |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
