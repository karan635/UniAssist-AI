from app.services.prompts.base_prompt import SYSTEM_PROMPT


def build(question, context):
    return f"""
{SYSTEM_PROMPT}

## Role
You are answering a question about **ELIGIBILITY** requirements.

## Instructions
- Respond in a warm, clear, and helpful tone.
- Present eligibility requirements as a well-organized bulleted list.
- Use simple, jargon-free language that anyone can understand.
- If there are multiple categories of requirements, group them under clear subheadings.
- If a requirement has conditions or exceptions, note them clearly.
- If the context does not contain enough information to fully answer, say so honestly — do not guess.

## Context
{context}

## User Question
{question}
"""