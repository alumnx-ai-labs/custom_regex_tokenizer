import os

import requests

API_BASE_URL = os.environ.get("TOKENIZER_API_URL", "http://localhost:8000")


class ApiError(Exception):
    def __init__(self, error_code: str, detail: str):
        self.error_code = error_code
        self.detail = detail
        super().__init__(detail)


def _raise_for_error(response: requests.Response) -> None:
    if response.ok:
        return
    try:
        body = response.json()
        error_code = body.get("error_code", "internal_error")
        detail = body.get("detail", "An unknown error occurred.")
    except ValueError:
        error_code = "internal_error"
        detail = f"Unexpected response from server (status {response.status_code})."
    raise ApiError(error_code, detail)


def get_encodings() -> list[str]:
    response = requests.get(f"{API_BASE_URL}/api/v1/encodings")
    _raise_for_error(response)
    return response.json()["encodings"]


def tokenize_text(text: str, encoding: str) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/api/v1/tokenize/text",
        json={"text": text, "encoding": encoding},
    )
    _raise_for_error(response)
    return response.json()


def tokenize_file(file_bytes: bytes, filename: str, encoding: str) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/api/v1/tokenize/file",
        files={"file": (filename, file_bytes)},
        data={"encoding": encoding},
    )
    _raise_for_error(response)
    return response.json()
