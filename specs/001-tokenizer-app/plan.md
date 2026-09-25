# Implementation Plan: Tokenizer Application

**Branch**: `001-tokenizer-app` | **Date**: 2026-09-16 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-tokenizer-app/spec.md`

## Summary

Build a small, stateless web tool that tokenizes text using `tiktoken`. A
Streamlit frontend collects input three ways — pasted text, `.txt` upload,
or `.pdf` upload — plus an encoding choice, and calls a FastAPI backend over
REST/HTTP. The backend owns all tokenization and PDF-extraction logic,
validates input server-side (5 MB max on both uploads and direct text, four
supported encodings, non-empty text), and returns token IDs, decoded
tokens, and statistics. The
frontend renders every token individually and shows the extracted text for
uploads, with no database and no persisted state anywhere.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: FastAPI, uvicorn, Pydantic, tiktoken, PyMuPDF
(`fitz`), Streamlit, `requests` (frontend → backend HTTP client), `httpx`
(FastAPI `TestClient` dependency), pytest

**Storage**: N/A — stateless; no database or persisted files (FR-015)

**Testing**: pytest — unit tests, FastAPI `TestClient`-based API tests, and
an integration test covering all three user stories

**Target Platform**: Local development machine / simple single-host
deployment (two local processes: `uvicorn` + `streamlit run`)

**Project Type**: Web application (separate frontend + backend)

**Performance Goals**: None formally required for v1 (clarified, SC-007);
correctness and error handling take priority over speed

**Constraints**: 5 MB max size on both file uploads (FR-014, clarified) and
direct/pasted text measured as UTF-8 bytes (FR-019); stateless end-to-end
(FR-015); backend is the sole enforcement point for validation
(constitution Principle VI, which mandates text length limits as well as
file limits); frontend must not duplicate tokenization logic (constitution
Principle IV)

**Scale/Scope**: Single-user-per-request local tool; 3 input modes, 4 fixed
encodings, 2 backend endpoints (plus one encodings-listing endpoint), no
accounts/history

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
|---|---|---|
| I. Simple, Modular Architecture | Two services (Streamlit, FastAPI) over REST/HTTP only; no extra services/layers | PASS |
| II. Streamlit Is Presentation-Only | Frontend only collects input, calls API, renders results — see "Streamlit vs. FastAPI Responsibilities" below | PASS |
| III. FastAPI Owns Tokenization/Processing | All tokenization + PDF extraction lives in backend `services/` | PASS |
| IV. No Duplicated Tokenization Logic | Frontend never imports `tiktoken`; encoding list fetched/mirrored from backend contract | PASS |
| V. tiktoken Is Single Source of Truth | Only `tiktoken.get_encoding` used for all token operations | PASS |
| VI. Backend-Enforced Validation | Size (files AND direct text, FR-014/FR-019), type, encoding, empty-input checks all run server-side regardless of client | PASS |
| VII. Explicit API Contracts via Pydantic | All request/response/error bodies are Pydantic models (see contracts/tokenize-api.md) | PASS |
| VIII. Unit Tests for Tokenization/Extraction | Dedicated unit tests planned for tokenizer service and PDF service | PASS |
| IX. API Tests for Endpoints | `TestClient`-based tests planned for all endpoints/status codes | PASS |
| X. Graceful Handling of Bad Input | Domain error types map 1:1 to spec's error cases (empty, unsupported type, invalid/corrupted PDF, no text, bad encoding, oversized) | PASS |
| XI. No Unnecessary Persistence | No database; nothing written to disk beyond transient in-memory processing | PASS |
| XII. Local Dev / Simple Deployment | Two local processes, no orchestration, plain `pip install` + run commands | PASS |
| XIII. Readable Code Over Abstraction | Flat `services/` modules, no repository/factory/strategy patterns introduced | PASS |
| XIV. Scope Discipline | No auth, DB, OCR, LLM inference, or history — matches spec's explicit exclusions | PASS |

No violations. Complexity Tracking table is not needed.

## Streamlit vs. FastAPI Responsibilities

**Streamlit (frontend) owns**:
- Rendering the title, description, input-mode selector, text area/file
  uploader, encoding dropdown, and Tokenize button.
- Sending the user's text or file plus chosen encoding to the backend over
  HTTP (`requests`).
- Rendering the backend's response: extracted text (for uploads), token
  statistics, the per-token visualization, and any error message.
- Client-side UX conveniences only (e.g., disabling the button while a
  request is in flight) — never a substitute for backend validation.

**FastAPI (backend) owns**:
- All request/response schema definitions (Pydantic).
- Input validation: non-empty text, supported file type, 5 MB size limit,
  supported encoding.
- PDF text extraction (PyMuPDF) and its failure handling (corrupted PDF, no
  extractable text).
- Tokenization via `tiktoken` (encode, per-token decode, token IDs).
- Computing all statistics (character/word/token counts, ratios).
- Translating every failure mode into a distinct, structured error
  response.

## Project Structure

### Documentation (this feature)

```text
specs/001-tokenizer-app/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── tokenize-api.md  # Phase 1 output
└── tasks.md              # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── main.py                    # FastAPI app instance, route registration
│   ├── api/
│   │   └── tokenize_routes.py     # /api/v1/tokenize/text, /tokenize/file, /encodings
│   ├── schemas/
│   │   └── tokenize.py            # Pydantic request/response/error models
│   ├── services/
│   │   ├── tokenizer_service.py   # tiktoken encode/decode + statistics
│   │   ├── pdf_service.py         # PyMuPDF extraction
│   │   └── validation.py          # size/type/encoding/empty-text checks
│   ├── core/
│   │   ├── config.py              # MAX_UPLOAD_BYTES, SUPPORTED_ENCODINGS
│   │   └── errors.py              # domain exception types + FastAPI exception handlers
│   └── __init__.py
├── tests/
│   ├── unit/
│   │   ├── test_tokenizer_service.py
│   │   └── test_pdf_service.py
│   ├── api/
│   │   └── test_tokenize_routes.py
│   └── integration/
│       └── test_user_stories.py
└── requirements.txt

frontend/
├── app.py                # Streamlit page: layout, input controls, rendering
├── api_client.py          # Thin wrapper around `requests` calls to the backend
└── requirements.txt
```

**Structure Decision**: Web-application split (Option 2 shape) with
`backend/` and `frontend/` as two independent top-level projects, matching
constitution Principles I–III. The backend is further split into `api/`
(HTTP layer), `services/` (business logic — tokenization, PDF extraction,
validation), `schemas/` (Pydantic contracts), and `core/` (config +
error types), which is the minimum separation needed to keep FastAPI routes
thin without introducing repository/factory-style abstractions (Principle
XIII). The frontend stays as two files (`app.py` + `api_client.py`) since a
component/pages structure would be premature for three input modes and one
results view (Principle XIV).

## Complexity Tracking

*No constitution violations — table omitted.*
