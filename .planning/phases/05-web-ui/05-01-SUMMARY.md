---
phase: 05-web-ui
plan: 01
subsystem: ui
tags: [react, vite, tailwind, shadcn, typescript, vitest]

# Dependency graph
requires:
  - phase: 04-full-api-integration
    provides: "All 5 backend API endpoints verified and working"
provides:
  - "React + Vite + Tailwind v4 + shadcn/ui frontend scaffold in frontend/"
  - "TypeScript interfaces matching backend JobResponse shape exactly"
  - "Typed API client covering all 5 backend endpoints"
  - "Field label registry for all 5 doc types (40+ keys)"
  - "Error message, status text, and doc type utility modules"
  - "Vitest test infrastructure configured and ready"
affects: [05-02, 05-03]

# Tech tracking
tech-stack:
  added:
    - "react 19 + react-dom"
    - "vite 8 + @vitejs/plugin-react"
    - "tailwindcss 4 + @tailwindcss/vite"
    - "shadcn/ui (CLI): table, button, input, select, badge"
    - "react-dropzone 15"
    - "lucide-react 1"
    - "clsx + tailwind-merge + class-variance-authority"
    - "vitest + @testing-library/react + @testing-library/jest-dom + jsdom"
  patterns:
    - "vitest/config defineConfig for unified Vite + test config"
    - "@ path alias (src/*) in tsconfig.app.json + vite.config.ts"
    - "Vite proxy: /api/* -> http://localhost:8000 with path rewrite"
    - "shadcn/ui cn() helper via clsx + tailwind-merge"

key-files:
  created:
    - "frontend/vite.config.ts"
    - "frontend/tsconfig.app.json"
    - "frontend/src/types/api.ts"
    - "frontend/src/lib/api.ts"
    - "frontend/src/lib/errorMessages.ts"
    - "frontend/src/lib/statusText.ts"
    - "frontend/src/lib/fieldLabels.ts"
    - "frontend/src/lib/docTypes.ts"
    - "frontend/src/test-setup.ts"
    - "frontend/src/components/ui/table.tsx"
    - "frontend/src/components/ui/button.tsx"
    - "frontend/src/components/ui/input.tsx"
    - "frontend/src/components/ui/select.tsx"
    - "frontend/src/components/ui/badge.tsx"
  modified:
    - "frontend/src/index.css (replaced with @import tailwindcss + shadcn theme)"
    - "frontend/src/App.tsx (replaced with minimal placeholder)"
    - "frontend/index.html (added IBM Plex font links)"

key-decisions:
  - "Use defineConfig from vitest/config (not vite) to include test config without TypeScript errors"
  - "Path alias @/* -> ./src/* added to tsconfig.app.json (required by shadcn init) and vite.config.ts"
  - "Removed nested .git repo created by npm create vite before staging to parent repo"
  - "shadcn init uses neutral palette by default — generates CSS custom properties for all shadcn tokens"

patterns-established:
  - "Pattern: All /api/* fetch calls use relative paths — Vite proxy handles dev routing, FastAPI serves prod"
  - "Pattern: JobResponse.status typed as union + string fallback for forward-compatibility"
  - "Pattern: getFieldLabel() fallback converts snake_case to Title Case for unlisted keys"
  - "Pattern: LINE_ITEM_KEYS maps doc_type to its line items array key in extraction_result"

requirements-completed: [REV-01, REV-02, REV-03, REV-04]

# Metrics
duration: 8min
completed: 2026-03-24
---

# Phase 05 Plan 01: Frontend Scaffold and Foundation Libraries Summary

**React 19 + Vite 8 + Tailwind v4 + shadcn/ui frontend with typed API client, field label registry covering all 5 doc types, and Vitest test infrastructure**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-24T03:27:00Z
- **Completed:** 2026-03-24T03:35:11Z
- **Tasks:** 2
- **Files modified:** 29

## Accomplishments

- Complete frontend scaffold: React 19, Vite 8, Tailwind v4, shadcn/ui (5 components), all runtime deps
- TypeScript interfaces matching backend models exactly (JobResponse, ExtractResponse, PatchFieldsRequest)
- Typed fetch wrappers for all 5 backend endpoints with proper error handling
- Field label registry with 40+ field keys covering all 5 doc types plus snake_case fallback
- Vitest configured with jsdom environment and @testing-library/jest-dom matchers
- Vite dev proxy: /api/* -> http://localhost:8000 with path rewrite matching backend route structure

## Task Commits

Each task was committed atomically:

1. **Task 1: Scaffold Vite project, install dependencies, initialize shadcn/ui** - `8995041` (feat)
2. **Task 2: Create TypeScript types, API client, and utility modules** - `84a018d` (feat)

## Files Created/Modified

- `frontend/vite.config.ts` - Vite + Tailwind plugin + proxy + @ alias + Vitest test config (using vitest/config)
- `frontend/tsconfig.app.json` - Added baseUrl + @/* path alias (required by shadcn init)
- `frontend/tsconfig.json` - Added compilerOptions with path aliases for root-level resolution
- `frontend/index.html` - IBM Plex Mono/Sans font links from Google Fonts
- `frontend/src/index.css` - @import tailwindcss + shadcn/ui CSS custom properties theme
- `frontend/src/App.tsx` - Minimal placeholder (bg-background font-sans)
- `frontend/src/test-setup.ts` - @testing-library/jest-dom import
- `frontend/src/lib/utils.ts` - cn() helper via clsx + tailwind-merge (installed by shadcn init)
- `frontend/src/types/api.ts` - JobResponse, ExtractResponse, DocTypeOverrideRequest, PatchFieldsRequest, ErrorResponse
- `frontend/src/lib/api.ts` - postExtract, getJob, patchDocType, patchFields, exportUrl
- `frontend/src/lib/errorMessages.ts` - ERROR_MESSAGES map + getErrorMessage() for all 5 error codes
- `frontend/src/lib/statusText.ts` - STATUS_TEXT map + getStatusText() for all 4 processing stages
- `frontend/src/lib/docTypes.ts` - DOC_TYPES_WITH_LINE_ITEMS, VALID_DOC_TYPES, DocType, DOC_TYPE_LABELS
- `frontend/src/lib/fieldLabels.ts` - FIELD_LABELS (40+ keys), getFieldLabel(), LINE_ITEM_KEYS
- `frontend/src/components/ui/{table,button,input,select,badge}.tsx` - shadcn/ui component copies

## Decisions Made

- **vitest/config vs vite**: Used `defineConfig` from `vitest/config` (not `vite`) to include `test:` config without TypeScript TS2769 error. The vite package's UserConfigExport type doesn't include test — vitest/config extends it.
- **Path alias location**: Added `@/*: ./src/*` to both `tsconfig.app.json` (for TypeScript resolution) and `vite.config.ts` (for Vite bundler resolution). shadcn init requires the alias in `tsconfig.json` root to validate import alias during init.
- **Nested git repo**: `npm create vite@latest` initialized a `.git` repo inside `frontend/`. Removed it before staging so files are tracked by the parent repo.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] tsconfig.json alias required for shadcn init**
- **Found during:** Task 1 (shadcn init)
- **Issue:** `npx shadcn@latest init` validates import alias from tsconfig.json (root) — the vite template doesn't include path aliases by default. Init exited with error: "No import alias found in your tsconfig.json file."
- **Fix:** Added `compilerOptions.baseUrl` and `compilerOptions.paths` with `@/*` to both `tsconfig.json` and `tsconfig.app.json`
- **Files modified:** frontend/tsconfig.json, frontend/tsconfig.app.json
- **Verification:** shadcn init completed successfully, `npx tsc --noEmit` exits 0
- **Committed in:** 8995041 (Task 1 commit)

**2. [Rule 3 - Blocking] vitest/config required for test config in vite.config.ts**
- **Found during:** Task 1 (npm run build verification)
- **Issue:** `defineConfig` from `vite` doesn't include the `test` key in its type — TypeScript error TS2769 on build
- **Fix:** Changed import from `'vite'` to `'vitest/config'` which re-exports Vite's defineConfig with Vitest type extensions merged in
- **Files modified:** frontend/vite.config.ts
- **Verification:** `npm run build` exits 0
- **Committed in:** 8995041 (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both fixes necessary to unblock task completion. No scope creep.

## Issues Encountered

- `npm create vite@latest` creates a nested `.git` directory in `frontend/` — caused `git add` on individual files to silently do nothing (git treats nested repos as submodules). Fixed by removing the nested `.git` before staging.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All foundation code is in place: types, API client, utilities, shadcn components, test setup
- Plans 02 and 03 can import from `@/types/api`, `@/lib/api`, `@/lib/fieldLabels`, `@/lib/docTypes` immediately
- Vitest is configured and ready for component tests (`cd frontend && npx vitest run`)
- Build is green; dev server proxy is configured for http://localhost:8000

---
*Phase: 05-web-ui*
*Completed: 2026-03-24*
