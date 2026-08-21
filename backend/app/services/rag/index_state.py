"""Incremental-indexing state.

Tracks, per source PDF, a content hash and the list of FAISS vector IDs
that came from it. This is what lets /index/rebuild skip re-chunking and
re-embedding files that haven't changed, instead of reprocessing the
entire document corpus on every call.

The manifest is a small JSON file stored alongside the FAISS index
itself (VECTOR_PATH/manifest.json), so it stays in sync with whichever
index it describes.
"""

import hashlib
import json
from pathlib import Path
from typing import Dict


def hash_file(path: Path, chunk_size: int = 65536) -> str:
    """
    SHA-256 hash of a file's raw bytes.

    Hashing the actual PDF bytes (rather than, say, the extracted text)
    means this is completely deterministic and unaffected by anything
    downstream (OCR variance, extraction library changes, etc.) -- any
    change to the file on disk, however small, changes the hash.

    Read in chunks so large PDFs don't need to be fully loaded into
    memory just to be hashed.
    """

    digest = hashlib.sha256()

    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk_size), b""):
            digest.update(block)

    return digest.hexdigest()


def load_manifest(manifest_path: Path) -> Dict:
    """
    Load the indexing manifest.

    Returns an empty manifest structure if the file doesn't exist yet
    (first run) or can't be parsed (corrupted/manually edited) -- this
    never raises, since the worst consequence of a bad manifest should
    be "falls back to reprocessing everything," not a crash.
    """

    if not manifest_path.exists():
        return {"files": {}}

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"files": {}}

    if not isinstance(data, dict) or "files" not in data:
        return {"files": {}}

    return data


def save_manifest(manifest_path: Path, manifest: Dict) -> None:

    manifest_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)