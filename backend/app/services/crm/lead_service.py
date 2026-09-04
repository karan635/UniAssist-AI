"""Orchestrates lead capture -- called by both the explicit contact form
and the auto-detected interest prompt. Both paths end up here so there's
one place that decides what a "Lead" looks like in Salesforce.
"""

from app.core.logger import logger
from app.services.crm.salesforce_service import SalesforceService
from app.services.crm.lead_intent_tracker import lead_intent_tracker


class LeadService:

    def __init__(self):
        self.salesforce = SalesforceService()

    def _split_name(self, full_name: str) -> tuple[str, str]:
        parts = full_name.strip().split(maxsplit=1)

        if len(parts) == 2:
            return parts[0], parts[1]

        # Salesforce Lead requires LastName; if only one word was given,
        # use it as the last name rather than failing the create.
        return "", parts[0] if parts else "Unknown"

    def capture_lead(
        self,
        full_name: str,
        email: str,
        phone: str | None = None,
        course_interest: str | None = None,
        message: str | None = None,
        source: str = "form",          # "form" | "auto"
        session_id: str | None = None,
    ) -> dict:

        first_name, last_name = self._split_name(full_name)

        fields = {
            "FirstName": first_name,
            "LastName": last_name or "Unknown",
            "Email": email,
            "Company": course_interest or "Prospective Student",
            "LeadSource": "UniAssist Chatbot",
        }

        if phone:
            fields["Phone"] = phone

        description_parts = []
        if source == "auto":
            description_parts.append("Auto-detected from chatbot conversation.")
        if course_interest:
            description_parts.append(f"Course interest: {course_interest}")
        if message:
            description_parts.append(f"Message: {message}")

        if description_parts:
            fields["Description"] = " | ".join(description_parts)

        # Optional custom field -- only set this if you've created
        # Course_Interest__c on the Lead object in Salesforce Setup.
        # Left commented out so this works against a stock org; uncomment
        # once the field exists.
        # if course_interest:
        #     fields["Course_Interest__c"] = course_interest

        result = self.salesforce.create_or_update_lead(fields)

        if session_id:
            lead_intent_tracker.mark_lead_created(session_id)

        logger.info(
            f"[LEAD] {'Created' if result['created'] else 'Updated'} "
            f"Lead {result['id']} via {source} (session={session_id})"
        )

        return result