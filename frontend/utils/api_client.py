"""Thin HTTP client wrapping calls to the UniAssist-AI backend."""

import requests

from utils.config import (
    CHAT_ENDPOINT,
    VOICE_TRANSCRIBE_ENDPOINT,
    VOICE_SPEAK_ENDPOINT,
    REQUEST_TIMEOUT_SECONDS,
)


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


def transcribe_audio(audio_bytes: bytes, filename: str = "recording.wav") -> dict:
    """
    Send recorded audio to the backend's /voice/transcribe endpoint.

    Returns: {"text": "...", "language": "en"} -- language is Whisper's
    own auto-detected code, used later to make the spoken reply come
    back in the same language.
    """

    try:

        files = {"file": (filename, audio_bytes, "audio/wav")}

        response = requests.post(
            VOICE_TRANSCRIBE_ENDPOINT,
            files=files,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

    except requests.exceptions.ConnectionError:

        raise BackendError(
            "Could not reach the UniAssist-AI backend. "
            "Is it running? (uvicorn app.main:app --reload)"
        )

    except requests.exceptions.Timeout:

        raise BackendError(
            "Transcription took too long. Try again in a moment."
        )

    if response.status_code != 200:

        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text

        raise BackendError(
            f"Transcription failed ({response.status_code}): {detail}"
        )

    return response.json()


def synthesize_speech(text: str, language: str = "en") -> bytes:
    """
    Send text to the backend's /voice/speak endpoint and return raw
    MP3 audio bytes, ready to hand to st.audio().
    """

    try:

        response = requests.post(
            VOICE_SPEAK_ENDPOINT,
            json={"text": text, "language": language},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

    except requests.exceptions.ConnectionError:

        raise BackendError(
            "Could not reach the UniAssist-AI backend. "
            "Is it running? (uvicorn app.main:app --reload)"
        )

    except requests.exceptions.Timeout:

        raise BackendError(
            "Speech synthesis took too long. Try again in a moment."
        )

    if response.status_code != 200:

        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text

        raise BackendError(
            f"Speech synthesis failed ({response.status_code}): {detail}"
        )

    return response.content