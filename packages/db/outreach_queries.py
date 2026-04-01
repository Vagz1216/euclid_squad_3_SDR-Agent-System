"""Read and update leads and campaign state for outbound batches."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.db.models import Campaign, CampaignLead, EmailMessage, Lead, AuditEvent
from packages.shared.settings import get_settings


@dataclass(frozen=True)
class OutreachTarget:
    """One lead to contact within a specific active campaign."""

    lead: Lead
    campaign: Campaign


def fetch_eligible_targets(session: Session, *, limit: int = 20) -> list[OutreachTarget]:
    """
    Eligible targets: not opted out, active campaign, emails_sent below cap
    (max_emails_per_lead from settings), lead status allowed for outreach.
    """
    settings = get_settings()
    cap = settings.max_emails_per_lead
    # Over-fetch in case the same lead appears in multiple rows (multiple campaigns).
    stmt = (
        select(Lead, Campaign)
        .join(CampaignLead, CampaignLead.lead_id == Lead.id)
        .join(Campaign, Campaign.id == CampaignLead.campaign_id)
        .where(Lead.email_opt_out.is_(False))
        .where(Campaign.status == "ACTIVE")
        .where(CampaignLead.emails_sent < cap)
        .where(Lead.status.not_in(("OPTED_OUT", "COLD")))
        .order_by(Lead.id.asc(), Campaign.id.asc())
        .limit(max(limit * 5, limit))
    )
    rows = session.execute(stmt).all()
    seen: set[int] = set()
    out: list[OutreachTarget] = []
    for lead, campaign in rows:
        if lead.id in seen:
            continue
        seen.add(lead.id)
        out.append(OutreachTarget(lead=lead, campaign=campaign))
        if len(out) >= limit:
            break
    return out


def persist_outbound_success(
    session: Session,
    *,
    lead: Lead,
    campaign_id: int,
    subject: str,
    body: str,
    provider_message_id: str | None,
    provider_thread_id: str | None,
) -> None:
    """
    After a successful provider send: update lead timestamps and counts,
    increment campaign_leads.emails_sent (create join row if needed),
    insert outbound email_messages, append events audit row.
    """
    now = datetime.now(timezone.utc)
    lead.touch_count = int(lead.touch_count or 0) + 1
    lead.last_contacted_at = now
    if lead.status == "NEW":
        lead.status = "CONTACTED"

    cl = session.get(CampaignLead, (campaign_id, lead.id))
    if cl is None:
        cl = CampaignLead(
            campaign_id=campaign_id,
            lead_id=lead.id,
            emails_sent=0,
            responded=False,
            meeting_booked=False,
        )
        session.add(cl)
    cl.emails_sent = int(cl.emails_sent or 0) + 1

    session.add(
        EmailMessage(
            lead_id=lead.id,
            campaign_id=campaign_id,
            direction="outbound",
            subject=subject,
            body=body,
            status="sent",
            intent=None,
            processed=True,
        )
    )

    payload = {
        "lead_id": lead.id,
        "campaign_id": campaign_id,
        "message_id": provider_message_id,
        "thread_id": provider_thread_id,
    }
    session.add(
        AuditEvent(
            type="outreach_sent",
            payload=json.dumps({k: v for k, v in payload.items() if v is not None}),
            metadata_=None,
        )
    )
