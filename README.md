# 🎓 UniAssist AI

**UniAssist AI** is a Retrieval-Augmented Generation (RAG) chatbot that answers university admission queries — eligibility, fees, scholarships, placements, courses, and academic calendars — by grounding every response in the institution's own PDF documents. It's built as a FastAPI backend paired with a Streamlit frontend.

> Currently configured for MCA admissions, with document ingestion for Admission, Fees, Placement, and Academic Calendar PDFs.

---

## ✨ Features

- **Document-grounded answers** — retrieves relevant sections from official PDFs before generating a response, reducing hallucination on facts like fees and eligibility.
- **FAISS vector search** — semantic retrieval over chunked and embedded document sections.
- **Query analysis & prompt routing** — classifies incoming questions (admission, eligibility, fees, placement, general) and routes them to a topic-specific prompt template.
- **Knowledge registry** — automatically builds a registry of available courses/topics from the documents in `backend/data/documents/`.
- **Groq-powered LLM** — fast inference via the Groq API.
- **Streamlit chat UI** — simple web interface for asking questions.
- **Modular FastAPI backend** — clean separation between document loading, chunking, embeddings, retrieval, prompting, and response building.

---

## 🏗️ Architecture

```
┌─────────────┐      HTTP       ┌──────────────────────────────────────┐
│  Streamlit   │  ───────────►  │              FastAPI backend          │
│  Frontend    │                │                                        │
└─────────────┘                │  Query Analyzer → Prompt Router         │
                                │         │                              │
                                │         ▼                              │
                                │  Index Manager (FAISS) ──► Retriever    │
                                │         │                              │
                                │         ▼                              │
                                │  Context Builder → Groq LLM Client      │
                                │         │                              │
                                │         ▼                              │
                                │  Response Builder → Citations           │
                                └──────────────────────────────────────┘
                                              │
                                              ▼
                                  backend/data/documents/*.pdf
```

Key pipeline stages:

1. **Document loading** (`services/rag/document_loader.py`, `services/knowledge/pdf_loader.py`) — reads PDFs from `backend/data/documents/`.
2. **Section splitting & chunking** (`services/rag/section_splitter.py`, `services/rag/chunk_service.py`) — splits documents into retrievable sections/chunks.
3. **Metadata tagging** (`services/knowledge/metadata_builder.py`) — tags chunks with course/topic metadata for filtered retrieval.
4. **Embedding & indexing** (`services/rag/embedding_service.py`, `services/rag/vector_store.py`, `services/rag/index_manager.py`) — builds and manages the FAISS index.
5. **Query analysis** (`services/ai/query_analyzer.py`) — classifies the incoming question.
6. **Retrieval** (`services/rag/retriever.py`) — fetches the most relevant chunks, filtered by metadata (`services/ai/metadata_filter.py`).
7. **Prompt routing** (`services/prompts/`) — picks a topic-specific prompt (admission, eligibility, fees, placement, general).
8. **Generation** (`services/ai/groq_client.py`) — calls the Groq-hosted LLM with the assembled context.
9. **Response building** (`services/ai/response_builder.py`) — formats the final answer with source metadata.

---

## 📁 Project Structure

```
UniAssist-AI/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/document.py       # Document chunking endpoint
│   │   │   └── v1/                      # Chat, search, query, index, registry, knowledge, pdf_loader
│   │   ├── core/                        # Config, constants, exceptions, logger
│   │   ├── services/
│   │   │   ├── ai/                      # Chat service, Groq client, query analyzer, prompt builder
│   │   │   ├── knowledge/               # Knowledge manager, metadata builder, registry builder
│   │   │   ├── prompts/                 # Topic-specific prompt templates
│   │   │   ├── rag/                     # Document loading, chunking, embeddings, FAISS index, retriever
│   │   │   └── shared/                  # Cache, file manager, helpers, validators
│   │   └── main.py                      # FastAPI app entrypoint
│   ├── data/documents/                  # Source PDFs (Admission, Fees, Placement, Academic Calendar)
│   └── requirements.txt
├── frontend/
│   ├── app.py                           # Streamlit chat UI
│   └── requirements.txt
├── docker-compose.yml
└── LICENSE
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- A [Groq API key](https://console.groq.com/)

### 1. Clone the repository

```bash
git clone https://github.com/karan635/UniAssist-AI.git
cd UniAssist-AI
```

### 2. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file inside `backend/` with the following variables (all required by `app/core/config.py`):

```env
APP_NAME=UniAssist AI
APP_VERSION=1.0.0
API_PREFIX=/api/v1

DEBUG=true
HOST=0.0.0.0
PORT=8000

GROQ_API_KEY=your_groq_api_key_here

MODEL_NAME=llama-3.3-70b-versatile
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

DOCUMENT_PATH=data/documents
VECTOR_PATH=data/vector_store

LANGUAGE=en
```

Run the API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`, with interactive docs at `http://localhost:8000/docs`.

### 3. Build the FAISS index

Before chatting, index the source PDFs:

```bash
curl -X POST http://localhost:8000/api/v1/index/rebuild
```

### 4. Frontend setup

```bash
cd frontend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The chat UI will open at `http://localhost:8501`.

---

## 🔌 API Reference

All routes are prefixed with `/api/v1`.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/chat` | Ask a question; returns a grounded answer with sources |
| `GET` | `/search?query=...` | Run retrieval only (no LLM call); returns matched documents & context |
| `GET` | `/analyze?query=...` | Classify a query's topic/intent |
| `POST` | `/index/rebuild` | Rebuild the FAISS index from source PDFs |
| `GET` | `/registry` | Get the built knowledge registry |
| `GET` | `/knowledge` | List loaded documents and available course topics |
| `GET` | `/pdf/load` | Load raw PDF documents with metadata |
| `GET` | `/chunks` | Preview document chunking output |

### Example: `/chat`

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the eligibility criteria for MCA admission?"}'
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | FastAPI, Uvicorn |
| LLM inference | Groq (Llama 3.3) |
| RAG / orchestration | LangChain, LangGraph |
| Vector store | FAISS |
| Embeddings | sentence-transformers |
| PDF parsing | pdfplumber, PyMuPDF, pypdf, pdfminer.six |
| Frontend | Streamlit |
| Config | Pydantic Settings, python-dotenv |

---

## 🗺️ Roadmap

- [ ] Wire up the Streamlit frontend to call the `/chat` API (currently a UI shell)
- [ ] Multi-institution support (BIT Mesra, Poornima, JECRC)
- [ ] WhatsApp integration for query handling
- [ ] Admin dashboard for document/index management
- [ ] Source citation display (PDF name + page number) in the UI
- [ ] Docker Compose services for backend + frontend

---

## 📄 License

See [LICENSE](./LICENSE).

---

## 🙋 Author

Built by [Karan](https://github.com/karan635) — MCA student, exploring RAG pipelines and applied LLM systems for real-world admissions use cases.

