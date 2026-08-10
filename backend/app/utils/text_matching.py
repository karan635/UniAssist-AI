"""Shared text-matching helpers used across the ingestion and retrieval
pipeline.

These were previously duplicated (and subtly inconsistent) in
document_loader.py, retriever.py, and section_splitter.py -- each one
normalized filenames differently (some stripped spaces, none stripped
underscores), so a file like "Academic_Calendar_SP2026.pdf" could be
missed by some checks and matched by others. Centralizing here keeps
detection consistent everywhere it's used.
"""


def normalize_filename(filename: str) -> str:
    """Lowercase and strip spaces/underscores/hyphens for loose matching."""

    return (
        str(filename or "")
        .lower()
        .replace(" ", "")
        .replace("_", "")
        .replace("-", "")
    )


def is_academic_calendar_filename(filename: str) -> bool:
    """True if a filename looks like an academic calendar document."""

    return "academiccalendar" in normalize_filename(filename)
