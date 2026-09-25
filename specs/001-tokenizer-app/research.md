# Research: Tokenizer Application

**Feature**: [spec.md](./spec.md) | **Date**: 2026-09-16

All technical choices are fixed by the user's request and the project
constitution ([.specify/memory/constitution.md](../../.specify/memory/constitution.md)).
No open `NEEDS CLARIFICATION` items remain from the spec's Technical Context.
This document records the concrete decisions and the reasoning/alternatives
considered for each.

## Language & Runtime

- **Decision**: Python 3.11+ for both frontend and backend.
- **Rationale**: Single language across the whole stack per constitution;
  3.11+ gives modern typing (`X | Y` unions) which keeps Pydantic models and
  service signatures concise.
- **Alternatives considered**: None — mandated by constitution and user
  input.

## Backend Framework

- **Decision**: FastAPI, served by `uvicorn` in development.
- **Rationale**: Native Pydantic integration for explicit request/response
  schemas (constitution Principle VII), automatic OpenAPI docs for free,
  async-capable if ever needed, and a built-in `TestClient` (via `httpx`)
  that makes API tests fast and dependency-free of a running server.
- **Alternatives considered**: Flask (rejected — no native schema
  validation, would require manual Pydantic wiring anyway); Django REST
  Framework (rejected — far more machinery than a small stateless tool
  needs, violates Principle I/XIV).

## Frontend Framework

- **Decision**: Streamlit, calling the backend over HTTP using the
  `requests` library.
- **Rationale**: Streamlit is mandated and is well-suited to a form-and-
  results style tool (input controls → button → rendered output) with no
  custom JS needed.
- **Alternatives considered**: None — mandated.

## Tokenization

- **Decision**: `tiktoken`, loading one of the four supported encodings
  (`cl100k_base`, `o200k_base`, `p50k_base`, `r50k_base`) via
  `tiktoken.get_encoding(name)`.
- **Rationale**: Single source of truth for tokenization (constitution
  Principle V); `get_encoding` validates the name and raises on invalid
  input, which maps directly to FR-005's validation requirement.
- **Decoded token text**: `tiktoken`'s `Encoding.decode_single_token_bytes`
  (or decoding each token ID individually) is used to produce a per-token
  decoded string. Decoded bytes are converted to text with
  `errors="replace"` so that partial/invalid UTF-8 sequences (e.g., a token
  that is one byte of a multi-byte character) never raise, satisfying the
  spec's note that decoded text is "best available" rather than always
  clean.
- **Alternatives considered**: None — `tiktoken` is mandated as the single
  source of truth.

## PDF Text Extraction

- **Decision**: PyMuPDF (`fitz`), reading each page's text via
  `page.get_text()` and concatenating in page order.
- **Rationale**: PyMuPDF is fast, has no external system dependencies (unlike
  `pdftotext`/poppler), and its exceptions (`fitz.FileDataError`, etc.) map
  cleanly to a single "invalid/corrupted PDF" error case (FR-012). Pages with
  no extractable text simply contribute an empty string, and a document
  whose full extracted text is empty maps to the "no extractable text" case
  (FR-013) — matching the spec's decision to treat scanned/image-only PDFs
  this way without adding OCR.
- **Alternatives considered**: `pdfplumber` (rejected — slower, heavier
  dependency footprint for the same v1 need); `pypdf` (rejected — weaker
  text-extraction fidelity for typical text-based PDFs).

## File & Input Validation

- **Decision**: Backend-side validation only (constitution Principle VI),
  performed in a small `validation` module used by both endpoints:
  - Reject empty/whitespace-only text (FR-010).
  - Reject file extensions other than `.txt`/`.pdf` (FR-011).
  - Reject files (or decoded text payload) larger than 5 MB (FR-014,
    clarified 2026-09-16), checked against the actual byte length received,
    not a client-reported size.
  - Reject encodings not in the fixed supported set (FR-005).
- **Rationale**: The clarified 5 MB limit and the fixed four-encoding list
  are enforced identically regardless of client behavior, per Principle VI
  and FR-014. Checking actual byte length (not `Content-Length` headers)
  avoids trusting client-supplied metadata.
- **Alternatives considered**: Enforcing size limits only in Streamlit
  (rejected — explicitly disallowed by FR-014 and Principle VI).

## Error Handling Strategy

- **Decision**: A small set of domain error types (e.g.,
  `EmptyInputError`, `UnsupportedFileTypeError`, `InvalidPDFError`,
  `NoExtractableTextError`, `UnsupportedEncodingError`,
  `UploadTooLargeError`), each mapped to a distinct HTTP status code
  (400 for validation-style errors, 413 for oversized uploads, 422 for
  unsupported encoding, 500 reserved for genuinely unexpected internal
  errors) and a Pydantic-defined error response body with a `detail`
  message and an `error_code` field the frontend can branch on.
- **Rationale**: Satisfies FR-017 (distinct, user-readable errors per
  failure case) without needing exception-handling logic duplicated across
  endpoints — a single FastAPI exception handler per domain error type
  converts it to the right response.
- **Alternatives considered**: Returning HTTP 200 with an `ok: false` body
  for all failures (rejected — loses standard HTTP semantics and makes
  client-side branching less idiomatic for a REST API).

## Frontend/Backend Communication

- **Decision**: Streamlit calls FastAPI over plain HTTP using `requests`,
  with the backend base URL read from an environment variable
  (`TOKENIZER_API_URL`, default `http://localhost:8000`) so both processes
  can be started independently in local development.
- **Rationale**: Keeps the two processes decoupled (matches constitution
  Principle I/II) and requires no shared in-process imports between the
  Streamlit and FastAPI codebases.
- **Alternatives considered**: Importing backend service functions directly
  into Streamlit (rejected — violates Principle II/III by letting the
  frontend touch business logic directly, and would duplicate the
  request/response contract).

## Testing Approach

- **Decision**: `pytest` for all tests, split into:
  - Unit tests for the tokenizer service and PDF extraction service
    (Principle VIII), using small in-memory strings/bytes — no HTTP layer.
  - API tests using FastAPI's `TestClient` (`httpx`-based) against the app
    instance directly — no running server process needed (Principle IX).
  - A thin integration test that drives the same TestClient through each of
    the three user stories end-to-end (text, TXT upload, PDF upload) to
    confirm the full request → validation → extraction → tokenization →
    response path.
- **Rationale**: `TestClient` avoids the complexity of spinning up a real
  server for tests while still exercising real FastAPI routing, validation,
  and serialization.
- **Alternatives considered**: `unittest` (rejected — pytest is mandated and
  is friendlier for fixtures/parametrization).

## Performance & Scale

- **Decision**: No formal performance target for v1 (per clarified SC-007);
  the 5 MB upload limit and single-process local deployment are considered
  sufficient bounding for a small local tool.
- **Rationale**: Matches the explicit clarification that correctness and
  error handling take priority over speed for this version.
- **Alternatives considered**: N/A.
