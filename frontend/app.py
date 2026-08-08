"""UniAssist AI frontend entry point."""
import streamlit as st

st.set_page_config(
    page_title="UniAssist AI",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 UniAssist AI")
st.subheader("Your Multilingual AI University Admission Assistant")

st.write("Welcome! Ask anything about admissions, eligibility, fees, scholarships, placements, or courses.")

question = st.text_input("Ask your question...")

if st.button("Send"):
    st.info(f"You asked: {question}")
