from app.services.prompts.base_prompt import SYSTEM_PROMPT


def build(question, context):

    return f"""
{SYSTEM_PROMPT}

The user is asking about ADMISSION.

Return:

Eligibility

Admission process

Required documents

Important dates (if available)

Application mode

Context:

{context}

Question:

{question}
"""