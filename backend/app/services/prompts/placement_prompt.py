from app.services.prompts.base_prompt import SYSTEM_PROMPT


def build(question, context):

    return f"""
{SYSTEM_PROMPT}

The user is asking about PLACEMENTS.

Return:

Highest package

Average package

Minimum package

Recruiters

Branch-wise offers

Total offers

Eligible students

Use tables whenever possible.

Context:

{context}

Question:

{question}
"""