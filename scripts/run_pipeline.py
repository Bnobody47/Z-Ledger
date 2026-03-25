"""
Run one application through the credit analysis agent.
Usage: python scripts/run_pipeline.py --application loan-app-1 [--phase credit]
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


async def main():
    parser = argparse.ArgumentParser(description="Z Ledger pipeline runner")
    parser.add_argument("--application", required=True, help="Application ID (e.g. app-1)")
    parser.add_argument("--phase", default="credit", choices=["credit"], help="Phase to run")
    parser.add_argument("--db-url", default=os.environ.get("DATABASE_URL"))
    args = parser.parse_args()

    if not args.db_url:
        print("Error: DATABASE_URL not set. Set it or use --db-url")
        sys.exit(1)

    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if not openrouter_key and (not anthropic_key or anthropic_key == "sk-ant-YOUR_KEY_HERE"):
        print("Error: set either OPENROUTER_API_KEY or ANTHROPIC_API_KEY in .env")
        sys.exit(1)

    client = None
    if anthropic_key and not openrouter_key:
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic()
    from src.event_store import EventStore
    from src.registry.client import ApplicantRegistryClient
    from src.agents.credit_analysis_agent import CreditAnalysisAgent

    store = EventStore(args.db_url)
    await store.connect()

    pool = await store._pool_or_raise()
    registry = ApplicantRegistryClient(pool)
    agent = CreditAnalysisAgent(
        agent_id="credit-agent-1",
        agent_type="credit_analysis",
        store=store,
        registry=registry,
        client=client,
    )

    app_id = args.application
    stream_id = f"loan-{app_id}"

    # Ensure loan stream exists with at least ApplicationSubmitted
    exists = await store.stream_exists(stream_id)
    if not exists:
        from src.models.events import ApplicationSubmitted
        from datetime import datetime, timezone
        await store.append(
            stream_id=stream_id,
            events=[
                ApplicationSubmitted(
                    application_id=app_id,
                    applicant_id="COMP-001",
                    requested_amount_usd=100_000,
                    loan_purpose="WorkingCapital",
                    submission_channel="api",
                    submitted_at=datetime.now(timezone.utc),
                )
            ],
            expected_version=-1,
        )
        print(f"Seeded {stream_id} with ApplicationSubmitted")

    print(f"Running credit analysis for {app_id}...")
    await agent.process_application(app_id)
    print(f"Done. Check stream: {stream_id}")

    await store.close()


if __name__ == "__main__":
    asyncio.run(main())
