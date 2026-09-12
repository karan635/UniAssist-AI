# UniAssist AI — React Frontend

A second frontend for the same FastAPI backend used by the Streamlit app.
Same `/api/v1/chat` and `/api/v1/leads` endpoints, no backend changes needed
beyond enabling CORS (see below).

## 1. Enable CORS on the backend (one-time)

The FastAPI backend currently has no CORS middleware, so browser requests
from Vite's dev server will be blocked. In
`backend/app/main.py`, add:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # add your deployed frontend URL too
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Add this right after `app = FastAPI(...)`, before the `include_router` calls.

## 2. Run the frontend

```bash
cd frontend-react
npm install
cp .env.example .env      # edit VITE_BACKEND_URL if your backend isn't on :8000
npm run dev
```

Opens at `http://localhost:5173`. Make sure the backend is already running
(`uvicorn app.main:app --reload` from `backend/`).

## 3. What's implemented

- Chat with history, matching the Streamlit app's `/chat` flow
- Source citations (filename + page), collapsible per answer
- A `session_id` per browser tab, sent with every request — this is what
  lets the backend's lead-intent tracker fire `lead_prompt` (the Streamlit
  frontend never sent a session_id, so it never got this)
- Lead-capture modal: opens automatically when `lead_prompt` is true, or
  manually via the "Talk to admissions" sidebar button — both POST to
  `/api/v1/leads`

## Not yet ported

- Voice input/output: the backend's `/voice/transcribe` exists, but
  `/voice/speak` referenced in the Streamlit config isn't implemented yet.
  Worth adding once that's built out.
