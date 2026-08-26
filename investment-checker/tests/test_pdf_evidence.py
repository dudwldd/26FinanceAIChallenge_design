"""Tests for extracting bounded evidence from uploaded PDFs."""

import pytest

from data.pdf_evidence import (
    MAX_PDF_BYTES,
    PDFEvidenceError,
    extract_pdf_evidence,
)


class FakePage:
    """Small PDF page substitute with extractable text."""

    def __init__(self, text: str) -> None:
        self.text = text

    def extract_text(self) -> str:
        """Return fixed page text."""
        return self.text


class FakeReader:
    """Small PDF reader substitute used without filesystem I/O."""

    is_encrypted = False

    def __init__(self, stream: object) -> None:
        self.pages = [FakePage("매출은 18% 증가했다."), FakePage("영업이익률은 12%다.")]


def test_extract_pdf_evidence_returns_page_aware_text() -> None:
    """Extracted evidence should retain filename and page numbers."""
    result = extract_pdf_evidence(
        b"fake-pdf", "earnings.pdf", reader_factory=FakeReader
    )

    assert result["filename"] == "earnings.pdf"
    assert result["page_count"] == 2
    assert result["pages"][0] == {"page": 1, "text": "매출은 18% 증가했다."}
    assert result["was_truncated"] is False


def test_extract_pdf_evidence_rejects_large_files() -> None:
    """Uploads above the MVP limit should fail before parsing."""
    with pytest.raises(PDFEvidenceError, match="10MB"):
        extract_pdf_evidence(b"x" * (MAX_PDF_BYTES + 1), "large.pdf")


def test_extract_pdf_evidence_rejects_image_only_pdf() -> None:
    """A PDF without extractable text should explain the OCR limitation."""
    class EmptyReader:
        is_encrypted = False

        def __init__(self, stream: object) -> None:
            self.pages = [FakePage("")]

    with pytest.raises(PDFEvidenceError, match="스캔 이미지 PDF"):
        extract_pdf_evidence(b"fake-pdf", "scan.pdf", reader_factory=EmptyReader)
