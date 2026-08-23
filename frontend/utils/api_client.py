"""Thin HTTP client wrapping calls to the UniAssist-AI backend."""

import requests

from utils.config import CHAT_ENDPOINT, REQUEST_TIMEOUT_SECONDS


class BackendError(Exception):
    """Raised whenever the backend can't be reached or returns an error,
    so the UI layer can show one clean message instead of a raw
    traceback."""


def ask_question(question: str) -> dict:
    """
    Send a question to the backend's /chat endpoint and return its
    parsed JSON response.

    Any failure (backend not running, timeout, non-200 response, or an
    "error" field in an otherwise-200 response) is converted into a
    BackendError with a clear, user-facing message.
    """

    try:

        response = requests.post(
            CHAT_ENDPOINT,
            json={"question": question},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

    except requests.exceptions.ConnectionError:

        raise BackendError(
            "Could not reach the UniAssist-AI backend. "
            "Is it running? (uvicorn app.main:app --reload)"
        )

    except requests.exceptions.Timeout:

        raise BackendError(
            "The backend took too long to respond. Try again in a moment."
        )

    if response.status_code != 200:

        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text

        raise BackendError(
            f"Backend returned an error ({response.status_code}): {detail}"
        )

    data = response.json()

    if "error" in data:
        raise BackendError(data["error"])

    return data