"""Tracks per-session interest signals to decide when to auto-prompt for
a Lead capture, without needing external storage.

In-memory and per-process -- fine for a single backend instance. If you
scale to multiple workers/instances behind a load balancer, sessions will
land on different processes and each will track independently (worst
case: the prompt fires more than once for the same visitor). Swap the
dict below for Redis if that becomes a problem -- the interface
(record_query / should_prompt / mark_prompted / mark_lead_created)
wouldn't need to change.
"""

import time

from app.core.config import settings

# Topics that indicate genuine admissions interest, not just browsing.
_INTEREST_TOPICS = {"Admission", "Fees", "Eligibility"}

# Session state expires after this many seconds of inactivity, so the
# dict doesn't grow unbounded over the life of the process.
_SESSION_TTL_SECONDS = 60 * 60


class LeadIntentTracker:

    def __init__(self):
        self._sessions: dict[str, dict] = {}

    def _get_session(self, session_id: str) -> dict:
        self._evict_stale()

        session = self._sessions.get(session_id)

        if session is None:
            session = {
                "score": 0,
                "prompted": False,
                "lead_created": False,
                "last_seen": time.time(),
            }
            self._sessions[session_id] = session

        return session

    def _evict_stale(self):
        now = time.time()
        stale = [
            sid for sid, s in self._sessions.items()
            if now - s["last_seen"] > _SESSION_TTL_SECONDS
        ]
        for sid in stale:
            del self._sessions[sid]

    def record_query(self, session_id: str, topic: str | None) -> bool:
        """
        Call this once per chat turn with the normalized topic from
        QueryAnalyzer/MetadataFilter. Returns True exactly once -- the
        turn where the session crosses the interest threshold and hasn't
        already been prompted.
        """

        session = self._get_session(session_id)
        session["last_seen"] = time.time()

        if session["prompted"] or session["lead_created"]:
            return False

        if topic in _INTEREST_TOPICS:
            session["score"] += 1

        if session["score"] >= settings.LEAD_INTEREST_THRESHOLD:
            session["prompted"] = True
            return True

        return False

    def mark_lead_created(self, session_id: str):
        session = self._get_session(session_id)
        session["lead_created"] = True


# Shared instance -- session state needs to persist across requests
# within the same process, so this isn't re-instantiated per request the
# way stateless services are.
lead_intent_tracker = LeadIntentTracker()