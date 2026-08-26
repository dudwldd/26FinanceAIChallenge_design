"""Extract bounded, page-aware evidence text from an uploaded PDF."""

from collections.abc import Callable
from io import BytesIO
from typing import Any

MAX_PDF_BYTES = 10 * 1024 * 1024
MAX_PDF_PAGES = 30
MAX_EXTRACTED_CHARACTERS = 30_000


class PDFEvidenceError(ValueError):
    """Raised when an uploaded PDF cannot be used as evidence."""


def _create_pdf_reader(stream: BytesIO) -> Any:
    """Import the PDF dependency only when a real upload is processed."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise PDFEvidenceError(
            "PDF 분석 라이브러리가 설치되지 않았습니다. "
            "requirements.txt를 다시 설치해주세요."
        ) from exc
    return PdfReader(stream)


def _normalize_text(text: str) -> str:
    """Collapse repeated whitespace while preserving readable paragraphs."""
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def extract_pdf_evidence(
    file_bytes: bytes,
    filename: str,
    *,
    reader_factory: Callable[[BytesIO], Any] | None = None,
) -> dict[str, Any]:
    """Return safe, bounded PDF text with page numbers for AI grounding."""
    if not file_bytes:
        raise PDFEvidenceError("PDF 파일이 비어 있습니다.")
    if len(file_bytes) > MAX_PDF_BYTES:
        raise PDFEvidenceError("PDF는 10MB 이하만 첨부할 수 있습니다.")

    try:
        reader = (reader_factory or _create_pdf_reader)(BytesIO(file_bytes))
        if getattr(reader, "is_encrypted", False):
            raise PDFEvidenceError("암호화된 PDF는 분석할 수 없습니다.")
        pages = list(reader.pages)
    except PDFEvidenceError:
        raise
    except Exception as exc:
        raise PDFEvidenceError(
            "PDF를 읽지 못했습니다. 정상적인 PDF 파일인지 확인해주세요."
        ) from exc

    if not pages:
        raise PDFEvidenceError("PDF에 페이지가 없습니다.")

    extracted_pages: list[dict[str, Any]] = []
    character_count = 0
    was_truncated = len(pages) > MAX_PDF_PAGES

    for page_number, page in enumerate(pages[:MAX_PDF_PAGES], start=1):
        try:
            text = _normalize_text(page.extract_text() or "")
        except Exception:
            text = ""
        if not text:
            continue

        remaining = MAX_EXTRACTED_CHARACTERS - character_count
        if remaining <= 0:
            was_truncated = True
            break
        if len(text) > remaining:
            text = text[:remaining]
            was_truncated = True

        extracted_pages.append({"page": page_number, "text": text})
        character_count += len(text)

    if not extracted_pages:
        raise PDFEvidenceError(
            "PDF에서 텍스트를 찾지 못했습니다. "
            "스캔 이미지 PDF는 현재 버전에서 지원하지 않습니다."
        )

    return {
        "filename": filename,
        "size_bytes": len(file_bytes),
        "page_count": len(pages),
        "extracted_character_count": character_count,
        "was_truncated": was_truncated,
        "pages": extracted_pages,
    }
