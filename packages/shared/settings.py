"""
Outreach and DB code import settings from here.

The real definition is config.settings.AppConfig. This module re-exports it so
packages.* imports stay aligned with the rest of the repo (config, email_monitor, tools).
"""

from config import settings
from config.settings import AppConfig

# Backward-compatible alias (tests, type hints)
OutreachSettings = AppConfig


def get_settings() -> AppConfig:
    return settings


def ensure_data_dir(url: str) -> None:
    """Create parent directory for file-based SQLite URLs."""
    from pathlib import Path

    if not url.startswith("sqlite:///"):
        return
    path_part = url.replace("sqlite:///", "", 1)
    if path_part in (":memory:",):
        return
    p = Path(path_part).resolve()
    if p.parent != p:
        p.parent.mkdir(parents=True, exist_ok=True)
