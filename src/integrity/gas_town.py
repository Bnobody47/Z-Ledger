"""
reconstruct_agent_context(): agent memory reconstruction from event stream
with token budget, NEEDS_RECONCILIATION detection.
"""
from __future__ import annotations

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
    stream_id = f"agent-{agent_id}-{session_id}"
    events = await store.load_stream(stream_id)
    if not events:
        return {
            "context_text": "No prior session events.",
            "last_event_position": 0,
            "pending_work": [],
            "session_health_status": "EMPTY",
        }

    last_event = events[-1]
    pending = [
        {"event_type": e.event_type, "position": e.stream_position}
        for e in events
        if "PENDING" in e.event_type or "ERROR" in e.event_type
    ]
    summary_lines = [f"{e.stream_position}:{e.event_type}" for e in events[-20:]]
    context_text = "\n".join(summary_lines)
    if len(context_text) > token_budget:
        context_text = context_text[-token_budget:]

    session_health = "HEALTHY"
    if "Partial" in last_event.event_type or "Pending" in last_event.event_type:
        session_health = "NEEDS_RECONCILIATION"

    return {
        "context_text": context_text,
        "last_event_position": last_event.stream_position,
        "pending_work": pending,
        "session_health_status": session_health,
        "verbatim_tail": [
            {"event_type": e.event_type, "payload": e.payload}
            for e in events[-3:]
        ],
    }
