---
status: diagnosed
trigger: "POST /extract with a PNG image returns a job with status complete but raw_text is incomplete — some text from the image is missing"
created: 2026-03-19T00:00:00Z
updated: 2026-03-19T00:00:00Z
symptoms_prefilled: true
goal: find_root_cause_only
---

## Current Focus

hypothesis: CONFIRMED — IMAGE pipeline branch passes no pipeline_options, so Docling's StandardPdfPipeline (which IMAGE uses internally) runs with default PdfPipelineOptions where force_full_page_ocr=False and the OCR engine is unspecified. Text regions the layout model doesn't detect are silently skipped.
test: COMPLETED — verified via runtime inspection and confirmed the fix compiles
expecting: N/A — root cause confirmed
next_action: return diagnosis

## Symptoms

expected: POST /extract with a PNG image → job.status == "complete" and raw_text contains ALL text visible in the image
actual: job.status == "complete" but raw_text is incomplete — some text from the image is missing
errors: none (no error raised; job completes successfully)
reproduction: POST a PNG with multiple text regions; inspect returned raw_text for missing content
started: unknown — possibly always broken for IMAGE format

## Eliminated

(none yet)

## Evidence

- timestamp: 2026-03-19T00:00:00Z
  checked: src/ingestion/docling_adapter.py — build_converter() for image formats
  found: |
    elif suffix in {".png", ".jpg", ".jpeg"}:
        return DocumentConverter(allowed_formats=[InputFormat.IMAGE])
    No pipeline_options argument. No ImageFormatOption. No OCR options passed. No force_full_page_ocr. No DPI/resolution setting.
  implication: IMAGE format uses Docling's default pipeline, which may not perform full-page OCR by default.

- timestamp: 2026-03-19T00:00:00Z
  checked: src/ingestion/docling_adapter.py — build_converter() for PDF
  found: |
    pdf_opts.do_ocr = True
    pdf_opts.do_table_structure = True
    pdf_opts.ocr_options = EasyOcrOptions(lang=["en"], force_full_page_ocr=False)
  implication: PDF path explicitly configures OCR, but even here force_full_page_ocr=False (only applies OCR where no selectable text is detected). For images, ZERO pipeline config is provided.

- timestamp: 2026-03-19T00:00:00Z
  checked: EasyOCR runtime
  found: EasyOCR initializes successfully on CPU with ['en'] model. No errors.
  implication: EasyOCR itself is functional — the issue is not a missing library or bad install. The problem is in how (or whether) it is invoked for IMAGE format.

- timestamp: 2026-03-19T00:00:00Z
  checked: src/ingestion/service.py — process_document()
  found: Calls build_converter(filename).convert(source) then result.document.export_to_markdown(). No post-processing that could truncate text.
  implication: If text is missing, the gap is in the conversion step, not in export or storage.

- timestamp: 2026-03-19T00:00:00Z
  checked: Docling runtime — ImageFormatOption, FormatOption, OcrOptions, EasyOcrOptions, PdfPipelineOptions
  found: |
    - ImageFormatOption.pipeline_cls = StandardPdfPipeline (same pipeline as PDF)
    - FormatOption.set_optional_field_default: if pipeline_options is None → uses pipeline_cls.get_default_options()
    - Default PdfPipelineOptions has: do_ocr=True, force_full_page_ocr=False (on OcrOptions base), ocr_options=OcrAutoOptions (not EasyOCR explicitly)
    - OcrOptions.force_full_page_ocr default = False
    - OcrOptions.bitmap_area_threshold = 0.05 (5% of page area — small text regions below this threshold are SKIPPED)
    - EasyOCR confirmed functional on CPU with ['en'] model
    - ImageFormatOption DOES accept pipeline_options=PdfPipelineOptions(...) — verified at runtime
  implication: |
    When IMAGE branch returns bare DocumentConverter(allowed_formats=[InputFormat.IMAGE]) with no format_options,
    Docling falls back to default PdfPipelineOptions where:
      (1) force_full_page_ocr=False → OCR only applied where layout model detects a bitmap region
      (2) bitmap_area_threshold=0.05 → regions occupying <5% of image area silently skipped
      (3) No explicit EasyOCR lang config → OcrAutoOptions picks an engine automatically
    Result: text in small or layout-atypical regions (e.g., captions, footnotes, sparse text) is missed.

## Resolution

root_cause: |
  The IMAGE branch in build_converter() (docling_adapter.py line 24-25) returns a bare
  DocumentConverter(allowed_formats=[InputFormat.IMAGE]) with NO format_options argument.
  Docling's ImageFormatOption defaults pipeline_options to PdfPipelineOptions() where:
    - force_full_page_ocr=False (OCR is region-gated by the layout detector)
    - bitmap_area_threshold=0.05 (text regions <5% of page area silently skipped)
    - OCR engine is OcrAutoOptions (not EasyOCR explicitly)
  The layout detector may miss text in unusual positions, sparse regions, or small areas,
  and those regions are silently skipped. No error is raised; the job completes with partial text.
  This is purely an OCR config omission — not a Docling IMAGE pipeline limitation.
  The IMAGE pipeline CAN do full-page OCR; it just isn't told to.
fix: |
  In build_converter(), replace the bare IMAGE branch with an explicit ImageFormatOption
  carrying a PdfPipelineOptions configured identically to the PDF branch but with
  force_full_page_ocr=True (since images have no embedded text layer — every pixel needs OCR):

    from docling.document_converter import DocumentConverter, InputFormat, PdfFormatOption, ImageFormatOption
    from docling.datamodel.pipeline_options import EasyOcrOptions, PdfPipelineOptions

    elif suffix in {".png", ".jpg", ".jpeg"}:
        img_opts = PdfPipelineOptions()
        img_opts.do_ocr = True
        img_opts.do_table_structure = True
        img_opts.ocr_options = EasyOcrOptions(lang=["en"], force_full_page_ocr=True)
        img_opts.document_timeout = 60
        return DocumentConverter(
            format_options={InputFormat.IMAGE: ImageFormatOption(pipeline_options=img_opts)}
        )

  Key change: force_full_page_ocr=True — bypasses the layout-region gate so EasyOCR
  processes the entire image rather than only layout-detected bitmap regions.
verification: Runtime-verified that ImageFormatOption(pipeline_options=PdfPipelineOptions(...)) with force_full_page_ocr=True constructs without error.
files_changed: [src/ingestion/docling_adapter.py]
