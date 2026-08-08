from app.services.prompts import (
    fees_prompt,
    placement_prompt,
    eligibility_prompt,
    admission_prompt,
    general_prompt,
)


class PromptRouter:

    def build(self, question, context, analysis):

        topic = analysis.get("topic")

        if topic == "Fees":
            return fees_prompt.build(question, context)

        elif topic == "Placement":
            return placement_prompt.build(question, context)

        elif topic == "Eligibility":
            return eligibility_prompt.build(question, context)

        elif topic == "Admission":
            return admission_prompt.build(question, context)

        return general_prompt.build(question, context)