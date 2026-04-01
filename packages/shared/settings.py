"""Environment-backed settings for outreach (pydantic-settings)."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class OutreachSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    openai_api_key: str | None = Field(
        default=None,
        validation_alias="OPENAI_API_KEY",
        description="OpenAI API key",
    )
    agentmail_api_key: str | None = Field(
        default=None,
        validation_alias="AGENTMAIL_API_KEY",
    )
    agentmail_inbox_id: str | None = Field(
        default=None,
        validation_alias="AGENTMAIL_INBOX_ID",
    )

    database_url: str = Field(
        default="sqlite:///./db/sdr.sqlite3",
        validation_alias="DATABASE_URL",
        description="SQLAlchemy URL; default SQLite next to db/schema.sql (see db/).",
    )

    outreach_model: str = Field(default="gpt-4o-mini")
    outreach_temperature: float = Field(default=0.5, ge=0.0, le=2.0)
    outreach_max_tokens: int = Field(default=500, gt=0, le=4096)

    max_emails_per_lead: int = Field(default=5, ge=1)
    max_words_per_email: int = Field(default=200, ge=1)
    tone: str = Field(default="professional")

    # Comma-separated list in env: FORBIDDEN_PHRASES="guaranteed ROI,no risk"
    forbidden_phrases: str = Field(
        default="guaranteed ROI,100% guarantee,no risk",
        description="Comma-separated phrases to block in generated copy",
    )

    opt_out_footer: str = Field(
        default="\n\nIf you'd prefer not to hear from us, reply with STOP and we will remove you.",
    )


def get_settings() -> OutreachSettings:
    return OutreachSettings()


def ensure_data_dir(url: str) -> None:
    """Create parent directory for file-based SQLite URLs."""
    if not url.startswith("sqlite:///"):
        return
    path_part = url.replace("sqlite:///", "", 1)
    if path_part in (":memory:",):
        return
    p = Path(path_part).resolve()
    if p.parent != p:
        p.parent.mkdir(parents=True, exist_ok=True)
