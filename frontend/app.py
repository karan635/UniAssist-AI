"""UniAssist AI frontend entry point."""

import sys
from pathlib import Path

# Make the `components` and `utils` packages importable regardless of
# the directory Streamlit is launched from (streamlit run app.py).
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

from utils.api_client import ask_question, BackendError
from components.chat_ui import render_history, render_message, render_sources


st.set_page_config(
    page_title="UniAssist AI",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 UniAssist AI")
st.subheader("Your AI University Admission Assistant")

st.write(
    "Ask anything about admissions, eligibility, fees, or placements."
)

# -----------------------------------------------------
# Sidebar
# -----------------------------------------------------

with st.sidebar:

    st.header("About")

    st.write(
        "UniAssist AI answers questions about admissions, "
        "eligibility, fees, and placements using the university's "
        "official documents."
    )

    if st.button("🗑️ Clear conversation"):
        st.session_state.history = []
        st.rerun()

# -----------------------------------------------------
# Conversation history
#
# Kept in Streamlit's session state, so it survives reruns within the
# same browser session but resets on a full page refresh -- this
# matches the backend's own design, since ChatService doesn't
# remember prior turns either (each /chat call is independent).
# -----------------------------------------------------

if "history" not in st.session_state:
    st.session_state.history = []

render_history(st.session_state.history)

question = st.chat_input("Ask your question...")

if question:

    st.session_state.history.append(
        {"role": "user", "content": question}
    )

    render_message("user", question)

    with st.chat_message("assistant", avatar="🎓"):

        with st.spinner("Thinking..."):

            try:

                data = ask_question(question)

                answer = data.get("answer", "")

                st.markdown(answer)

                render_sources(
                    data.get("documents_used", [])
                )

            except BackendError as e:

                answer = f"⚠️ {e}"

                st.error(str(e))

    st.session_state.history.append(
        {"role": "assistant", "content": answer}
    )