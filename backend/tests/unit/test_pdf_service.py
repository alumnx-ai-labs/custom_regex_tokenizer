import fitz
import pytest

from app.core.errors import InvalidPDFError, NoExtractableTextError
from app.services.pdf_service import extract_text


def _build_pdf(text: str | None) -> bytes:
    document = fitz.open()
    page = document.new_page()
    if text:
        page.insert_text((72, 72), text)
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


def test_extract_text_from_valid_pdf():
    pdf_bytes = _build_pdf("Hello, tokenizer world!")

    text = extract_text(pdf_bytes)

    assert "Hello" in text


def test_extract_text_raises_on_corrupted_pdf():
    with pytest.raises(InvalidPDFError):
        extract_text(b"this is not a real pdf file")


def test_extract_text_raises_on_no_extractable_text():
    pdf_bytes = _build_pdf(None)

    with pytest.raises(NoExtractableTextError):
        extract_text(pdf_bytes)
