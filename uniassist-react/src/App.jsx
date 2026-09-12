import { useEffect, useRef, useState } from "react";
import Sidebar from "./components/Sidebar.jsx";
import MessageBubble from "./components/MessageBubble.jsx";
import LeadModal from "./components/LeadModal.jsx";
import { askQuestion, BackendError } from "./api/client.js";

// One session id per browser tab, sent with every /chat call so the
// backend's lead-intent tracker can build interest signal across turns.
// Same behaviour the backend expects; the Streamlit frontend just never
// sent one, so it never got lead_prompt at all.
function getSessionId() {
  const key = "uniassist_session_id";
  let id = sessionStorage.getItem(key);
  if (!id) {
    id = crypto.randomUUID();
    sessionStorage.setItem(key, id);
  }
  return id;
}

export default function App() {
  const [history, setHistory] = useState([]);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const [leadModal, setLeadModal] = useState({ open: false, source: "form" });
  const sessionId = useRef(getSessionId());
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [history, thinking]);

  async function handleSend(e) {
    e.preventDefault();
    const question = input.trim();
    if (!question || thinking) return;

    setInput("");
    setHistory((h) => [...h, { role: "user", content: question }]);
    setThinking(true);

    try {
      const data = await askQuestion(question, sessionId.current);

      setHistory((h) => [
        ...h,
        { role: "assistant", content: data.answer, documents: data.documents_used },
      ]);

      if (data.lead_prompt) {
        setLeadModal({ open: true, source: "auto" });
      }
    } catch (err) {
      const message = err instanceof BackendError ? err.message : "Something went wrong.";
      setHistory((h) => [...h, { role: "assistant", content: message, isError: true }]);
    } finally {
      setThinking(false);
    }
  }

  function handleClear() {
    setHistory([]);
  }

  return (
    <div className="app">
      <Sidebar
        onClear={handleClear}
        onTalkToAdmissions={() => setLeadModal({ open: true, source: "form" })}
      />

      <main className="chat">
        <header className="chat__header">
          <h1>UniAssist AI</h1>
          <p>Your AI university admission assistant</p>
        </header>

        <div className="chat__messages" ref={scrollRef}>
          {history.length === 0 && (
            <div className="chat__empty">
              Ask anything about admissions, eligibility, fees, or placements.
            </div>
          )}

          {history.map((m, i) => (
            <MessageBubble key={i} role={m.role} content={m.content} documents={m.documents} isError={m.isError} />
          ))}

          {thinking && (
            <div className="message-row">
              <div className="message-avatar">UA</div>
              <div className="message-bubble message-bubble--assistant message-bubble--thinking">
                Thinking...
              </div>
            </div>
          )}
        </div>

        <form className="chat__input" onSubmit={handleSend}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask your question..."
            disabled={thinking}
          />
          <button type="submit" disabled={thinking || !input.trim()}>
            Send
          </button>
        </form>
      </main>

      <LeadModal
        open={leadModal.open}
        source={leadModal.source}
        sessionId={sessionId.current}
        onClose={() => setLeadModal({ open: false, source: "form" })}
      />
    </div>
  );
}
