import os

from fastapi import APIRouter, File, Form, UploadFile

from app.core.config import SUPPORTED_ENCODINGS
from app.schemas.tokenize import (
    EncodingsResponse,
    SourceType,
    SupportedEncoding,
    TextTokenizeRequest,
    TokenizationResult,
)
from app.services import tokenizer_service, validation

router = APIRouter(prefix="/api/v1")


@router.get("/encodings", response_model=EncodingsResponse)
def get_encodings() -> EncodingsResponse:
    return EncodingsResponse(encodings=SUPPORTED_ENCODINGS)


@router.post("/tokenize/text", response_model=TokenizationResult)
def tokenize_text(request: TextTokenizeRequest) -> TokenizationResult:
    validation.validate_upload_size(len(request.text.encode("utf-8")))
    validation.validate_non_empty_text(request.text)
    validation.validate_encoding(request.encoding)
    return tokenizer_service.tokenize(request.text, request.encoding, SourceType.text)


@router.post("/tokenize/file", response_model=TokenizationResult)
async def tokenize_file(
    file: UploadFile = File(...), encoding: SupportedEncoding = Form(...)
) -> TokenizationResult:
    file_bytes = await file.read()

    validation.validate_upload_size(len(file_bytes))
    validation.validate_file_extension(file.filename)
    validation.validate_encoding(encoding)

    ext = os.path.splitext(file.filename or "")[1].lower()

    if ext == ".pdf":
        from app.services import pdf_service

        text = pdf_service.extract_text(file_bytes)
        source_type = SourceType.pdf_file
    else:
        text = validation.decode_text_file_content(file_bytes)
        source_type = SourceType.txt_file

    validation.validate_non_empty_text(text)
    return tokenizer_service.tokenize(text, encoding, source_type)
