"""Unit tests for outreach guardrails (no network, no API keys)."""

from packages.agents.guardrails import apply_opt_out_footer, validate_outreach_draft
from packages.schema.outreach import OutreachEmailDraft
from packages.shared.settings import OutreachSettings


def test_validate_passes_clean_draft():
    draft = OutreachEmailDraft(
        subject="Quick question on your roadmap",
        body="Hi - we help teams streamline outreach. Open to a short call?",
    )
    settings = OutreachSettings(
        max_words_per_email=200,
        forbidden_phrases="guaranteed ROI,100% guarantee,no risk",
        opt_out_footer="\n\nReply STOP to opt out.",
    )
    ok, err = validate_outreach_draft(draft, settings=settings)
    assert ok and err is None


def test_forbidden_phrase_fails():
    draft = OutreachEmailDraft(
        subject="Hello",
        body="We offer guaranteed ROI in 30 days.",
    )
    settings = OutreachSettings(
        max_words_per_email=200,
        forbidden_phrases="guaranteed ROI",
        opt_out_footer="",
    )
    ok, err = validate_outreach_draft(draft, settings=settings)
    assert not ok
    assert err and "Forbidden" in err


def test_max_words_fails():
    body = "word " * 250
    draft = OutreachEmailDraft(subject="Hi", body=body.strip())
    settings = OutreachSettings(
        max_words_per_email=50,
        forbidden_phrases="",
        opt_out_footer="",
    )
    ok, err = validate_outreach_draft(draft, settings=settings)
    assert not ok
    assert err and "max_words" in err


def test_opt_out_footer_appended():
    draft = OutreachEmailDraft(subject="Hi", body="Short note.")
    settings = OutreachSettings(opt_out_footer="\n\nReply STOP to opt out.")
    out = apply_opt_out_footer(draft, settings=settings)
    assert "STOP" in out.body
