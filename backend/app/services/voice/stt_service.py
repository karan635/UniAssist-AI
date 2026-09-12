"""Speech-to-text using Groq's Whisper API.

Uses the same GROQ_API_KEY you already have configured for chat --
Whisper transcription is a separate endpoint on the same Groq account,
not a separate service to sign up for.
"""

from groq import Groq

from app.core.config import settings
from app.core.logger import logger


class STTService:

    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)

    def transcribe(self, audio_bytes: bytes, filename: str = "audio.wav") -> dict:
        """
        audio_bytes: raw audio file content (wav/mp3/m4a -- Whisper
        accepts all common formats).

        Returns: {"text": "...", "language": "en"}  -- language is
        Whisper's own auto-detected ISO-639-1 code, so the same spoken
        language naturally gets used again for the TTS reply, without
        needing your own language-detection logic to be fully wired up.
        """

        try:
            result = self.client.audio.transcriptions.create(
                file=(filename, audio_bytes),
                model="whisper-large-v3",
                response_format="verbose_json",  # includes detected language
            )

            return {
                "text": result.text.strip(),
                "language": getattr(result, "language", "en"),
            }

        except Exception as e:
            logger.error(f"[STT] Transcription failed: {e}")
            raise