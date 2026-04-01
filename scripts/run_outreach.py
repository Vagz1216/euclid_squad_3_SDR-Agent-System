#!/usr/bin/env python3
"""CLI: run one outreach batch (generate + guardrails + AgentMail send + DB update)."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Allow `python scripts/run_outreach.py` from repo root without editable install
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from packages.agents.outreach_pipeline import CampaignContext, run_outreach_batch

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")


async def _run(limit: int, *, dry_run: bool, full_body: bool) -> int:
    results = await run_outreach_batch(
        limit=limit,
        campaign=CampaignContext(),
        dry_run=dry_run,
        include_body_preview=dry_run,
        body_preview_max_len=None if full_body else 400,
    )
    print(json.dumps([r.model_dump() for r in results], indent=2))

    def _ok(rec) -> bool:
        if rec.error:
            return False
        if dry_run:
            return rec.dry_run
        return rec.sent

    return 0 if all(_ok(r) for r in results) or not results else 1


def main() -> None:
    p = argparse.ArgumentParser(
        description="Run one outbound batch. Use --dry-run to review drafts without sending.",
    )
    p.add_argument("--limit", type=int, default=5, help="Max leads to process this run")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate + guardrails only; do not send email or update lead touches",
    )
    p.add_argument(
        "--full-body-preview",
        action="store_true",
        help="Include full body in body_preview (default is truncated); use for local review only",
    )
    args = p.parse_args()
    raise SystemExit(
        asyncio.run(
            _run(
                args.limit,
                dry_run=args.dry_run,
                full_body=args.full_body_preview,
            )
        )
    )


if __name__ == "__main__":
    main()
