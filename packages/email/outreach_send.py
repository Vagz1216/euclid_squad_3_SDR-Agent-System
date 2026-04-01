"""Outbound send: calls tools.send_plain_email (shared AgentMail path)."""

from __future__ import annotations

from packages.schema.outreach import OutreachEmailDraft, OutreachSendResult
from tools.send_email import send_plain_email


def send_outreach_email(
    *,
    to_email: str,
    to_name: str | None,
    draft: OutreachEmailDraft,
) -> OutreachSendResult:
    r = send_plain_email(
        to_email,
        to_name or "",
        draft.subject,
        draft.body,
    )
    return OutreachSendResult(
        ok=r.ok,
        message_id=r.message_id,
        thread_id=r.thread_id,
        error=r.error,
    )
