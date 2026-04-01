"""Send outbound email via AgentMail (tool action; spec §3.2)."""

from __future__ import annotations

import time

from email.utils import formataddr

from agentmail import AgentMail
from agentmail.core.api_error import ApiError

from packages.schema.outreach import OutreachEmailDraft, OutreachSendResult
from packages.shared.settings import get_settings


def send_outreach_email(
    *,
    to_email: str,
    to_name: str | None,
    draft: OutreachEmailDraft,
) -> OutreachSendResult:
    settings = get_settings()
    if not settings.agentmail_api_key or not settings.agentmail_inbox_id:
        return OutreachSendResult(
            ok=False,
            error="AGENTMAIL_API_KEY and AGENTMAIL_INBOX_ID must be set in the environment.",
        )

    client = AgentMail(api_key=settings.agentmail_api_key)
    name = (to_name or "").strip()
    to = formataddr((name, to_email)) if name else to_email.strip()

    for attempt in range(5):
        try:
            response = client.inboxes.messages.send(
                settings.agentmail_inbox_id,
                to=to,
                subject=draft.subject.strip(),
                text=draft.body.strip(),
            )
            return OutreachSendResult(
                ok=True,
                message_id=str(response.message_id),
                thread_id=str(response.thread_id) if response.thread_id else None,
            )
        except ApiError as e:
            if e.status_code == 429 and attempt < 4:
                _sleep_backoff(attempt, e)
                continue
            return OutreachSendResult(ok=False, error=_format_api_error(e))

    return OutreachSendResult(ok=False, error="Failed after retries")


def _format_api_error(exc: ApiError) -> str:
    body = exc.body
    if isinstance(body, dict) and body.get("message"):
        return str(body["message"])
    if hasattr(body, "message") and getattr(body, "message"):
        return str(body.message)
    return str(exc)


def _sleep_backoff(attempt: int, exc: ApiError) -> None:
    if exc.headers:
        ra = exc.headers.get("retry-after") or exc.headers.get("Retry-After")
        if ra:
            try:
                wait = float(ra)
                if wait > 0:
                    time.sleep(wait)
                    return
            except (TypeError, ValueError):
                pass
    time.sleep(min(2.0**attempt, 60.0))
