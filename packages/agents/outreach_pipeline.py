"""
Outreach batch: fetch eligible leads, generate copy, guardrails, send, then update the DB.

After each successful send: lead row, campaign_leads, email_messages, and events audit row.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from packages.agents.guardrails import apply_opt_out_footer, validate_outreach_draft
from packages.agents.outreach_generator import generate_outreach_email
from packages.db.outreach_queries import fetch_eligible_targets, persist_outbound_success
from packages.db.session import get_session_factory
from packages.email.outreach_send import send_outreach_email
from packages.schema.outreach import OutreachRunRecord
from packages.shared.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class CampaignContext:
    """Campaign copy for prompts. Usually loaded from campaigns rows; optional override for tests."""

    name: str = "Default campaign"
    value_proposition: str = "We help teams automate outbound with AI-assisted workflows."
    cta: str = "Are you open to a 15-minute call next week?"


def _preview_body(body: str, max_len: int | None = 400) -> str:
    body = body.strip()
    if max_len is None or len(body) <= max_len:
        return body
    return body[: max_len - 3] + "..."


async def run_outreach_batch(
    *,
    limit: int = 10,
    campaign: CampaignContext | None = None,
    dry_run: bool = False,
    include_body_preview: bool = True,
    body_preview_max_len: int | None = 400,
) -> list[OutreachRunRecord]:
    """
    Process up to limit eligible leads.

    Normal mode: generate, guardrails, AgentMail send, then commit per send.
    dry_run: generate and guardrails only; no send and no DB updates for staging.

    Sets OPENAI_API_KEY on the process for the OpenAI Agents SDK if missing.
    """
    settings = get_settings()
    if settings.openai_api_key and not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key

    campaign_override = campaign
    factory = get_session_factory()
    session = factory()
    results: list[OutreachRunRecord] = []

    try:
        targets = fetch_eligible_targets(session, limit=limit)
        if not targets:
            logger.info("No eligible leads to contact (need ACTIVE campaign + campaign_leads row).")
            return results

        for target in targets:
            lead = target.lead
            camp = target.campaign
            ctx = campaign_override or CampaignContext(
                name=camp.name,
                value_proposition=camp.value_proposition or "",
                cta=camp.cta or "",
            )
            rec = OutreachRunRecord(
                lead_id=lead.id,
                email=lead.email,
                campaign_id=camp.id,
                sent=False,
            )
            try:
                draft = await generate_outreach_email(
                    lead_name=lead.name,
                    lead_email=lead.email,
                    campaign_name=ctx.name,
                    value_proposition=ctx.value_proposition,
                    cta=ctx.cta,
                )
                draft = apply_opt_out_footer(draft)
                ok, err = validate_outreach_draft(draft)
                if not ok:
                    rec.error = err
                    results.append(rec)
                    continue

                if dry_run:
                    rec.dry_run = True
                    rec.subject = draft.subject
                    if include_body_preview:
                        rec.body_preview = _preview_body(draft.body, body_preview_max_len)
                    results.append(rec)
                    logger.info(
                        "Dry-run OK lead_id=%s email=%s subject=%r",
                        lead.id,
                        lead.email,
                        draft.subject[:80],
                    )
                    continue

                send_res = send_outreach_email(
                    to_email=lead.email,
                    to_name=lead.name,
                    draft=draft,
                )
                if not send_res.ok:
                    rec.error = send_res.error
                    results.append(rec)
                    continue

                persist_outbound_success(
                    session,
                    lead=lead,
                    campaign_id=camp.id,
                    subject=draft.subject,
                    body=draft.body,
                    provider_message_id=send_res.message_id,
                    provider_thread_id=send_res.thread_id,
                )
                session.commit()
                rec.sent = True
                rec.subject = draft.subject
                rec.message_id = send_res.message_id
                rec.thread_id = send_res.thread_id
                results.append(rec)
                logger.info("Sent outreach to lead_id=%s email=%s", lead.id, lead.email)

            except Exception as e:
                logger.exception("Outreach failed for lead_id=%s", lead.id)
                rec.error = str(e)
                session.rollback()
                results.append(rec)

        return results
    finally:
        session.close()
