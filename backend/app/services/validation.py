import os

from app.core.config import MAX_UPLOAD_BYTES, SUPPORTED_ENCODINGS
from app.core.errors import (
    EmptyInputError,
    UnsupportedEncodingError,
    UnsupportedFileTypeError,
    UploadTooLargeError,
)

SUPPORTED_FILE_EXTENSIONS = {".txt", ".pdf"}


def validate_encoding(encoding: str) -> None:
    if encoding not in SUPPORTED_ENCODINGS:
        raise UnsupportedEncodingError(
            f"Unsupported encoding '{encoding}'. Supported encodings: "
            f"{', '.join(SUPPORTED_ENCODINGS)}."
        )


def validate_non_empty_text(text: str) -> None:
    if not text or not text.strip():
        raise EmptyInputError("Text is required and cannot be empty or whitespace-only.")


def validate_upload_size(byte_length: int) -> None:
    if byte_length > MAX_UPLOAD_BYTES:
        raise UploadTooLargeError(
            f"Input exceeds the maximum allowed size of {MAX_UPLOAD_BYTES} bytes (5 MB)."
        )


def validate_file_extension(filename: str) -> None:
    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in SUPPORTED_FILE_EXTENSIONS:
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{ext or filename}'. Supported types: "
            f"{', '.join(sorted(SUPPORTED_FILE_EXTENSIONS))}."
        )


def decode_text_file_content(file_bytes: bytes) -> str:
    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UnsupportedFileTypeError(
            "This .txt upload does not contain valid UTF-8 text content; it may "
            "be a binary or non-text file with a misleading extension."
        ) from exc
