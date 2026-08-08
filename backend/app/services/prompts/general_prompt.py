from app.services.prompts.base_prompt import SYSTEM_PROMPT


def build(question, context):

    return f"""
{SYSTEM_PROMPT}

Context:

{context}

Question:

{question}
"""