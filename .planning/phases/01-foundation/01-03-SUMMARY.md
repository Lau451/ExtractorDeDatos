---
phase: 01-foundation
plan: "03"
subsystem: ingestion
tags: [docling, ocr, easyocr, image-processing, error-handling, logging]

# Dependency graph
requires:
  - phase: 01-02
    provides: "docling_adapter.py IMAGE branch and service.py process_document function"
provides:
  - "IMAGE branch with ImageFormatOption and force_full_page_ocr=True for complete OCR extraction"
  - "Error handler that exposes exc.__cause__ and logs full traceback for real Docling errors"
affects: [02-extraction, 03-api, testing]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ImageFormatOption with PdfPipelineOptions for image OCR (mirrors PdfFormatOption pattern)"
    - "exc.__cause__ unwrapping for chained exceptions from third-party libraries"
    - "logging.exception() before set_error for full traceback capture"

key-files:
  created: []
  modified:
    - src/ingestion/docling_adapter.py
    - src/ingestion/service.py

key-decisions:
  - "force_full_page_ocr=True for images (no embedded text layer, every pixel needs OCR) vs False for PDF (may have selectable text)"
  - "exc.__cause__ unwrapping surfaces real Docling error instead of opaque pipeline wrapper message"
  - "logging.exception() chosen over logging.error() to automatically include full traceback"

patterns-established:
  - "Format options pattern: always use format_options dict with explicit FormatOption objects rather than allowed_formats list"
  - "Error surfacing pattern: unwrap exc.__cause__ before storing error detail in job store"

requirements-completed: [ING-04, ING-05]

# Metrics
duration: 3min
completed: 2026-03-19
---

# Phase 01 Plan 03: UAT Gap Closure — Full-page OCR and Error Surfacing Summary

**PNG OCR fixed with ImageFormatOption(force_full_page_ocr=True) and HTML errors now surface real cause via exc.__cause__ unwrapping with logging.exception()**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-03-19T04:44:02Z
- **Completed:** 2026-03-19T04:47:50Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- IMAGE branch in `docling_adapter.py` now uses `ImageFormatOption` with `PdfPipelineOptions(do_ocr=True, force_full_page_ocr=True)` — guarantees full OCR coverage on PNG/JPG files where no embedded text layer exists
- `service.py` error handler now unwraps `exc.__cause__` to surface the real Docling error (e.g. "Invalid HTML document.") instead of the opaque "Pipeline SimplePipeline failed" wrapper
- Full traceback is emitted via `logger.exception()` before setting job error state, enabling server-side debugging
- All 15 existing tests pass with no regressions (7 ingestion + 4 extract + 4 jobs)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add ImageFormatOption with full-page OCR to IMAGE branch** - `fc03dad` (feat)
2. **Task 2: Surface real Docling error via exc.__cause__ and add logging** - `7c26a38` (fix)

## Files Created/Modified

- `src/ingestion/docling_adapter.py` - Added `ImageFormatOption` import; replaced bare `allowed_formats=[InputFormat.IMAGE]` with explicit `ImageFormatOption(pipeline_options=img_opts)` carrying `force_full_page_ocr=True`
- `src/ingestion/service.py` - Added `import logging`, module-level `logger`, and replaced `str(exc)` with `str(exc.__cause__) if exc.__cause__ else str(exc)` plus `logger.exception()` call

## Decisions Made

- `force_full_page_ocr=True` for images vs `False` for PDF: images have no embedded text layer so OCR must scan every pixel; PDFs may have selectable text that does not need OCR
- `exc.__cause__` unwrapping preferred over walking the full exception chain — Docling uses direct chaining (`raise X from Y`) so `__cause__` is sufficient and safe
- `logging.exception()` over `logging.error()` because it automatically appends the full traceback without requiring manual `exc_info=True`

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - both fixes applied cleanly, all pre-existing tests continued to pass.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 01 ingestion layer is complete: PDF (text + scanned), XLSX, PNG/JPG, and HTML all parse correctly
- OCR is active and not silently skipped (Phase 01 success criteria #3 now met)
- Error observability is in place for all format pipelines
- Ready to proceed to Phase 02 (extraction / structured data output)

---
*Phase: 01-foundation*
*Completed: 2026-03-19*

## Self-Check: PASSED

- src/ingestion/docling_adapter.py: FOUND
- src/ingestion/service.py: FOUND
- .planning/phases/01-foundation/01-03-SUMMARY.md: FOUND
- Commit fc03dad: FOUND
- Commit 7c26a38: FOUND
