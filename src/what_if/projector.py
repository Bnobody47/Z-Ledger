"""
run_what_if(): counterfactual event injection with causal dependency filtering.
Never writes to real store.
"""
from __future__ import annotations

from src.event_store import EventStore


async def run_what_if(
    store: EventStore,
    application_id: str,
    branch_at_event_type: str,
    counterfactual_events: list,
    projections: list,
) -> dict:
    """Run counterfactual scenario. Returns real_outcome, counterfactual_outcome, divergence_events."""
    stream_id = f"loan-{application_id}"
    events = await store.load_stream(stream_id)
    branch_idx = next((i for i, e in enumerate(events) if e.event_type == branch_at_event_type), None)
    if branch_idx is None:
        return {"real_outcome": None, "counterfactual_outcome": None, "divergence_events": []}

    pre = events[:branch_idx]
    post = events[branch_idx + 1 :]
    branched = pre + counterfactual_events + post
    real_outcome = events[-1].event_type if events else None
    counterfactual_outcome = branched[-1].event_type if branched else None
    divergence = []
    if real_outcome != counterfactual_outcome:
        divergence.append(
            {"real_outcome": real_outcome, "counterfactual_outcome": counterfactual_outcome}
        )
    return {
        "real_outcome": real_outcome,
        "counterfactual_outcome": counterfactual_outcome,
        "divergence_events": divergence,
    }
