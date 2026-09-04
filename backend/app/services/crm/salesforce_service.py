"""Salesforce CRM integration for UniAssist-AI.

Auth: username + password + security token (no Connected App / OAuth
redirect needed). This is fine for a server-to-server backend service
like this one; it's not appropriate for anything running client-side.
"""

from functools import lru_cache

from simple_salesforce import Salesforce, SalesforceAuthenticationFailed

from app.core.config import settings
from app.core.logger import logger


@lru_cache(maxsize=1)
def _get_client() -> Salesforce:
    """
    Authenticate once per process and reuse the session. Re-authenticating
    on every request (like the pre-fix embedding model behavior) would add
    a real network round-trip to every lead write for no benefit -- the
    session token is valid for hours.
    """

    try:
        return Salesforce(
            username=settings.SF_USERNAME,
            password=settings.SF_PASSWORD,
            security_token=settings.SF_SECURITY_TOKEN,
        )
    except SalesforceAuthenticationFailed as e:
        logger.error(f"[SALESFORCE] Authentication failed: {e}")
        raise


def _escape_soql(value: str) -> str:
    # Minimal SOQL string escaping -- Lead emails shouldn't contain quotes,
    # but don't trust that blindly.
    return value.replace("\\", "\\\\").replace("'", "\\'")


class SalesforceService:
    """Create/update Salesforce Lead records."""

    def __init__(self):
        self.client = _get_client()

    def find_lead_by_email(self, email: str):
        safe_email = _escape_soql(email)

        result = self.client.query(
            f"SELECT Id, Email FROM Lead WHERE Email = '{safe_email}' LIMIT 1"
        )

        if result["totalSize"] > 0:
            return result["records"][0]["Id"]

        return None

    def create_or_update_lead(self, fields: dict) -> dict:
        """
        fields must include: FirstName/LastName, Email, Company.
        Optional: Phone, Description, LeadSource.

        If a Lead with this email already exists, it's updated instead of
        duplicated -- important since the auto-detection path may fire
        more than once for the same visitor before they submit contact
        info, and the explicit form could also be filled after an
        auto-prompt already created a partial lead.
        """

        email = fields.get("Email")

        if not email:
            raise ValueError("Email is required to create or update a Lead")

        existing_id = self.find_lead_by_email(email)

        if existing_id:
            self.client.Lead.update(existing_id, fields)
            logger.info(f"[SALESFORCE] Updated existing Lead {existing_id} ({email})")
            return {"id": existing_id, "created": False}

        result = self.client.Lead.create(fields)
        lead_id = result["id"]
        logger.info(f"[SALESFORCE] Created new Lead {lead_id} ({email})")
        return {"id": lead_id, "created": True}