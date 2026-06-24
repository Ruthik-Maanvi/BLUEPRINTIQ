"""
Local document extraction fallback.

This module performs REAL text/table extraction -- it never fabricates
content. It exists so the product has a working, evaluable pipeline before
any cloud credentials are configured (see docs/decisions.md, "Graceful
Degradation"). When Azure Document Intelligence credentials ARE configured,
app.services.azure_ocr is used instead and this module is not invoked.

Two extraction paths:
  - Digitally-generated PDFs (text-based): pdfplumber extracts the actual
    embedded text + tables directly from the PDF content stream. This is
    exact, not an OCR estimate, so we record ocr_confidence = 1.0.
  - Scanned/image-based pages (no embedded text) and raw images: Tesseract
    OCR is run instead, and its real per-word confidence is averaged and
    used as ocr_confidence.
"""
from pathlib import Path
from typing import TypedDict

import pdfplumber
from PIL import Image
import pytesseract

from app.utils.logger import get_logger

logger = get_logger(__name__)


class PageResult(TypedDict):
    page_number: int
    text: str
    tables: list
    confidence: float
    method: str


def _extract_image_file(filepath: Path) -> list[PageResult]:
    image = Image.open(filepath)
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    words = [w for w in data["text"] if w.strip()]
    confidences = [int(c) for c, w in zip(data["conf"], data["text"]) if w.strip() and int(c) >= 0]
    text = " ".join(words)
    avg_conf = (sum(confidences) / len(confidences) / 100.0) if confidences else 0.5
    return [
        {
            "page_number": 1,
            "text": text,
            "tables": [],
            "confidence": round(avg_conf, 2),
            "method": "tesseract_ocr",
        }
    ]


def _extract_pdf_file(filepath: Path) -> list[PageResult]:
    results: list[PageResult] = []
    with pdfplumber.open(filepath) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            tables = page.extract_tables() or []

            if text.strip() or tables:
                results.append(
                    {
                        "page_number": i,
                        "text": text,
                        "tables": tables,
                        "confidence": 1.0,  # exact embedded-text extraction
                        "method": "pdfplumber_text",
                    }
                )
            else:
                # No embedded text -> this page is a scanned image. Rasterize
                # and run Tesseract OCR on it instead of returning nothing.
                try:
                    pil_image = page.to_image(resolution=200).original
                    data = pytesseract.image_to_data(
                        pil_image, output_type=pytesseract.Output.DICT
                    )
                    words = [w for w in data["text"] if w.strip()]
                    confidences = [
                        int(c)
                        for c, w in zip(data["conf"], data["text"])
                        if w.strip() and int(c) >= 0
                    ]
                    ocr_text = " ".join(words)
                    avg_conf = (
                        (sum(confidences) / len(confidences) / 100.0)
                        if confidences
                        else 0.4
                    )
                    results.append(
                        {
                            "page_number": i,
                            "text": ocr_text,
                            "tables": [],
                            "confidence": round(avg_conf, 2),
                            "method": "tesseract_ocr_rasterized",
                        }
                    )
                except Exception as exc:  # pragma: no cover
                    logger.warning("Page %s OCR rasterization failed: %s", i, exc)
                    results.append(
                        {
                            "page_number": i,
                            "text": "",
                            "tables": [],
                            "confidence": 0.0,
                            "method": "extraction_failed",
                        }
                    )
    return results


def extract_local(filepath: Path) -> list[PageResult]:
    """Extract text/tables from a PDF or image file using local libraries
    only (no network calls). Returns one PageResult per page."""
    suffix = filepath.suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf_file(filepath)
    elif suffix in {".png", ".jpg", ".jpeg", ".tiff", ".tif"}:
        return _extract_image_file(filepath)
    raise ValueError(f"Unsupported file type for local extraction: {suffix}")