"""Database package: schema, session, outreach queries."""

from packages.db.models import (
    AuditEvent,
    Base,
    Campaign,
    CampaignLead,
    EmailMessage,
    Lead,
    Meeting,
    Staff,
)
from packages.db.outreach_queries import (
    OutreachTarget,
    fetch_eligible_targets,
    persist_outbound_success,
)
from packages.db.session import get_engine, get_session_factory, session_scope

__all__ = [
    "AuditEvent",
    "Base",
    "Campaign",
    "CampaignLead",
    "EmailMessage",
    "Lead",
    "Meeting",
    "Staff",
    "OutreachTarget",
    "fetch_eligible_targets",
    "persist_outbound_success",
    "get_engine",
    "get_session_factory",
    "session_scope",
]
