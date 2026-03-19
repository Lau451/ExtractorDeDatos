---
status: resolved
trigger: "POST /extract with HTML returns docling_parse_error: Pipeline SimplePipeline failed"
created: 2026-03-19T00:00:00Z
updated: 2026-03-19T00:01:00Z
---

## Current Focus

hypothesis: CONFIRMED — two bugs: (1) service.py discards the real exception cause; (2) docling_adapter.py has no HTMLFormatOption, but this is fine since Docling provides a working default.
test: Reproduced by patching HTMLDocumentBackend.convert() to raise — str(exc) only shows wrapper, __cause__ is lost.
expecting: Fix is to capture exc.__cause__ in service.py error handler.
next_action: DONE — root cause and fix identified.

## Symptoms

expected: POST /extract with HTML file returns 200 with extracted markdown text
actual: Returns {"status": "error", "error_code": "docling_parse_error", "error_message": "Pipeline SimplePipeline failed"}
errors: "Pipeline SimplePipeline failed"
reproduction: POST /extract with any .html or .htm file that exercises a code path in HTMLDocumentBackend.convert() that raises
started: unknown

## Eliminated

- hypothesis: lxml or beautifulsoup4 not installed
  evidence: pip show confirms lxml==6.0.2 and beautifulsoup4==4.14.3 are both installed and listed as docling dependencies
  timestamp: 2026-03-19T00:00:00Z

- hypothesis: HTMLFormatOption missing / wrong API usage
  evidence: DocumentConverter(allowed_formats=[InputFormat.HTML]) correctly maps to HTMLFormatOption with SimplePipeline + HTMLDocumentBackend. Simple and complex HTML conversions all succeed in isolation.
  timestamp: 2026-03-19T00:00:00Z

- hypothesis: Stream position / consumed stream causes failure
  evidence: HTMLDocumentBackend reads via BytesIO.getvalue(), not .read(), so stream position is irrelevant.
  timestamp: 2026-03-19T00:00:00Z

## Evidence

- timestamp: 2026-03-19T00:00:00Z
  checked: requirements.txt
  found: lxml and beautifulsoup4 not listed — but both are installed as transitive dependencies of docling==2.80.0
  implication: Not the cause of the error

- timestamp: 2026-03-19T00:00:00Z
  checked: docling/pipeline/base_pipeline.py:79-89
  found: execute() wraps any internal exception as RuntimeError("Pipeline SimplePipeline failed") using `raise ... from e` — Python's __cause__ chaining
  implication: The real underlying error is stored in exc.__cause__ but service.py never accesses it

- timestamp: 2026-03-19T00:00:00Z
  checked: src/ingestion/service.py:36
  found: `except Exception as exc: await job_store.set_error(job_id, "docling_parse_error", str(exc))`
  implication: str(exc) only captures the RuntimeError wrapper text. The original exception (the actual reason HTMLDocumentBackend.convert() failed) is in exc.__cause__ and is silently discarded. This makes the error completely undiagnosable in production.

- timestamp: 2026-03-19T00:00:00Z
  checked: Reproduction test (patched HTMLDocumentBackend.convert to raise ValueError)
  found: str(exc) = "Pipeline SimplePipeline failed"; exc.__cause__ = "lxml parsing failed: encoding error in HTML content"
  implication: Confirms that any content-specific HTML parsing failure will present as the opaque "Pipeline SimplePipeline failed" message with no actionable detail

- timestamp: 2026-03-19T00:00:00Z
  checked: docling/backend/html_backend.py:290-291
  found: convert() raises RuntimeError("Invalid HTML document.") when is_valid() is False (i.e., when BeautifulSoup failed to initialize)
  implication: This is one of the real failure modes that gets swallowed into the opaque wrapper

## Resolution

root_cause: src/ingestion/service.py line 36 — the except clause calls str(exc) on the RuntimeError wrapper from Docling, discarding exc.__cause__ which holds the real underlying failure reason. The message "Pipeline SimplePipeline failed" is Docling's generic wrapper (base_pipeline.py:89) that wraps any internal exception via Python's exception chaining. The actual parse error is always in __cause__ but is never captured.
fix: In service.py, change the error message to walk the exception chain: use `str(exc.__cause__ or exc)` instead of `str(exc)`. This surfaces the real Docling error. Additionally, log the full traceback with `logging.exception()` before setting the error so the real stack trace is visible in server logs.
verification: Patching test confirms exc.__cause__ contains the real error message.
files_changed: [src/ingestion/service.py]
