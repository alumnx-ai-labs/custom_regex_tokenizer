---

description: "Task list for Tokenizer Application implementation"
---

# Tasks: Tokenizer Application

**Input**: Design documents from `/specs/001-tokenizer-app/`
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/tokenize-api.md](./contracts/tokenize-api.md), [quickstart.md](./quickstart.md)

**Tests**: Included — constitution Principles VIII/IX require unit tests for tokenization/PDF extraction and API tests for every endpoint.

**Organization**: Tasks are grouped by user story (from spec.md) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- File paths are exact and relative to the repository root

## Path Conventions

Per plan.md's "Structure Decision" (web application split):
- Backend: `backend/app/...`, `backend/tests/...`
- Frontend: `frontend/...`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create the directory skeleton: `backend/app/api/`, `backend/app/schemas/`, `backend/app/services/`, `backend/app/core/`, `backend/tests/unit/`, `backend/tests/api/`, `backend/tests/integration/`, `frontend/`
- [X] T002 Create `backend/requirements.txt` with `fastapi`, `uvicorn`, `pydantic`, `tiktoken`, `pymupdf`, `pytest`, `httpx`
- [X] T003 [P] Create `frontend/requirements.txt` with `streamlit`, `requests`
- [X] T004 [P] Create empty `backend/app/__init__.py`, `backend/app/api/__init__.py`, `backend/app/schemas/__init__.py`, `backend/app/services/__init__.py`, `backend/app/core/__init__.py`

**Checkpoint**: Project skeleton and dependency manifests exist.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create `backend/app/core/config.py` defining `MAX_UPLOAD_BYTES = 5 * 1024 * 1024` and `SUPPORTED_ENCODINGS = ["cl100k_base", "o200k_base", "p50k_base", "r50k_base"]` (FR-014, FR-004)
- [X] T006 Create `backend/app/core/errors.py` with domain exception classes (`EmptyInputError`, `UnsupportedFileTypeError`, `InvalidPDFError`, `NoExtractableTextError`, `UnsupportedEncodingError`, `UploadTooLargeError`), each carrying a `detail` message, plus FastAPI exception handler functions that convert each to the `ErrorResponse` shape with its documented HTTP status code (per contracts/tokenize-api.md's error table)
- [X] T007 [P] Create `backend/app/schemas/tokenize.py` with Pydantic models: `SupportedEncoding` (str enum, 4 values), `SourceType` (str enum: `text`, `txt_file`, `pdf_file`), `Token` (index, token_id, decoded_text), `TokenStatistics` (character_count, word_count, token_count, tokens_per_word, tokens_per_character), `TokenizationResult` (text, encoding, source_type, tokens, statistics), `TextTokenizeRequest` (text, encoding), `ErrorResponse` (error_code, detail) — per data-model.md
- [X] T008 Create `backend/app/services/tokenizer_service.py` with a `tokenize(text: str, encoding: str) -> TokenizationResult`-style function: loads the encoding via `tiktoken.get_encoding`, encodes `text`, builds the ordered `Token` list (decoding each token ID individually with `errors="replace"`), and computes `TokenStatistics` (character count via `len(text)`, word count via whitespace split, token count, tokens_per_word and tokens_per_character guarded against division by zero)
- [X] T009 Create `backend/app/services/validation.py` with `validate_encoding(encoding: str)`, `validate_non_empty_text(text: str)`, and `validate_upload_size(byte_length: int)` (used for both uploaded-file byte length and UTF-8-encoded direct-text length), each raising the corresponding exception from T006 when invalid (FR-005, FR-010, FR-014, FR-019)
- [X] T010 Create `backend/app/main.py`: instantiate the FastAPI app, register the exception handlers from T006, and include the router created in T011
- [X] T011 Create `backend/app/api/tokenize_routes.py` with a router exposing `GET /api/v1/encodings` returning `{"encodings": SUPPORTED_ENCODINGS}` (per contracts/tokenize-api.md)
- [X] T012 [P] Create `frontend/api_client.py` with a base HTTP helper reading `TOKENIZER_API_URL` (default `http://localhost:8000`) from the environment and a `get_encodings()` function calling `GET /api/v1/encodings`
- [X] T013 [P] Create `frontend/app.py` skeleton: application title, description, and an encoding `selectbox` populated from `api_client.get_encodings()`

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 - Tokenize Pasted Text (Priority: P1) 🎯 MVP

**Goal**: A user can type/paste text, pick an encoding, and see the full token breakdown and statistics.

**Independent Test**: Enter text directly, select an encoding, click Tokenize — verify token count, token list (index/ID/decoded text), and character/word statistics are returned and rendered, with no file upload involved.

### Tests for User Story 1 ⚠️

- [X] T014 [P] [US1] Unit test `backend/tests/unit/test_tokenizer_service.py`: verify `tokenize()` on a known short string returns the expected token count, correct token indices/IDs, decoded text that round-trips reasonably, and correct character/word/token ratios; include an edge case for a single-character/single-word input
- [X] T015 [P] [US1] API test `backend/tests/api/test_tokenize_routes.py`: `POST /api/v1/tokenize/text` returns 200 with `source_type: "text"` for valid input; returns 400 `empty_input` for empty/whitespace-only text; returns 422 `unsupported_encoding` for an invalid encoding name; returns 413 `upload_too_large` for text whose UTF-8 byte length exceeds 5 MB (FR-019)

### Implementation for User Story 1

- [X] T016 [US1] Add `POST /api/v1/tokenize/text` to `backend/app/api/tokenize_routes.py`: parse `TextTokenizeRequest`, call `validation.validate_upload_size` on `len(text.encode("utf-8"))`, `validation.validate_non_empty_text`, and `validation.validate_encoding`, call `tokenizer_service.tokenize`, return `TokenizationResult` with `source_type=SourceType.text` (FR-019)
- [X] T017 [US1] Add `tokenize_text(text, encoding)` to `frontend/api_client.py`, posting JSON to `POST /api/v1/tokenize/text` and raising/returning a parsed error (`error_code`/`detail`) on non-200 responses
- [X] T018 [US1] Add the "paste text" input control (text area + Tokenize button) to `frontend/app.py`, wired to `api_client.tokenize_text`, showing the error message inline when the call fails
- [X] T019 [US1] Render the statistics section (character count, word count, token count, tokens-per-word, tokens-per-character) and the token visualization (one row/chip per token showing index, token ID, and decoded text, visually distinguished per token, with none hidden or truncated) in `frontend/app.py`

**Checkpoint**: User Story 1 is fully functional and independently testable.

---

## Phase 4: User Story 2 - Tokenize an Uploaded Text File (Priority: P2)

**Goal**: A user can upload a `.txt` file and get the same token breakdown/statistics as pasted text, plus a view of the extracted text.

**Independent Test**: Upload a valid non-empty `.txt` file, select an encoding, click Tokenize — verify the extracted text, token results, and statistics are returned; also verify an empty file, a non-`.txt`/`.pdf` file, and an oversized file are each rejected with the correct error.

### Tests for User Story 2 ⚠️

- [X] T020 [P] [US2] API tests in `backend/tests/api/test_tokenize_routes.py` for `POST /api/v1/tokenize/file` with `.txt` uploads: 200 with `source_type: "txt_file"` and `text` equal to file contents for a valid file; 400 `empty_input` for an empty file; 400 `unsupported_file_type` for a `.csv`/other unsupported extension; 413 `upload_too_large` for a file over 5 MB

### Implementation for User Story 2

- [X] T021 [US2] Extend `backend/app/services/validation.py` with `validate_file_extension(filename: str)` (accepts only `.txt`/`.pdf`) raising `UnsupportedFileTypeError` otherwise (FR-011)
- [X] T022 [US2] Add `POST /api/v1/tokenize/file` to `backend/app/api/tokenize_routes.py`: accept `file: UploadFile` and `encoding: str` form fields; read the file bytes; call `validation.validate_upload_size` on the actual byte length, `validation.validate_file_extension`, and `validation.validate_encoding`; branch on the file extension — for `.txt`, decode bytes as UTF-8 (`errors="replace"`), call `validation.validate_non_empty_text`, then `tokenizer_service.tokenize`, returning `TokenizationResult` with `source_type=SourceType.txt_file`; for `.pdf`, import `backend.app.services.pdf_service` **lazily inside this branch** (not at module level) and call `pdf_service.extract_text` — the module doesn't exist yet (created in T028/US3), so a module-level import would break `.txt` handling and T020's tests until US3 lands; the deferred import keeps this endpoint fully working for `.txt` in the meantime
- [X] T023 [US2] Add `tokenize_file(file_bytes, filename, encoding)` to `frontend/api_client.py`, posting `multipart/form-data` to `POST /api/v1/tokenize/file` and parsing the same success/error shapes as `tokenize_text`
- [X] T024 [US2] Add an input-mode selector ("Paste text" / "Upload TXT file") to `frontend/app.py`; for the upload mode, add a `file_uploader` restricted to `.txt`, wired to `api_client.tokenize_file`
- [X] T025 [US2] Add an "Extracted Text" section to `frontend/app.py`, shown only when the result's `source_type` is a file-based source, displaying `TokenizationResult.text`

**Checkpoint**: User Stories 1 and 2 both work independently.

---

## Phase 5: User Story 3 - Tokenize an Uploaded PDF Document (Priority: P3)

**Goal**: A user can upload a text-based PDF and get the same token breakdown/statistics, with graceful handling of corrupted or scanned/image-only PDFs.

**Independent Test**: Upload a valid text-based PDF, select an encoding, click Tokenize — verify extracted text, token results, and statistics are returned; also verify a corrupted PDF and a scanned/image-only PDF are each rejected with the correct, distinct error.

### Tests for User Story 3 ⚠️

- [X] T026 [P] [US3] Unit tests in `backend/tests/unit/test_pdf_service.py`: extracting text from a small generated text-based PDF fixture returns non-empty text; opening a corrupted/non-PDF byte stream raises `InvalidPDFError`; a PDF fixture with no text content (e.g., generated with only an empty page) raises `NoExtractableTextError`
- [X] T027 [P] [US3] API tests in `backend/tests/api/test_tokenize_routes.py` for `POST /api/v1/tokenize/file` with `.pdf` uploads: 200 with `source_type: "pdf_file"` for a valid text-based PDF fixture; 400 `invalid_pdf` for a corrupted PDF fixture; 400 `no_extractable_text` for a text-less PDF fixture

### Implementation for User Story 3

- [X] T028 [US3] Create `backend/app/services/pdf_service.py` with `extract_text(pdf_bytes: bytes) -> str`: opens the bytes via `fitz.open(stream=pdf_bytes, filetype="pdf")` inside a try/except that raises `InvalidPDFError` on any open/parse failure, concatenates `page.get_text()` across all pages in order, and raises `NoExtractableTextError` if the stripped concatenated result is empty (FR-012, FR-013)
- [X] T029 [US3] Complete the `.pdf` branch in `POST /api/v1/tokenize/file` (`backend/app/api/tokenize_routes.py`): call `pdf_service.extract_text` on the uploaded bytes, then `validation.validate_non_empty_text` on the result, then `tokenizer_service.tokenize`, returning `TokenizationResult` with `source_type=SourceType.pdf_file`
- [X] T030 [US3] Extend the input-mode selector in `frontend/app.py` to add "Upload PDF file", with a `file_uploader` accepting `.pdf`, reusing the existing `api_client.tokenize_file` call and the "Extracted Text" section from US2

**Checkpoint**: All three user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that span multiple user stories

- [X] T031 [P] Integration test `backend/tests/integration/test_user_stories.py`: using FastAPI's `TestClient`, drive each of the three user stories end-to-end (text, `.txt` upload, `.pdf` upload) plus at least one error case per story, asserting on response status and shape; also assert statelessness (FR-015, SC-006) by sending two independent requests with different text and confirming the second response's `text`/`tokens`/`statistics` are unaffected by the first (e.g., the first request's text never appears in the second response), and by asserting no new files are written under the repo during either request
- [X] T032 [P] Add a top-level `README.md` summarizing setup/run commands (derived from [quickstart.md](./quickstart.md))
- [X] T033 Manually run through every scenario in [quickstart.md](./quickstart.md) (both curl commands and the Streamlit UI) and confirm actual behavior matches expected results
- [X] T034 [P] Review every `error_code`/`detail` message produced across `backend/app/core/errors.py` and the route handlers for clarity and consistency (FR-017)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories.
- **User Story 1 (Phase 3)**: Depends only on Foundational.
- **User Story 2 (Phase 4)**: Depends on Foundational; reuses the mode-selector and results-rendering scaffolding US1 adds to `frontend/app.py`, so implement after US1.
- **User Story 3 (Phase 5)**: Depends on Foundational; extends the same `/tokenize/file` endpoint and mode selector US2 introduces, so implement after US2.
- **Polish (Phase 6)**: Depends on all three user stories being complete.

### Within Each User Story

- Tests (T014/T015, T020, T026/T027) are written first and should fail before their corresponding implementation tasks.
- Services/validation before routes; routes before frontend wiring.

### Parallel Opportunities

- T003, T004 can run in parallel with each other (Setup).
- T007, T012, T013 can run in parallel with each other (Foundational) once T005/T006 exist.
- T014 and T015 can run in parallel (different files).
- T020 can run in parallel with any remaining Foundational polish, but must follow T005–T011.
- T026 and T027 can run in parallel with each other.

---

## Parallel Example: User Story 1

```bash
# Tests for User Story 1 together:
Task: "Unit test tokenizer_service in backend/tests/unit/test_tokenizer_service.py"
Task: "API test for POST /api/v1/tokenize/text in backend/tests/api/test_tokenize_routes.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (blocks everything else)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: run T014/T015, then manually exercise the "paste text" flow per quickstart.md
5. This is a demonstrable MVP: text in, tokens out.

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. Add User Story 1 → validate independently → demo (MVP)
3. Add User Story 2 → validate independently (still works without touching US1) → demo
4. Add User Story 3 → validate independently → demo
5. Phase 6 polish once all three stories are in place

## Notes

- [P] tasks touch different files and have no unmet dependencies.
- Tests are included per constitution Principles VIII (unit tests for tokenization/PDF extraction) and IX (API tests for endpoints) — commit them before their implementation task and confirm they fail first.
- Every task lists an exact file path so it is directly actionable.

---

## Phase 7: Convergence

- [X] T035 Add a content-sanity check for `.txt` uploads in `backend/app/services/validation.py` (e.g., reject if the bytes fail strict UTF-8 decoding, or the `errors="replace"` replacement-character ratio is high) and wire it into the `.txt` branch of `backend/app/api/tokenize_routes.py` so binary/non-text content renamed to `.txt` is rejected with a clear error instead of silently decoded and tokenized, per spec.md Edge Cases bullet 3 ("validate actual content, not just the file extension") (partial)
- [X] T036 Type the `encoding` parameter of `tokenize_file` in `backend/app/api/tokenize_routes.py` as `SupportedEncoding = Form(...)` instead of plain `str = Form(...)`, so FastAPI/OpenAPI declares and validates it the same way `TextTokenizeRequest.encoding` is validated on the JSON endpoint, per constitution Principle VII (partial)

---

## Phase 8: Convergence

- [X] T037 CRITICAL: Define an explicit Pydantic response model (e.g., `EncodingsResponse`) in `backend/app/schemas/tokenize.py` and set it as `response_model` on `GET /api/v1/encodings` in `backend/app/api/tokenize_routes.py`, which currently returns a plain `dict` — the only endpoint without an explicit Pydantic response schema — per constitution Principle VII ("Every backend request and response MUST be defined with explicit Pydantic models") (partial)
