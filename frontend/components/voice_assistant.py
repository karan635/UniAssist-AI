"""Voice assistant component -- mic input and transcription, wired
into the same session history and rendering functions the text chat
already uses. Voice input only; the answer is shown as text."""

import streamlit as st
from streamlit_mic_recorder import mic_recorder

from utils.api_client import ask_question, transcribe_audio, BackendError
from components.chat_ui import render_message, render_sources


def render_voice_assistant():

    st.subheader("🎤 Voice Assistant")

    # Same history list the text chat uses in app.py -- so a voice
    # question and its answer show up in the same conversation thread,
    # not a separate one.
    if "history" not in st.session_state:
        st.session_state.history = []

    audio = mic_recorder(
        start_prompt="Start recording",
        stop_prompt="Stop recording",
        just_once=True,
        key="voice_recorder",
    )

    if not audio:
        return

    try:

        # -----------------------------------------------------
        # 1. Audio -> text
        # -----------------------------------------------------

        with st.spinner("Listening..."):
            transcribed = transcribe_audio(audio["bytes"])

        question = transcribed["text"]

        if not question:
            st.warning("Didn't catch that, please try again.")
            return

        st.session_state.history.append({"role": "user", "content": question})
        render_message("user", question)

        # -----------------------------------------------------
        # 2. Text -> chat answer (same /chat flow as typed questions)
        # -----------------------------------------------------

        with st.chat_message("assistant", avatar="🎓"):

            with st.spinner("Thinking..."):
                data = ask_question(question)

            answer = data.get("answer", "")

            st.markdown(answer)
            render_sources(data.get("documents_used", []))

        st.session_state.history.append({"role": "assistant", "content": answer})

    except BackendError as e:
        st.error(str(e))