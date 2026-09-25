# Data Model: Tokenizer Application

**Feature**: [spec.md](./spec.md) | **Date**: 2026-09-16

All entities below are transient request/response shapes (Pydantic models on
the backend). None are persisted (constitution Principle XI / FR-015);
each exists only for the lifetime of a single HTTP request.

## SupportedEncoding

A fixed enumeration of the tokenizer encodings the user may select.

| Field | Type | Notes |
|---|---|---|
| value | `str` (enum) | One of `cl100k_base`, `o200k_base`, `p50k_base`, `r50k_base` |

**Validation rule**: any value outside this fixed set is rejected with an
`UnsupportedEncodingError` (FR-004, FR-005).

## SourceType

A fixed enumeration describing where the tokenized text came from.

| Field | Type | Notes |
|---|---|---|
| value | `str` (enum) | One of `text`, `txt_file`, `pdf_file` |

Used to satisfy FR-018 (report which input source produced a result).

## TokenizationRequest

Represents one attempt to tokenize input. Two concrete shapes exist at the
API boundary (see [contracts/tokenize-api.md](./contracts/tokenize-api.md)),
but both resolve to this same logical shape before reaching the tokenizer
service.

| Field | Type | Notes |
|---|---|---|
| text | `str` | Raw or already-extracted text to tokenize. Required, non-empty after whitespace-stripping (FR-010). |
| encoding | `SupportedEncoding` | Selected tiktoken encoding (FR-004). |
| source_type | `SourceType` | How this text was obtained (FR-018). |

**Validation rules**:
- `text` stripped of whitespace MUST be non-empty (FR-010).
- `encoding` MUST be one of `SupportedEncoding` (FR-005).
- For file-based requests, the originating file's byte size MUST NOT exceed
  5 MB (FR-014), checked before extraction/tokenization is attempted.
- For direct-text requests, `text` encoded as UTF-8 MUST NOT exceed 5 MB
  (FR-019), checked before tokenization is attempted.

## Token

A single unit produced by tokenizing text with a given encoding.

| Field | Type | Notes |
|---|---|---|
| index | `int` | Zero-based position of this token in the sequence (FR-006). |
| token_id | `int` | Numeric identifier tiktoken assigned to this token (FR-006). |
| decoded_text | `str` | Best-available decoded representation of this token (FR-006); may contain replacement characters for partial byte sequences (see research.md). |

## TokenStatistics

Aggregate counts and ratios computed for one tokenization result.

| Field | Type | Notes |
|---|---|---|
| character_count | `int` | Length of the tokenized text in characters (FR-008). |
| word_count | `int` | Count of whitespace-delimited words (FR-008; see spec Assumptions). |
| token_count | `int` | Total number of tokens produced (FR-007, FR-008). |
| tokens_per_word | `float` | `token_count / word_count`; `0.0` if `word_count` is `0` (guarded, though empty input is rejected before this point). |
| tokens_per_character | `float` | `token_count / character_count`; `0.0` if `character_count` is `0`. |

## TokenizationResult

The full outcome of a successful tokenization, returned to the frontend.

| Field | Type | Notes |
|---|---|---|
| text | `str` | The original (direct input) or extracted (file upload) text that was tokenized (FR-016 for file sources). |
| encoding | `SupportedEncoding` | Encoding used (FR-018). |
| source_type | `SourceType` | Input source used (FR-018). |
| tokens | `list[Token]` | Every token produced, in order, with no cap or truncation (FR-009, clarified 2026-09-16). |
| statistics | `TokenStatistics` | See above (FR-008). |

## ErrorResponse

Uniform shape for every rejected/failed request (FR-017).

| Field | Type | Notes |
|---|---|---|
| error_code | `str` (enum) | One of `empty_input`, `unsupported_file_type`, `invalid_pdf`, `no_extractable_text`, `unsupported_encoding`, `upload_too_large`, `internal_error`. |
| detail | `str` | Human-readable message describing the specific problem (e.g., naming the valid encodings, or stating the size limit). |

## Entity Relationships

```
TokenizationRequest --(processed by tokenizer service)--> TokenizationResult
TokenizationResult *---- 1..* ----* Token
TokenizationResult ---- 1 ---- TokenStatistics
(any validation/processing failure short-circuits to) --> ErrorResponse
```

There are no relationships beyond this single request/response lifecycle —
no entity outlives one HTTP call, and no entity references another user's
data (constitution Principle XI, FR-015, SC-006).
