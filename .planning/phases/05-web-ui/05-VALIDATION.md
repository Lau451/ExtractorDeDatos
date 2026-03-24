---
phase: 5
slug: web-ui
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing backend) + Vitest (new, frontend) |
| **Config file** | `frontend/vite.config.ts` (Vitest shares Vite config) |
| **Quick run command** | `cd frontend && npx vitest run --reporter=verbose` |
| **Full suite command** | `pytest tests/ && cd frontend && npx vitest run` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npx vitest run --reporter=verbose`
- **After every plan wave:** Run `pytest tests/ && cd frontend && npx vitest run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | REV-01 | unit (component) | `npx vitest run src/components/ReviewTable.test.tsx` | ❌ W0 | ⬜ pending |
| 05-01-02 | 01 | 1 | REV-02 | unit (component) | `npx vitest run src/components/EditableCell.test.tsx` | ❌ W0 | ⬜ pending |
| 05-01-03 | 01 | 1 | REV-03 | unit (component) | `npx vitest run src/components/EditableCell.test.tsx` | ❌ W0 | ⬜ pending |
| 05-01-04 | 01 | 1 | REV-04 | unit (component) | `npx vitest run src/components/ProgressView.test.tsx` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/src/components/ReviewTable.test.tsx` — stubs for REV-01
- [ ] `frontend/src/components/EditableCell.test.tsx` — stubs for REV-02, REV-03
- [ ] `frontend/src/components/ProgressView.test.tsx` — stubs for REV-04
- [ ] `frontend/src/test-setup.ts` — `@testing-library/jest-dom` matchers config
- [ ] Framework install: `cd frontend && npm install --save-dev vitest @testing-library/react @testing-library/jest-dom jsdom`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Drag-and-drop upload zone | REV-01 | Browser drag events not reliably testable in JSDOM | 1. Open app 2. Drag PDF onto upload zone 3. Verify file accepted and progress starts |
| CSV download triggers browser download | REV-02 | File download requires real browser | 1. Complete extraction 2. Click Download CSV 3. Verify file downloads with correct content |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
