import { useState } from "react";
import { submitLead, BackendError } from "../api/client.js";

const initialForm = {
  full_name: "",
  email: "",
  phone: "",
  course_interest: "",
  message: "",
};

export default function LeadModal({ open, source, sessionId, onClose }) {
  const [form, setForm] = useState(initialForm);
  const [status, setStatus] = useState("idle"); // idle | submitting | done | error
  const [error, setError] = useState("");

  if (!open) return null;

  function update(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setStatus("submitting");
    setError("");

    try {
      await submitLead({
        ...form,
        phone: form.phone || null,
        course_interest: form.course_interest || null,
        message: form.message || null,
        source,
        session_id: sessionId,
      });
      setStatus("done");
    } catch (err) {
      setError(err instanceof BackendError ? err.message : "Something went wrong. Try again.");
      setStatus("error");
    }
  }

  function handleClose() {
    setForm(initialForm);
    setStatus("idle");
    setError("");
    onClose();
  }

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal__close" onClick={handleClose} aria-label="Close">
          ×
        </button>

        {status === "done" ? (
          <div className="modal__done">
            <h3>Thanks, {form.full_name.split(" ")[0]}.</h3>
            <p>An admissions counselor will reach out to you shortly.</p>
            <button className="sidebar__action sidebar__action--primary" onClick={handleClose}>
              Close
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <h3>Talk to admissions</h3>
            <p className="modal__subtitle">
              Leave your details and a counselor will follow up.
            </p>

            <label>
              Full name
              <input required value={form.full_name} onChange={update("full_name")} />
            </label>

            <label>
              Email
              <input required type="email" value={form.email} onChange={update("email")} />
            </label>

            <label>
              Phone (optional)
              <input value={form.phone} onChange={update("phone")} />
            </label>

            <label>
              Course of interest (optional)
              <input value={form.course_interest} onChange={update("course_interest")} />
            </label>

            <label>
              Message (optional)
              <textarea rows={3} value={form.message} onChange={update("message")} />
            </label>

            {error && <p className="modal__error">{error}</p>}

            <button
              className="sidebar__action sidebar__action--primary"
              type="submit"
              disabled={status === "submitting"}
            >
              {status === "submitting" ? "Sending..." : "Submit"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
