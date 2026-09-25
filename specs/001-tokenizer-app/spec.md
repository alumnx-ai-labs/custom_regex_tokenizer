# Feature Specification: Tokenizer Application

**Feature Branch**: `001-tokenizer-app`

**Created**: 2026-09-16

**Status**: Draft

**Input**: User description: "Build a Tokenizer Application. The application allows a user to provide text through direct text input, TXT file upload, or PDF file upload. The application extracts the text and tokenizes it using the Python tiktoken library. Users can select from supported encodings (cl100k_base, o200k_base, p50k_base, r50k_base). The system tokenizes input, returns token IDs and decoded tokens, computes token/character/word statistics, and visualizes each token individually. The system must validate encodings, enforce upload size limits, and handle malformed input gracefully. No database, authentication, OCR, or LLM inference is in scope."

## Clarifications

### Session 2026-09-16

- Q: What should the maximum upload file size limit be for TXT/PDF uploads? → A: 5 MB
- Q: For very large inputs producing thousands of tokens, should the token visualization show every single token, or cap/paginate the display for usability? → A: Always show every token (no cap or pagination)
- Q: Is there a maximum acceptable response time for a tokenization request, or is there no explicit target for this version? → A: No explicit target for this version

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tokenize Pasted Text (Priority: P1)

A user wants to understand how a piece of text they type or paste directly
into the application gets broken into tokens, so they can reason about
token counts before using that text elsewhere (e.g., estimating cost or
context-window usage for an LLM).

**Why this priority**: This is the simplest and most immediate way to use
the tool and requires no file handling. It delivers the core value
(text → tokens) with the least friction and must work before any upload
feature is meaningful.

**Independent Test**: Can be fully tested by entering text directly into the
input area, choosing an encoding, and triggering tokenization — delivers a
complete token breakdown and statistics without needing any file upload
capability.

**Acceptance Scenarios**:

1. **Given** the application is open, **When** the user types or pastes text
   and selects an encoding and requests tokenization, **Then** the system
   displays the total token count, the list of tokens (with index, token ID,
   and decoded text), and the character/word statistics for that text.
2. **Given** the user has entered text, **When** the user changes the
   selected encoding and re-requests tokenization, **Then** the system
   returns updated results reflecting the newly selected encoding.
3. **Given** the input area is empty, **When** the user requests
   tokenization, **Then** the system shows a clear message explaining that
   text is required and performs no tokenization.

---

### User Story 2 - Tokenize an Uploaded Text File (Priority: P2)

A user has a `.txt` file and wants to know its token breakdown without
copying and pasting its contents manually.

**Why this priority**: File upload is a natural extension of the text-input
flow and is the simplest file-based path (no extraction step required),
making it the next most valuable capability after direct text input.

**Independent Test**: Can be fully tested by uploading a valid `.txt` file,
selecting an encoding, and requesting tokenization — delivers the same
statistics and token breakdown as direct text input, sourced from file
contents.

**Acceptance Scenarios**:

1. **Given** a valid, non-empty `.txt` file, **When** the user uploads it,
   selects an encoding, and requests tokenization, **Then** the system reads
   the file's text, displays the extracted text, and returns token results
   and statistics for that content.
2. **Given** an empty `.txt` file, **When** the user uploads it and requests
   tokenization, **Then** the system reports that the file contains no text
   to tokenize and performs no tokenization.
3. **Given** a file that is not a `.txt` or supported `.pdf` file, **When**
   the user attempts to upload it, **Then** the system rejects the file with
   a message stating the file type is unsupported.
4. **Given** a file larger than the maximum allowed upload size, **When**
   the user attempts to upload it, **Then** the system rejects the upload
   with a message stating the size limit and performs no tokenization.

---

### User Story 3 - Tokenize an Uploaded PDF Document (Priority: P3)

A user has a text-based PDF document and wants to see its token breakdown
without manually extracting the text themselves.

**Why this priority**: PDF handling delivers the same value as the other two
stories but requires an extra extraction step and carries the most failure
modes (corrupted files, scanned/image-only pages), so it is the most complex
and lowest-priority of the three input paths, though still core to the
product's purpose.

**Independent Test**: Can be fully tested by uploading a valid text-based PDF,
selecting an encoding, and requesting tokenization — delivers the extracted
text, token breakdown, and statistics, proving the extraction-then-tokenize
path independently of the other two input modes.

**Acceptance Scenarios**:

1. **Given** a valid, text-based PDF, **When** the user uploads it, selects
   an encoding, and requests tokenization, **Then** the system extracts the
   text, displays it, and returns token results and statistics for the
   extracted content.
2. **Given** a corrupted or unreadable PDF, **When** the user uploads it and
   requests tokenization, **Then** the system reports that the file could
   not be read and performs no tokenization.
3. **Given** a scanned or image-only PDF with no extractable text, **When**
   the user uploads it and requests tokenization, **Then** the system
   reports that no extractable text was found and performs no tokenization
   (optical character recognition is out of scope).

---

### Edge Cases

- What happens when the user requests tokenization without selecting an
  encoding, or selects an encoding that is not one of the supported options?
  → The system MUST reject the request with a message identifying the valid
  supported encodings.
- What happens when text (typed or extracted) contains only whitespace?
  → The system MUST treat it the same as empty input and report that text is
  required.
- What happens when an uploaded file's extension is disguised (e.g., a
  renamed file) or its content does not match its extension?
  → The system MUST validate actual content, not just the file extension,
  and reject files it cannot process with a clear error.
- What happens when a very large body of text or a large file produces an
  extremely high token count?
  → The system MUST still return complete, accurate results up to the
  defined maximum upload size; requests exceeding that size are rejected
  before processing.
- What happens when the underlying tokenization process fails unexpectedly
  (e.g., an internal error unrelated to user input)?
  → The system MUST report a generic, user-friendly error without exposing
  internal technical details, while still distinguishing this case from
  input-validation errors.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow a user to provide input text by typing
  or pasting it directly.
- **FR-002**: The system MUST allow a user to provide input by uploading a
  `.txt` file.
- **FR-003**: The system MUST allow a user to provide input by uploading a
  PDF file and extract its text automatically, limited to text-based PDFs
  (scanned/image-only PDFs are explicitly out of scope for text extraction).
- **FR-004**: The system MUST let the user choose an encoding from a fixed
  set of supported options (`cl100k_base`, `o200k_base`, `p50k_base`,
  `r50k_base`) before tokenizing.
- **FR-005**: The system MUST reject any tokenization request that specifies
  an encoding outside the supported set, with a message listing valid
  options.
- **FR-006**: The system MUST tokenize the provided or extracted text using
  the selected encoding and return, for each token: its position/index, its
  numeric token identifier, and its decoded text representation (when a
  decoded representation is available).
- **FR-007**: The system MUST return the total token count for the
  tokenized input.
- **FR-008**: The system MUST compute and return, for every successful
  tokenization: character count, word count, token count, tokens-per-word
  ratio, and tokens-per-character ratio.
- **FR-009**: The system MUST present every token individually to the user,
  with no cap or pagination on how many tokens are rendered, in a way that
  visually distinguishes one token from the next, showing each token's
  index, ID, and decoded text.
- **FR-010**: The system MUST reject tokenization requests where the
  resulting text (typed, pasted, or extracted) is empty or contains only
  whitespace, with a message indicating that text is required.
- **FR-011**: The system MUST reject uploaded files with unsupported file
  types, with a message identifying the supported types.
- **FR-012**: The system MUST detect and reject invalid or corrupted PDF
  files with a clear error message rather than failing silently or crashing.
- **FR-013**: The system MUST detect PDFs (or other uploads) that yield no
  extractable text and report this condition distinctly from a corrupted-file
  error.
- **FR-014**: The system MUST enforce a maximum upload size of 5 MB per file
  and reject uploads exceeding that size with a message stating the limit,
  regardless of any client-side size checks.
- **FR-019**: The system MUST enforce the same 5 MB maximum on directly
  typed/pasted text (measured as UTF-8 encoded byte length) and reject
  oversized text input with a message stating the limit, consistent with
  the file-upload limit in FR-014.
- **FR-015**: The system MUST NOT persist any user-provided text, uploaded
  files, or tokenization results beyond the lifetime of a single request;
  the application holds no state and uses no database.
- **FR-016**: The system MUST display the extracted text to the user when
  the input source is an uploaded file (TXT or PDF), so the user can verify
  what was actually tokenized.
- **FR-017**: The system MUST surface all rejected/failed operations
  (unsupported encoding, empty input, unsupported file type, corrupted file,
  no extractable text, oversized upload, unexpected internal error) as
  distinct, user-readable error messages rather than generic failures.
- **FR-018**: The system MUST report which encoding and which input source
  type (direct text, TXT upload, or PDF upload) were used for a given
  tokenization result.

### Key Entities

- **Tokenization Request**: Represents one attempt to tokenize input. Key
  attributes: the input source type (direct text, TXT upload, PDF upload),
  the selected encoding, and the raw or extracted text to be tokenized.
- **Tokenization Result**: Represents the outcome of a successful
  tokenization. Key attributes: the original/extracted text, the ordered
  list of tokens, the total token count, character count, word count,
  tokens-per-word, tokens-per-character, the encoding used, and the source
  type.
- **Token**: A single unit produced by tokenization. Key attributes: index
  (its position in the sequence), token ID (numeric identifier), and decoded
  text (human-readable representation, when available).
- **Supported Encoding**: One of the fixed, named tokenization schemes the
  user may select (`cl100k_base`, `o200k_base`, `p50k_base`, `r50k_base`).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can go from typing/pasting text to seeing a complete
  token breakdown and statistics in under 2 actions (select encoding,
  request tokenization) with no page reload or manual refresh required.
- **SC-002**: A user can upload a supported TXT or text-based PDF file and
  receive tokenization results without needing to manually extract or
  transcribe the file's text themselves.
- **SC-003**: 100% of invalid inputs described in the edge cases (empty
  text, unsupported file type, corrupted PDF, PDF with no extractable text,
  unsupported encoding, oversized upload) result in a clear, specific error
  message rather than a crash, blank result, or generic failure.
- **SC-004**: A user can visually distinguish every individual token in a
  tokenization result — with no tokens hidden, capped, or paginated out of
  view — and identify its index, ID, and decoded text at a glance.
- **SC-005**: Switching the selected encoding and re-tokenizing the same
  input produces updated results reflecting the newly selected encoding
  100% of the time.
- **SC-006**: No user text, files, or results are retrievable after a
  session ends or by any other user — confirming the system retains no data
  between requests.
- **SC-007**: This version defines no formal response-time target for
  tokenization requests; correctness and error handling take priority over
  speed for v1.

## Assumptions

- "Word count" is computed using standard whitespace-delimited word
  splitting; no language-specific word-segmentation is required for v1.
- "Approximate token percentage relative to input size" is satisfied by
  reporting tokens-per-character and tokens-per-word ratios; no additional
  normalized "percentage" metric beyond these ratios is required.
- Only the four listed tiktoken encodings need to be supported in this
  version; adding further encodings is a future enhancement.
- Optical character recognition (OCR) for scanned/image-only PDFs is
  explicitly out of scope; such files are treated as containing no
  extractable text.
- The application serves a single user per request with no concept of
  accounts, sessions, or saved history; every request is independent and
  stateless.
- "Decoded token text" may not always be a clean human-readable string
  (e.g., partial byte sequences or control characters); the system returns
  the best available decoded representation without guaranteeing
  print-safe output for every token.
