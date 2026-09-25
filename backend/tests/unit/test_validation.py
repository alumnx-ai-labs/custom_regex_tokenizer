import pytest

from app.core.errors import UnsupportedFileTypeError
from app.services.validation import decode_text_file_content


def test_decode_text_file_content_valid_utf8():
    assert decode_text_file_content(b"Hello, world!") == "Hello, world!"


def test_decode_text_file_content_rejects_invalid_utf8():
    with pytest.raises(UnsupportedFileTypeError):
        decode_text_file_content(bytes([0xFF, 0xFE, 0x00, 0x80, 0x81]))
