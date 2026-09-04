"""
Document text extraction service (Phase 8).

Target flow (docs/architecture.md upload step 5):

    file bytes â†’ extract text (PyMuPDF / plain text)
              â†’ if scanned/insufficient text â†’ OCR fallback (Tesseract)
              â†’ ExtractionOutcome(status, method, text, page_count)

Design rules:

* **Never raises** â€” callers get a FAILED outcome instead; extraction problems
  must not break document upload/versioning (graceful degradation).
* OCR is optional: Tesseract is detected at runtime via PATH. When absent,
  scanned PDFs yield OCR_UNAVAILABLE (never fabricated results).
* Only textual metadata is produced here â€” raw file bytes stay in object
  storage; extracted text is persisted by the caller in document_texts.
"""

from __future__ import annotations

import logging
import re
import shutil
import subprocess  # noqa: S404 â€” fixed-argument tesseract invocation, no shell
import tempfile
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("sih26190.extraction")

# Extraction methods (document_texts.extraction_method).
METHOD_PYMUPDF = "PYMUPDF"
METHOD_OCR = "OCR"
METHOD_PLAIN_TEXT = "PLAIN_TEXT"
METHOD_NONE = "NONE"

# Extraction statuses (document_texts.extraction_status).
STATUS_COMPLETED = "COMPLETED"  # usable text extracted
STATUS_EMPTY = "EMPTY"  # parsed fine but no text at all
STATUS_UNSUPPORTED = "UNSUPPORTED_TYPE"  # binary office/image formats, no OCR
STATUS_OCR_UNAVAILABLE = "OCR_UNAVAILABLE"  # scanned file but no Tesseract
STATUS_FAILED = "FAILED"  # parser/OCR error (file remains fully accessible)

# A PDF is considered "scanned" when it contains fewer alphanumeric characters
# than this across all pages (normal text PDFs far exceed it).
_MIN_USEFUL_TEXT_CHARS = 40

# Upper bound for text we persist from one document (protects the DB row from
# pathological multi-hundred-page scans; search only needs the leading text).
_MAX_STORED_TEXT_CHARS = 200_000

_OCR_TIMEOUT_SECONDS = 120
_OCR_MAX_DPI = 200  # balance between OCR quality and CPU/memory cost

_tesseract_path: str | None | bool = False  # False = not yet resolved


@dataclass
class ExtractionOutcome:
    """Result of a text-extraction attempt (never raises)."""

    status: str
    method: str
    text: str | None = None
    page_count: int | None = None
    error_message: str | None = None

    @property
    def searchable(self) -> bool:
        return bool(self.text and self.text.strip())


def ocr_available() -> bool:
    """Detect a Tesseract executable on PATH (result cached per process)."""
    global _tesseract_path
    if _tesseract_path is False:
        found = shutil.which("tesseract")
        _tesseract_path = found or None
        if _tesseract_path is None:
            logger.info("Tesseract OCR not found on PATH — OCR fallback disabled")
    return _tesseract_path is not None


def reset_ocr_cache() -> None:
    """Testing hook — force re-detection of the Tesseract executable."""
    global _tesseract_path
    _tesseract_path = False


def _clean_text(raw: str) -> str:
    """Normalise whitespace; hard-limit the persisted size."""
    cleaned = re.sub(r"[ \t]+", " ", raw)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    if len(cleaned) > _MAX_STORED_TEXT_CHARS:
        cleaned = cleaned[:_MAX_STORED_TEXT_CHARS] + "\nâ€¦[truncated]"
    return cleaned


def _run_tesseract(images: list[bytes], lang: str = "eng") -> str:
    """
    OCR a sequence of PNG page images with the installed Tesseract binary.

    Each image is written to a temp file (Tesseract needs a file argument) and
    invoked with fixed arguments â€” no shell, no user-controlled argv.
    """
    binary = _tesseract_path
    if not binary:  # pragma: no cover â€” callers check ocr_available() first
        raise RuntimeError("Tesseract is not available")

    chunks: list[str] = []
    with tempfile.TemporaryDirectory(prefix="sih_ocr_") as tmp:
        for index, png in enumerate(images):
            image_path = Path(tmp) / f"page_{index:04d}.png"
            image_path.write_bytes(png)
            result = subprocess.run(  # noqa: S603 â€” fixed argv, no shell
                [binary, str(image_path), "stdout", "-l", lang],
                capture_output=True,
                timeout=_OCR_TIMEOUT_SECONDS,
            )
            if result.returncode != 0:
                stderr = result.stderr.decode("utf-8", "replace").strip()
                raise RuntimeError(f"Tesseract failed on page {index + 1}: {stderr[:200]}")
            chunks.append(result.stdout.decode("utf-8", "replace"))
    return "\n".join(chunks)


def _extract_pdf(content: bytes) -> ExtractionOutcome:
    """Text-layer extraction with OCR fallback for scanned PDFs."""
    import pymupdf  # imported lazily so the app can start without the wheel

    try:
        doc = pymupdf.open(stream=content, filetype="pdf")
    except Exception as exc:  # noqa: BLE001 â€” malformed PDF
        return ExtractionOutcome(
            status=STATUS_FAILED,
            method=METHOD_NONE,
            error_message=f"PDF could not be parsed: {exc}"[:300],
        )

    page_count = int(doc.page_count)
    try:
        page_texts = [page.get_text("text") or "" for page in doc]
    except Exception as exc:  # noqa: BLE001 â€” page-level parser failure
        doc.close()
        return ExtractionOutcome(
            status=STATUS_FAILED,
            method=METHOD_PYMUPDF,
            page_count=page_count,
            error_message=f"PDF text layer could not be read: {exc}"[:300],
        )
    doc.close()

    combined = _clean_text("\n".join(page_texts))
    alpha_total = sum(ch.isalnum() for ch in combined)

    if alpha_total >= _MIN_USEFUL_TEXT_CHARS:
        return ExtractionOutcome(
            status=STATUS_COMPLETED,
            method=METHOD_PYMUPDF,
            text=combined,
            page_count=page_count,
        )

    # Little/no text layer â†’ scanned PDF. OCR only if actually available.
    if not ocr_available():
        return ExtractionOutcome(
            status=STATUS_OCR_UNAVAILABLE if alpha_total == 0 else STATUS_COMPLETED,
            method=METHOD_PYMUPDF if alpha_total else METHOD_NONE,
            text=combined or None,
            page_count=page_count,
            error_message=(
                "Scanned PDF detected but Tesseract OCR is not installed"
                if alpha_total == 0
                else None
            ),
        )

    try:
        doc = pymupdf.open(stream=content, filetype="pdf")
        images: list[bytes] = []
        for page in doc:
            pix = page.get_pixmap(dpi=_OCR_MAX_DPI)
            images.append(pix.tobytes("png"))
        doc.close()
        ocr_text = _run_tesseract(images)
    except Exception as exc:  # noqa: BLE001 â€” OCR must never break the flow
        logger.warning("OCR failed for a scanned PDF: %s", exc)
        return ExtractionOutcome(
            status=STATUS_FAILED,
            method=METHOD_OCR,
            page_count=page_count,
            error_message=f"OCR failed: {exc}"[:300],
        )

    ocr_clean = _clean_text(ocr_text)
    if ocr_clean:
        return ExtractionOutcome(
            status=STATUS_COMPLETED,
            method=METHOD_OCR,
            text=ocr_clean,
            page_count=page_count,
        )
    return ExtractionOutcome(
        status=STATUS_EMPTY,
        method=METHOD_OCR,
        page_count=page_count,
        error_message="OCR produced no text",
    )


def _extract_image(content: bytes, content_type: str) -> ExtractionOutcome:
    """OCR a PNG/JPEG upload directly (image documents have no text layer)."""
    if not ocr_available():
        return ExtractionOutcome(
            status=STATUS_OCR_UNAVAILABLE,
            method=METHOD_NONE,
            error_message=f"OCR not installed â€” {content_type} cannot be read",
        )
    try:
        ocr_text = _run_tesseract([content])
    except Exception as exc:  # noqa: BLE001
        return ExtractionOutcome(
            status=STATUS_FAILED,
            method=METHOD_OCR,
            error_message=f"OCR failed: {exc}"[:300],
        )
    cleaned = _clean_text(ocr_text)
    if cleaned:
        return ExtractionOutcome(
            status=STATUS_COMPLETED, method=METHOD_OCR, text=cleaned, page_count=1
        )
    return ExtractionOutcome(status=STATUS_EMPTY, method=METHOD_OCR, page_count=1)


def extract_text(content: bytes, content_type: str) -> ExtractionOutcome:
    """
    Extract searchable text from uploaded bytes. Never raises.

    Supported: PDF (PyMuPDF + OCR fallback), text/plain, text/csv.
    Images are OCR'd only when Tesseract is installed. Every other type
    (office documents) yields UNSUPPORTED_TYPE â€” upload still succeeds.
    """
    try:
        if content_type == "application/pdf":
            return _extract_pdf(content)
        if content_type in ("text/plain", "text/csv"):
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                text = content.decode("latin-1", "replace")
            cleaned = _clean_text(text)
            if cleaned:
                return ExtractionOutcome(
                    status=STATUS_COMPLETED, method=METHOD_PLAIN_TEXT, text=cleaned
                )
            return ExtractionOutcome(status=STATUS_EMPTY, method=METHOD_PLAIN_TEXT)
        if content_type in ("image/png", "image/jpeg"):
            return _extract_image(content, content_type)
        return ExtractionOutcome(
            status=STATUS_UNSUPPORTED,
            method=METHOD_NONE,
            error_message="Text extraction not supported for this file type",
        )
    except Exception as exc:  # noqa: BLE001 â€” absolute last-resort guard
        logger.warning("Unexpected extraction failure (%s): %s", content_type, exc)
        return ExtractionOutcome(
            status=STATUS_FAILED,
            method=METHOD_NONE,
            error_message="Text extraction failed unexpectedly",
        )
