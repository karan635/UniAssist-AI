from app.services.prompts.base_prompt import SYSTEM_PROMPT


def build(question, context):

    return f"""
{SYSTEM_PROMPT}

The user is asking about ELIGIBILITY.

Return eligibility requirements as bullet points.

Context:

{context}

Question:

{question}
"""