"""Pydantic models for outbound email drafts and run results."""

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
    dry_run: bool = Field(
        default=False,
        description="True when copy was validated but not sent (dry run).",
    )
    body_preview: str | None = Field(
        default=None,
        description="Short body snippet for review output.",
    )
