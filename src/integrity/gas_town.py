"""
reconstruct_agent_context(): agent memory reconstruction from event stream
with token budget, NEEDS_RECONCILIATION detection.
"""
from src.event_store import EventStore


async def reconstruct_agent_context(
    store: EventStore,
    agent_id: str,
    session_id: str,
    token_budget: int = 8000,
) -> dict:
    """
    1. Load full AgentSession stream for agent_id + session_id
    2. Identify: last completed action, pending work items, current application state
    3. Summarise old events into prose (token-efficient)
    4. Preserve verbatim: last 3 events, any PENDING or ERROR state events
    5. Return: AgentContext with context_text, last_event_position,
       pending_work[], session_health_status
    CRITICAL: if the agent's last event was a partial decision (no corresponding
    completion event), flag the context as NEEDS_RECONCILIATION.
    """
    raise NotImplementedError
