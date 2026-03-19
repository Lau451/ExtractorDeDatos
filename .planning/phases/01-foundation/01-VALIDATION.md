---
phase: 1
slug: foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x + pytest-asyncio |
| **Config file** | `pytest.ini` or `pyproject.toml [tool.pytest.ini_options]` — Wave 0 installs |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 0 | ING-01..06 | unit | `pytest tests/test_ingestion.py -x -q` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | ING-01 | integration | `pytest tests/test_ingestion.py::test_pdf_text -x -q` | ❌ W0 | ⬜ pending |
| 1-01-03 | 01 | 1 | ING-02 | integration | `pytest tests/test_ingestion.py::test_scanned_pdf_ocr -x -q` | ❌ W0 | ⬜ pending |
| 1-01-04 | 01 | 1 | ING-03 | integration | `pytest tests/test_ingestion.py::test_xlsx_all_sheets -x -q` | ❌ W0 | ⬜ pending |
| 1-01-05 | 01 | 1 | ING-04 | integration | `pytest tests/test_ingestion.py::test_image_ocr -x -q` | ❌ W0 | ⬜ pending |
| 1-01-06 | 01 | 1 | ING-05 | integration | `pytest tests/test_ingestion.py::test_html_parse -x -q` | ❌ W0 | ⬜ pending |
| 1-01-07 | 01 | 1 | ING-06 | unit | `pytest tests/test_ingestion.py::test_unsupported_type -x -q` | ❌ W0 | ⬜ pending |
| 1-02-01 | 02 | 0 | API-01..05 | unit | `pytest tests/test_api.py -x -q` | ❌ W0 | ⬜ pending |
| 1-02-02 | 02 | 1 | API-01 | integration | `pytest tests/test_api.py::test_post_extract_returns_job_id -x -q` | ❌ W0 | ⬜ pending |
| 1-02-03 | 02 | 1 | API-02 | integration | `pytest tests/test_api.py::test_get_job_status_lifecycle -x -q` | ❌ W0 | ⬜ pending |
| 1-02-04 | 02 | 1 | API-05 | unit | `pytest tests/test_api.py::test_health_endpoint -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/__init__.py` — package marker
- [ ] `tests/conftest.py` — shared fixtures (TestClient, sample files)
- [ ] `tests/test_ingestion.py` — stubs for ING-01 through ING-06
- [ ] `tests/test_api.py` — stubs for API-01, API-02, API-05
- [ ] `pytest` + `pytest-asyncio` + `httpx` install in requirements-dev.txt

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| OCR produces non-empty text on real scanned PDF | ING-02 | Requires real scanned PDF fixture; OCR output is non-deterministic | Upload a multi-page scanned PDF; verify raw_text in job result is non-empty string |
| 60-second timeout causes error state | (timeout) | Requires simulating slow Docling processing | Mock asyncio.sleep(61) in ingestion; confirm job.status == "error" and error_code == "docling_timeout" |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
