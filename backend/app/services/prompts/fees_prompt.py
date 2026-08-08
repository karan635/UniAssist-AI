from app.services.prompts.base_prompt import SYSTEM_PROMPT


def build(question, context):

    return f"""
{SYSTEM_PROMPT}

The user is asking about FEES.

Instructions:

Return:

# Program Fees

Semester-wise fee table

Admission fee

Caution money

Hostel fee (if available)

Approximate total expenditure

Never summarize.

Always preserve exact numbers.

If the context does not contain fee information for the requested program/campus,
say so explicitly instead of estimating or guessing numbers.

Context:

{context}

Question:

{question}
"""