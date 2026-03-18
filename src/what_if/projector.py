"""
run_what_if(): counterfactual event injection with causal dependency filtering.
Never writes to real store.
"""
from src.event_store import EventStore


async def run_what_if(
    store: EventStore,
    application_id: str,
    branch_at_event_type: str,
    counterfactual_events: list,
    projections: list,
) -> dict:
    """Run counterfactual scenario. Returns real_outcome, counterfactual_outcome, divergence_events."""
    raise NotImplementedError
