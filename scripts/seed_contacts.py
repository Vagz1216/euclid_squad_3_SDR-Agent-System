#!/usr/bin/env python3
"""
Add demo leads linked to campaign 1 after db/schema.sql and db/seed.sql bootstrap.

The first engine connect applies schema and seeds sample campaigns/leads if empty.
This script adds extra rows for local testing without duplicating emails.
"""

from __future__ import annotations

from sqlalchemy import select

from packages.db.models import Campaign, CampaignLead, Lead
from packages.db.session import get_engine, get_session_factory


def main() -> None:
    get_engine()
    factory = get_session_factory()
    session = factory()
    try:
        campaign = session.scalar(select(Campaign).where(Campaign.id == 1).limit(1))
        if campaign is None:
            print("No campaign with id=1. Open the app once to bootstrap db/, or run from repo root.")
            return

        samples = [
            ("alex@example.com", "Alex Demo"),
            ("jamie@example.com", "Jamie Demo"),
            ("sam@example.com", "Sam Demo"),
        ]
        for email, name in samples:
            existing = session.scalar(select(Lead).where(Lead.email == email).limit(1))
            if existing:
                print(f"skip existing lead {email}")
                continue
            lead = Lead(
                email=email,
                name=name,
                status="NEW",
                email_opt_out=False,
                touch_count=0,
            )
            session.add(lead)
            session.flush()
            session.add(
                CampaignLead(
                    campaign_id=campaign.id,
                    lead_id=lead.id,
                    emails_sent=0,
                    responded=False,
                    meeting_booked=False,
                )
            )
            print(f"added {email} to campaign {campaign.id}")
        session.commit()
        print("Done. Eligible outreach needs ACTIVE campaign + join row (see db/seed.sql defaults).")
    finally:
        session.close()


if __name__ == "__main__":
    main()
