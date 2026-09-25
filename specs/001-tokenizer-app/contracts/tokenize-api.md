# API Contract: Tokenizer Backend

**Feature**: [../spec.md](../spec.md) | **Data model**: [../data-model.md](../data-model.md)

Base path: `/api/v1`. All request/response bodies are JSON except the file
upload endpoint, which uses `multipart/form-data`. All schemas below are
Pydantic models (constitution Principle VII).

## GET /api/v1/encodings

Returns the fixed list of supported encodings, so the frontend never
hardcodes it separately from the backend (constitution Principle IV).

**Response 200**:
```json
{
  "encodings": ["cl100k_base", "o200k_base", "p50k_base", "r50k_base"]
}
```

## POST /api/v1/tokenize/text

Tokenizes directly provided text. Covers User Story 1 (FR-001).

**Request body** (`TextTokenizeRequest`):
```json
{
  "text": "string, required",
  "encoding": "cl100k_base | o200k_base | p50k_base | r50k_base"
}
```

**Response 200** (`TokenizationResult`, see data-model.md): `source_type`
is always `"text"`.

**Error responses** (`ErrorResponse`, see data-model.md):
| Status | error_code | Condition |
|---|---|---|
| 400 | `empty_input` | `text` is empty or whitespace-only (FR-010) |
| 413 | `upload_too_large` | `text`, measured as UTF-8 encoded bytes, exceeds 5 MB (FR-019) |
| 422 | `unsupported_encoding` | `encoding` not in the supported set (FR-005) |
| 500 | `internal_error` | Unexpected failure during tokenization (edge case) |

## POST /api/v1/tokenize/file

Tokenizes an uploaded `.txt` or `.pdf` file. Covers User Stories 2 & 3
(FR-002, FR-003).

**Request**: `multipart/form-data` with:
- `file`: the uploaded file (required)
- `encoding`: form field, one of the supported encodings (required)

**Response 200** (`TokenizationResult`): `source_type` is `"txt_file"` or
`"pdf_file"` depending on the uploaded file's extension. `text` contains the
extracted file content (FR-016).

**Error responses** (`ErrorResponse`):
| Status | error_code | Condition |
|---|---|---|
| 400 | `empty_input` | Extracted/file text is empty or whitespace-only (FR-010) |
| 400 | `unsupported_file_type` | File extension is not `.txt` or `.pdf` (FR-011) |
| 400 | `invalid_pdf` | PDF cannot be opened/parsed (corrupted/malformed) (FR-012) |
| 400 | `no_extractable_text` | PDF opened successfully but yields no text, e.g. scanned/image-only (FR-013) |
| 413 | `upload_too_large` | File exceeds the 5 MB limit (FR-014) |
| 422 | `unsupported_encoding` | `encoding` not in the supported set (FR-005) |
| 500 | `internal_error` | Unexpected failure during extraction/tokenization |

## Notes for the frontend (Streamlit)

- The frontend MUST call `GET /api/v1/encodings` (or hold the same fixed
  list only as a display concern) rather than reimplementing tokenization
  logic — it never tokenizes locally (constitution Principle IV).
- The frontend renders `error_code`/`detail` from `ErrorResponse` directly;
  it does not need to re-derive error meaning from HTTP status codes alone.
- Every token in `TokenizationResult.tokens` MUST be rendered — no
  client-side truncation (FR-009, clarified 2026-09-16).
