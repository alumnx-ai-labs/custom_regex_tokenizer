# Quickstart: Tokenizer Application

**Feature**: [spec.md](./spec.md) | **Contract**: [contracts/tokenize-api.md](./contracts/tokenize-api.md)

## Prerequisites

- Python 3.11+
- A virtual environment (recommended)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

## Run the backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Verify it is up:

```bash
curl http://localhost:8000/api/v1/encodings
# {"encodings": ["cl100k_base", "o200k_base", "p50k_base", "r50k_base"]}
```

## Run the frontend

In a second terminal:

```bash
cd frontend
export TOKENIZER_API_URL=http://localhost:8000
streamlit run app.py
```

Open the URL Streamlit prints (default `http://localhost:8501`).

## Validate User Story 1 — Tokenize pasted text

```bash
curl -s -X POST http://localhost:8000/api/v1/tokenize/text \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, tokenizer world!", "encoding": "cl100k_base"}' | python3 -m json.tool 2>/dev/null || true
```

**Expected**: HTTP 200 with `source_type: "text"`, a non-empty `tokens`
array, and `statistics.token_count` matching `len(tokens)`.

In the UI: paste the same text, select `cl100k_base`, click Tokenize, and
confirm the statistics section and token visualization both appear with
matching counts.

## Validate User Story 2 — Tokenize an uploaded TXT file

```bash
printf "Hello, tokenizer world!" > /tmp/sample.txt
curl -s -X POST http://localhost:8000/api/v1/tokenize/file \
  -F "file=@/tmp/sample.txt" \
  -F "encoding=cl100k_base"
```

**Expected**: HTTP 200, `source_type: "txt_file"`, `text` equal to the
file's contents.

In the UI: upload `/tmp/sample.txt`, select an encoding, click Tokenize, and
confirm the extracted text section shows the file's content.

## Validate User Story 3 — Tokenize an uploaded PDF

Use any small, text-based PDF (not scanned):

```bash
curl -s -X POST http://localhost:8000/api/v1/tokenize/file \
  -F "file=@/path/to/sample.pdf" \
  -F "encoding=cl100k_base"
```

**Expected**: HTTP 200, `source_type: "pdf_file"`, `text` containing the
PDF's extracted text.

## Validate error handling (SC-003)

```bash
# Empty text
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8000/api/v1/tokenize/text \
  -H "Content-Type: application/json" -d '{"text": "", "encoding": "cl100k_base"}'
# expect 400

# Unsupported encoding
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8000/api/v1/tokenize/text \
  -H "Content-Type: application/json" -d '{"text": "hi", "encoding": "not_a_real_encoding"}'
# expect 422

# Oversized upload (adjust path to a file > 5 MB)
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8000/api/v1/tokenize/file \
  -F "file=@/path/to/large-file.txt" -F "encoding=cl100k_base"
# expect 413
```

## Run automated tests

```bash
cd backend
pytest
```

**Expected**: unit tests (tokenizer + PDF extraction services), API tests
(all endpoints and error cases), and the integration test covering all
three user stories all pass.
