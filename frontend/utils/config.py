"""Frontend configuration."""

import os

# Base URL of the UniAssist-AI FastAPI backend. Override via the
# BACKEND_URL environment variable if the backend runs somewhere other
# than localhost:8000 (e.g. a deployed server), instead of editing code.
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

CHAT_ENDPOINT = f"{BACKEND_URL}/api/v1/chat"

REQUEST_TIMEOUT_SECONDS = 60