"""Programmatic guardrails after the model drafts outbound copy."""

from __future__ import annotations

import re

from config.settings import AppConfig
from packages.schema.outreach import OutreachEmailDraft
from packages.shared.settings import get_settings


def _word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def validate_outreach_draft(
    draft: OutreachEmailDraft,
    *,
    settings: AppConfig | None = None,
) -> tuple[bool, str | None]:
    """
    Returns (ok, error_message).
    Enforces length, forbidden phrases, and basic sanity checks.
    """
    settings = settings or get_settings()
    combined = f"{draft.subject}\n{draft.body}".lower()

    for phrase in _forbidden_list(settings):
        p = phrase.strip().lower()
        if p and p in combined:
            return False, f"Forbidden phrase not allowed: {phrase.strip()}"

    words = _word_count(draft.body)
    if words > settings.max_words_per_email:
        return False, f"Body exceeds max_words ({words} > {settings.max_words_per_email})"

    if re.search(r"\b100%\s*(guarantee|sure|certain)\b", combined):
        return False, "Avoid absolute guarantee claims."

    return True, None


def apply_opt_out_footer(draft: OutreachEmailDraft, settings: AppConfig | None = None) -> OutreachEmailDraft:
    """Append or keep an opt-out line in the body when missing."""
    settings = settings or get_settings()
    footer = settings.opt_out_footer.strip()
    if not footer:
        return draft
    body = draft.body.rstrip()
    if "stop" in body.lower() and "opt" in body.lower():
        return draft
    return OutreachEmailDraft(subject=draft.subject, body=f"{body}\n{footer}")


def _forbidden_list(settings: AppConfig) -> list[str]:
    return [x.strip() for x in settings.forbidden_phrases.split(",") if x.strip()]
