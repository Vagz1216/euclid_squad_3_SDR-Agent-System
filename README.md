# Agent-Driven Outreach Platform

Automated email outreach with AI response monitoring and lead qualification.

## Project Structure

```
project-root/
│
├── apps/
│   ├── api/                  # Main backend (all core logic lives here)
│   ├── worker/               # Background jobs (email sending, monitoring)
│   └── web/                  # Internal chat interface (Phase 2)
│
├── packages/
│   ├── agents/               # All agent workflows
│   ├── db/                   # DB schema + queries
│   ├── email/                # Email handling (server + utilities)
│   ├── integrations/         # External services (Google Meet, etc.)
│   ├── schema/               # Pydantic declarations
│   └── shared/               # Types, constants, helpers
│
├── scripts/                  # Dev scripts (seeding, cron triggers, etc.)
├── .env
├── pyproject.toml            # uv configuration and dependencies
└── README.md
```

## Quick Start

1. Copy `.env.example` to `.env` and configure your settings (`OPENAI_API_KEY`, `AGENTMAIL_*`).
2. Install dependencies: `uv sync`
3. First DB connection applies `db/schema.sql` (and `db/seed.sql` if campaigns are empty). Optional extra leads: `uv run python scripts/seed_contacts.py`
4. Run one outreach batch (generate → guardrails → AgentMail → DB touch update): `uv run python scripts/run_outreach.py --limit 5`
5. Optional API trigger: from repo root, `uv run uvicorn apps.api.main:app --reload` then `POST /outreach/run?limit=5`
6. Worker app (`apps/worker`) remains for background jobs as the platform grows.

### Outbound slice (v2 spec §4) — review checklist

Use this to confirm the **outbound** track is ready for PR review and demo.

| Spec item | Status | Where |
|-----------|--------|--------|
| Fetch eligible leads (not opted out, below cap, **ACTIVE campaign + `campaign_leads`**) | Done | `packages/db/outreach_queries.fetch_eligible_targets` (aligned with upstream `api` `lead_service`) |
| Per-lead: load context → generate `{subject, body}` | Done (copy from `campaigns` row, optional `CampaignContext` override) | `outreach_generator.py` + `outreach_pipeline.py` |
| Guardrails (tone prompt, length, forbidden phrases, opt-out footer) | Done | `packages/agents/guardrails.py` |
| Send via provider (AgentMail) | Done | `packages/email/outreach_send.py` |
| Update `touch_count` / `last_contacted_at` / status | Done | `persist_outbound_success` |
| Persist outbound rows in `email_messages` | Done | same |
| Increment `campaign_leads.emails_sent` | Done | same |
| Audit `events` row | Done | `AuditEvent` (`outreach_sent`) |
| Schema source of truth | `db/schema.sql` (+ SQLAlchemy models in `packages/db/models.py`) | Matches upstream `origin/api` draft |

**Safe review (no real sends):**

```bash
uv run python scripts/seed_contacts.py
uv run python scripts/run_outreach.py --limit 1 --dry-run
```

Uses OpenAI for generation; does **not** call AgentMail or mutate the database. Add `--full-body-preview` locally if you want the entire body in JSON (avoid sharing in public channels).

**Note:** Eligible leads must appear in `campaign_leads` for an **ACTIVE** campaign (see `db/seed.sql`). Seed adds alice/bob on campaign 1; `scripts/seed_contacts.py` adds more linked leads.

**Full path (sends real mail):**

```bash
uv run python scripts/run_outreach.py --limit 1
```

Requires valid `OPENAI_API_KEY` and `AGENTMAIL_*`; use test inboxes and consenting recipients only.

**Automated checks (guardrails only):**

```bash
uv sync --extra dev
uv run pytest tests/test_guardrails.py -q
```

## Core Features

- **Email Outreach Agent**: AI-powered personalized email campaigns
- **Response Monitoring**: Automatic response parsing and sentiment analysis
- **Lead Qualification**: Scoring system with Slack/Teams notifications
- **Google Meet Integration**: Automated scheduling for qualified leads

## Architecture

- **API App**: REST endpoints for managing contacts, campaigns, and analytics
- **Worker App**: Background processing for email sending and monitoring
- **Packages**: Shared libraries for database, email, and integrations
- **Schema**: Type-safe data validation with Pydantic