"""Pydantic contracts for outreach email generation (spec §4)."""

from pydantic import BaseModel, Field


class OutreachEmailDraft(BaseModel):
    """Email generation contract: subject + body only."""

    subject: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)


class OutreachSendResult(BaseModel):
    ok: bool
    message_id: str | None = None
    thread_id: str | None = None
    error: str | None = None


class OutreachRunRecord(BaseModel):
    """One lead processed in a batch (for logging / API responses)."""

    lead_id: int
    email: str
    campaign_id: int | None = None
    sent: bool
    error: str | None = None
    subject: str | None = None
    message_id: str | None = None
    thread_id: str | None = None
    #: True when email was generated + validated but not sent (review / staging).
    dry_run: bool = False
    #: Truncated body for review; omit in production logs if policy requires.
    body_preview: str | None = None
