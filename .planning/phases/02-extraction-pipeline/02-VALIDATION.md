---
phase: 2
slug: extraction-pipeline
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-19
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio 1.3.0 |
| **Config file** | `pyproject.toml` — `asyncio_mode = "auto"`, `testpaths = ["tests"]` |
| **Quick run command** | `pytest tests/test_extraction.py -x -q` |
| **Full suite command** | `pytest tests/ -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_extraction.py -x -q`
- **After every plan wave:** Run `pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 2-CLS-01a | 01 | 0 | CLS-01 | unit | `pytest tests/test_extraction.py::test_classify_returns_known_type -x` | ❌ W0 | ⬜ pending |
| 2-CLS-01b | 01 | 0 | CLS-01 | unit | `pytest tests/test_extraction.py::test_classify_unknown -x` | ❌ W0 | ⬜ pending |
| 2-CLS-02 | 01 | 0 | CLS-02 | integration | `pytest tests/test_extraction.py::test_job_has_doc_type_after_classification -x` | ❌ W0 | ⬜ pending |
| 2-CLS-03 | 01 | 0 | CLS-03 | integration | `pytest tests/test_doc_type_override.py::test_override_triggers_reextraction -x` | ❌ W0 | ⬜ pending |
| 2-EXT-01 | 02 | 0 | EXT-01 | unit | `pytest tests/test_extraction.py::test_po_extraction_header -x` | ❌ W0 | ⬜ pending |
| 2-EXT-02 | 02 | 0 | EXT-02 | unit | `pytest tests/test_extraction.py::test_tender_extraction -x` | ❌ W0 | ⬜ pending |
| 2-EXT-03 | 02 | 0 | EXT-03 | unit | `pytest tests/test_extraction.py::test_quotation_extraction -x` | ❌ W0 | ⬜ pending |
| 2-EXT-04 | 02 | 0 | EXT-04 | unit | `pytest tests/test_extraction.py::test_invoice_extraction_header -x` | ❌ W0 | ⬜ pending |
| 2-EXT-05 | 02 | 0 | EXT-05 | unit | `pytest tests/test_extraction.py::test_supplier_comparison_header -x` | ❌ W0 | ⬜ pending |
| 2-EXT-06 | 02 | 0 | EXT-06 | unit | `pytest tests/test_extraction.py::test_po_extraction_line_items -x` | ❌ W0 | ⬜ pending |
| 2-EXT-07 | 02 | 0 | EXT-07 | unit | `pytest tests/test_extraction.py::test_invoice_extraction_line_items -x` | ❌ W0 | ⬜ pending |
| 2-EXT-08 | 02 | 0 | EXT-08 | unit | `pytest tests/test_extraction.py::test_supplier_comparison_line_items -x` | ❌ W0 | ⬜ pending |
| 2-EXT-09 | 03 | 0 | EXT-09 | unit | `pytest tests/test_extraction.py::test_provider_registry_swap -x` | ❌ W0 | ⬜ pending |
| 2-EXT-10 | 03 | 0 | EXT-10 | unit | `pytest tests/test_extraction.py::test_gemini_provider_uses_correct_sdk -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Note:** All LLM calls MUST be mocked via `unittest.mock.AsyncMock` for `client.aio.models.generate_content`. No real Gemini API calls in tests.

---

## Wave 0 Requirements

- [ ] `tests/test_extraction.py` — unit/integration stubs for CLS-01, CLS-02, EXT-01 through EXT-10
- [ ] `tests/test_doc_type_override.py` — integration stub for CLS-03 override + re-extraction flow
- [ ] `tests/fixtures/sample_po.md` — markdown fixture simulating Docling-processed purchase order
- [ ] `tests/fixtures/sample_invoice.md` — markdown fixture simulating Docling-processed invoice
- [ ] `tests/fixtures/sample_tender.md` — markdown fixture for tender/RFQ
- [ ] `tests/fixtures/sample_quotation.md` — markdown fixture for quotation
- [ ] `tests/fixtures/sample_supplier_comparison.md` — markdown fixture for supplier comparison

*Existing infrastructure (`tests/conftest.py` with `client` + `clear_job_store` fixtures, `pyproject.toml` asyncio config) is fully reusable — no framework changes needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Gemini response quality for ambiguous documents | EXT-01 to EXT-08 | LLM output quality is non-deterministic and cannot be fully asserted | Upload real sample documents; verify structured fields are populated and semantically correct |
| Schema rejection behavior (InvalidArgument 400) | EXT-01 to EXT-08 | Only triggered by Gemini API on schema violations; requires live API call | Use a schema with `additionalProperties` and verify 400 error is caught and surfaced |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
