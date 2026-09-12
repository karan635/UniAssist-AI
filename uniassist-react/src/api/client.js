// Thin fetch wrapper around the UniAssist-AI FastAPI backend.
// Mirrors frontend/utils/api_client.py so both frontends hit the
// same endpoints the same way.

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

const CHAT_ENDPOINT = `${BACKEND_URL}/api/v1/chat`;
const LEADS_ENDPOINT = `${BACKEND_URL}/api/v1/leads`;

export class BackendError extends Error {}

async function parseErrorResponse(response) {
  try {
    const data = await response.json();
    return data.detail || data.error || response.statusText;
  } catch {
    return response.statusText;
  }
}

export async function askQuestion(question, sessionId) {
  let response;

  try {
    response = await fetch(CHAT_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, session_id: sessionId }),
    });
  } catch (err) {
    throw new BackendError(
      "Could not reach the UniAssist-AI backend. Is it running? (uvicorn app.main:app --reload)"
    );
  }

  if (!response.ok) {
    const detail = await parseErrorResponse(response);
    throw new BackendError(`Backend returned an error (${response.status}): ${detail}`);
  }

  const data = await response.json();

  if (data.error) {
    throw new BackendError(data.error);
  }

  return data;
}

export async function submitLead(lead) {
  let response;

  try {
    response = await fetch(LEADS_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(lead),
    });
  } catch (err) {
    throw new BackendError("Could not reach the UniAssist-AI backend.");
  }

  if (!response.ok) {
    const detail = await parseErrorResponse(response);
    throw new BackendError(`Could not submit your details (${response.status}): ${detail}`);
  }

  return response.json();
}
