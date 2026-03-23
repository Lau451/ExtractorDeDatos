---
phase: 4
slug: full-api-integration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio (`asyncio_mode = "auto"`) |
| **Config file** | `pyproject.toml` — `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/test_patch.py -x` |
| **Full suite command** | `pytest tests/ -x` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_patch.py -x`
- **After every plan wave:** Run `pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 4-W0-01 | 01 | 0 | API-03 | unit | `pytest tests/test_patch.py::test_deep_merge_preserves_untouched_fields -x` | ❌ W0 | ⬜ pending |
| 4-W0-02 | 01 | 0 | API-03 | unit | `pytest tests/test_patch.py::test_deep_merge_nested_dict -x` | ❌ W0 | ⬜ pending |
| 4-W0-03 | 01 | 0 | API-03 | unit | `pytest tests/test_patch.py::test_deep_merge_list_by_index -x` | ❌ W0 | ⬜ pending |
| 4-W0-04 | 01 | 0 | API-03 | integration | `pytest tests/test_patch.py::test_patch_updates_field -x` | ❌ W0 | ⬜ pending |
| 4-W0-05 | 01 | 0 | API-03 | integration | `pytest tests/test_patch.py::test_patch_404 -x` | ❌ W0 | ⬜ pending |
| 4-W0-06 | 01 | 0 | API-03 | integration | `pytest tests/test_patch.py::test_patch_409_not_complete -x` | ❌ W0 | ⬜ pending |
| 4-W0-07 | 01 | 0 | REV-05 | integration | `pytest tests/test_patch.py::test_patch_then_export_reflects_edits -x` | ❌ W0 | ⬜ pending |
| 4-W0-08 | 01 | 0 | TTL (implicit) | unit | `pytest tests/test_patch.py::test_cleanup_removes_expired_jobs -x` | ❌ W0 | ⬜ pending |
| 4-W0-09 | 01 | 0 | Error codes | unit | `pytest tests/test_patch.py::test_error_codes_defined -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_patch.py` — stubs for all API-03, REV-05, TTL, and error-code tests listed above

*Existing infrastructure covers test runner and fixtures: `conftest.py` with `client` fixture and `clear_job_store` autouse fixture are already in place. No framework installation needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Background cleanup task runs every 5 minutes without crashing | TTL cleanup | Requires real-time observation over multiple minutes | Start server, watch logs for 10+ minutes; confirm no unhandled exceptions |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
