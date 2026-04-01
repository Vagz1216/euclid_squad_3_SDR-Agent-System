"""Use the OpenAI Agents SDK to produce subject and body JSON for outbound mail."""

from __future__ import annotations

import json
import logging
import re

from agents import Agent, ModelSettings, Runner

from packages.schema.outreach import OutreachEmailDraft
from packages.shared.settings import get_settings

logger = logging.getLogger(__name__)


def _parse_json_object(raw: str) -> dict:
    text = raw.strip()
    fence = re.match(r"^```(?:json)?\s*([\s\S]*?)```\s*$", text)
    if fence:
        text = fence.group(1).strip()
    return json.loads(text)


async def generate_outreach_email(
    *,
    lead_name: str | None,
    lead_email: str,
    campaign_name: str,
    value_proposition: str,
    cta: str,
) -> OutreachEmailDraft:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    tone = settings.tone
    agent = Agent(
        name="OutreachEmailWriter",
        instructions=f"""
You write concise outbound sales emails.

Rules:
- Tone: {tone}
- Include a clear call-to-action aligned with the CTA provided
- No false or absolute claims (no guaranteed ROI, no "100% guarantee")
- Keep the body under {settings.max_words_per_email} words
- Output ONLY valid JSON with keys "subject" and "body" (both strings)
- Do not include markdown fences around the JSON
""",
        model_settings=ModelSettings(
            model=settings.outreach_model,
            temperature=settings.outreach_temperature,
            max_tokens=settings.outreach_max_tokens,
        ),
    )

    prompt = f"""
Campaign: {campaign_name}
Value proposition: {value_proposition}
CTA to weave in: {cta}

Lead name: {lead_name or "there"}
Lead email (do not paste into body): {lead_email}

Return JSON exactly:
{{"subject": "...", "body": "..."}}
"""
    result = await Runner.run(agent, prompt)
    data = _parse_json_object(result.final_output)
    return OutreachEmailDraft.model_validate(data)
