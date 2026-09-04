"""
Run this once from your backend folder to inspect exactly what got
indexed for Admission_Btech.pdf -- helps confirm whether the real
Eligibility section exists as a chunk, and if so, why it isn't
matching the "eligibility"/"eligible" keyword check.

Usage: python debug_btech_chunks.py
"""

from app.services.rag.embedding_service import EmbeddingService
from langchain_community.vectorstores import FAISS
from app.core.config import settings

embedding_service = EmbeddingService()
embeddings = embedding_service.get_embeddings()

db = FAISS.load_local(
    settings.VECTOR_PATH,
    embeddings,
    allow_dangerous_deserialization=True,
)

all_docs = list(db.docstore._dict.values())

btech_docs = [
    doc for doc in all_docs
    if str(doc.metadata.get("filename", "")).lower() == "admission_btech.pdf"
]

print(f"Total chunks for Admission_Btech.pdf: {len(btech_docs)}\n")

# Sort by chunk number so pages print in document order
def chunk_number(doc):
    chunk_id = str(doc.metadata.get("chunk_id", ""))
    try:
        return int(chunk_id.rsplit("__", 1)[-1])
    except (ValueError, IndexError):
        return 0

btech_docs.sort(key=chunk_number)

for doc in btech_docs:
    metadata = doc.metadata
    text = doc.page_content
    has_eligibility_word = "eligib" in text.lower()

    print("=" * 60)
    print("CHUNK ID:", metadata.get("chunk_id"))
    print("PAGE:", metadata.get("page_label"))
    print("TOPIC:", metadata.get("topic"))
    print("SECTION:", metadata.get("section"))
    print("Contains 'eligib...':", has_eligibility_word)
    print("TEXT PREVIEW:")
    print(text[:300])
    print()