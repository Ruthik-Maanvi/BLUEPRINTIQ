"""
Document extraction via IBM Docling (local layout + table structure).
Configured for Native PDF Mode (OCR Disabled) to prevent Windows Tesseract crashes.
"""
import threading
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_converter_lock = threading.Lock()
_converter_singleton: Any = None


class DoclingNotAvailable(Exception):
    """The docling package could not be loaded at all."""
    pass


class DoclingExtractionError(Exception):
    """Docling loaded fine, but conversion of THIS document failed."""
    pass


def _build_converter():
    """Lazily construct and cache a single DocumentConverter."""
    global _converter_singleton
    if _converter_singleton is not None:
        return _converter_singleton

    with _converter_lock:
        if _converter_singleton is not None:
            return _converter_singleton

        settings = get_settings()
        try:
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import (
                PdfPipelineOptions,
                TableFormerMode,
            )
            from docling.document_converter import DocumentConverter, PdfFormatOption
        except Exception as exc:
            raise DoclingNotAvailable(
                f"Could not import docling ({type(exc).__name__}: {exc})."
            ) from exc

        logger.info("Initializing Docling pipeline (Native PDF Text Mode, NO Tesseract OCR)...")

        pipeline_options = PdfPipelineOptions()
        
        # CRITICAL FIX 1: Turn OCR OFF so Windows doesn't crash
        pipeline_options.do_ocr = False 
        
        # Enable deep-learning table structure extraction
        pipeline_options.do_table_structure = True
        
        # CRITICAL FIX 2: Safely hardcode ACCURATE mode
        pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
        
        timeout = getattr(settings, "DOCLING_TIMEOUT_SECONDS", 300)
        if hasattr(pipeline_options, "document_timeout"):
            pipeline_options.document_timeout = timeout

        try:
            _converter_singleton = DocumentConverter(
                format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
            )
        except Exception as exc:
            raise DoclingNotAvailable(
                f"Docling DocumentConverter failed to initialize: {exc}"
            ) from exc

        return _converter_singleton


def _extract_page_content(document) -> list[dict]:
    """Walk the DoclingDocument in reading order and group real text + tables."""
    from docling_core.types.doc.document import TableItem, TextItem

    num_pages = len(document.pages) or 1
    text_by_page: dict[int, list[str]] = {}
    tables_by_page: dict[int, list[str]] = {}

    for item, _level in document.iterate_items():
        prov = getattr(item, "prov", None)
        page_no = prov[0].page_no if prov else 1

        if isinstance(item, TableItem):
            try:
                md = item.export_to_markdown(document)
            except TypeError:
                md = item.export_to_markdown()
            except Exception as exc:
                logger.warning("Failed to render a table to markdown: %s", exc)
                md = ""
            if md:
                tables_by_page.setdefault(page_no, []).append(md)
                text_by_page.setdefault(page_no, []).append(md)
        elif isinstance(item, TextItem):
            text = (item.text or "").strip()
            if text:
                text_by_page.setdefault(page_no, []).append(text)

    pages_out = []
    for page_no in range(1, num_pages + 1):
        combined_text = "\n\n".join(text_by_page.get(page_no, []))
        tables = [{"markdown": t} for t in tables_by_page.get(page_no, [])]
        pages_out.append(
            {
                "page_number": page_no,
                "text": combined_text,
                "tables": tables,
                "confidence": 0.90,
                "method": "docling_native_text",
            }
        )
    return pages_out


def analyze_document(filepath: Path) -> list[dict]:
    """Convert filepath with Docling and return per-page dicts."""
    from docling.datamodel.base_models import ConversionStatus

    converter = _build_converter() 

    try:
        try:
            result = converter.convert(filepath, raises_on_error=False)
        except TypeError:
            result = converter.convert(filepath)
    except Exception as exc:
        raise DoclingExtractionError(f"Docling raised during conversion: {exc}") from exc

    status = getattr(result, "status", None)
    if status not in (ConversionStatus.SUCCESS, ConversionStatus.PARTIAL_SUCCESS):
        raise DoclingExtractionError(f"Docling conversion status={status}")

    pages_out = _extract_page_content(result.document)

    if not any(p["text"].strip() for p in pages_out):
        raise DoclingExtractionError(
            f"Docling extracted zero text. The PDF might be entirely images, requiring OCR."
        )

    logger.info("Docling extracted %d page(s) from %s", len(pages_out), filepath.name)
    return pages_out