import fitz

from app.core.errors import InvalidPDFError, NoExtractableTextError


def extract_text(pdf_bytes: bytes) -> str:
    try:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise InvalidPDFError("The uploaded file could not be read as a PDF.") from exc

    try:
        text = "".join(page.get_text() for page in document)
    except Exception as exc:
        raise InvalidPDFError("The uploaded PDF could not be parsed.") from exc
    finally:
        document.close()

    if not text.strip():
        raise NoExtractableTextError(
            "No extractable text was found in this PDF (it may be scanned or "
            "image-only; OCR is not supported)."
        )

    return text
