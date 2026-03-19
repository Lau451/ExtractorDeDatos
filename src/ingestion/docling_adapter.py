from pathlib import Path

from docling.document_converter import DocumentConverter, InputFormat, PdfFormatOption
from docling.datamodel.pipeline_options import EasyOcrOptions, PdfPipelineOptions


def build_converter(filename: str) -> DocumentConverter:
    """Return a format-aware Docling DocumentConverter for the given filename."""
    suffix = Path(filename).suffix.lower()

    if suffix == ".pdf":
        pdf_opts = PdfPipelineOptions()
        pdf_opts.do_ocr = True                    # fallback OCR for scanned pages
        pdf_opts.do_table_structure = True
        pdf_opts.ocr_options = EasyOcrOptions(lang=["en"], force_full_page_ocr=False)
        pdf_opts.document_timeout = 60            # soft batch-level checkpoint
        return DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_opts)}
        )

    elif suffix in {".xlsx", ".xls"}:
        return DocumentConverter(allowed_formats=[InputFormat.XLSX])

    elif suffix in {".png", ".jpg", ".jpeg"}:
        return DocumentConverter(allowed_formats=[InputFormat.IMAGE])

    elif suffix in {".html", ".htm"}:
        return DocumentConverter(allowed_formats=[InputFormat.HTML])

    raise ValueError(f"No converter for extension: {suffix}")
