"""
Minimal FastAPI app to trigger an outreach batch.

Run from repo root: uv run uvicorn apps.api.main:app --reload
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi import FastAPI

from packages.agents.outreach_pipeline import CampaignContext, run_outreach_batch

app = FastAPI(title="SDR Outreach API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/outreach/run")
async def outreach_run(limit: int = 5, dry_run: bool = False) -> dict:
    """Start one outreach batch. Set dry_run=true to validate drafts without sending or DB updates."""
    rows = await run_outreach_batch(
        limit=limit,
        campaign=CampaignContext(),
        dry_run=dry_run,
        include_body_preview=dry_run,
        body_preview_max_len=400,
    )
    return {"results": [r.model_dump() for r in rows], "dry_run": dry_run}
