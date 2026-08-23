"""Reusable Streamlit components for the chat UI."""

import streamlit as st


def render_message(role: str, content: str):
    """Render a single chat bubble (one message) using Streamlit's
    built-in chat message component."""

    avatar = "🎓" if role == "assistant" else "🧑"

    with st.chat_message(role, avatar=avatar):
        st.markdown(content)


def render_history(history: list):
    """Render the full conversation history, oldest message first."""

    for message in history:
        render_message(message["role"], message["content"])


def render_sources(documents: list):
    """
    Show which source documents/pages backed an answer, tucked into a
    collapsed expander so it doesn't clutter the main chat view unless
    the user actually wants to check it.
    """

    if not documents:
        return

    with st.expander(f"📄 Sources ({len(documents)})"):

        for doc in documents:

            metadata = (
                doc.get("metadata", {})
                if isinstance(doc, dict)
                else {}
            )

            filename = metadata.get("filename", "Unknown document")
            page = metadata.get("page_label")

            label = f"**{filename}**"

            if page:
                label += f" — page {page}"

            st.markdown(f"- {label}")