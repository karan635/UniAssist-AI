"""
Process-wide singleton dependencies for FastAPI routes.

Previously every route did e.g. `IndexManager()` / `ChatService()` inline,
which meant the HuggingFace embedding model was loaded from scratch and the
FAISS index re-deserialized from disk on *every single request*. These
`lru_cache`d getters make each of these heavy services a true singleton for
the lifetime of the process, while keeping the exact same construction
logic/behavior as before (they're still built lazily, on first use, using
the exact same constructors).

Routes pull these in via FastAPI's `Depends(...)`, so this doesn't change
any endpoint, request/response shape, or retrieval/generation logic -- only
*how many times* the underlying objects get built.

Deliberately using one shared IndexManager instance (rather than, say, a
separate one per ChatService) so that a call to POST /index/rebuild updates
the exact same in-memory index that /chat and /search subsequently query --
otherwise those routes could keep answering from a stale, pre-rebuild index
until the process restarted.
"""

from functools import lru_cache

from app.services.rag.index_manager import IndexManager
from app.services.ai.chat_service import ChatService
from app.services.knowledge.knowledge_manager import KnowledgeManager
from app.services.knowledge.pdf_loader import PDFLoaderService
from app.services.knowledge.registry_builder import RegistryBuilder


@lru_cache(maxsize=1)
def get_index_manager() -> IndexManager:
    return IndexManager()


@lru_cache(maxsize=1)
def get_chat_service() -> ChatService:
    return ChatService(index_manager=get_index_manager())


@lru_cache(maxsize=1)
def get_knowledge_manager() -> KnowledgeManager:
    return KnowledgeManager()


@lru_cache(maxsize=1)
def get_pdf_loader_service() -> PDFLoaderService:
    return PDFLoaderService()


@lru_cache(maxsize=1)
def get_registry_builder() -> RegistryBuilder:
    return RegistryBuilder()
