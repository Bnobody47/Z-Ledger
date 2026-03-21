"""
Simulated crash recovery: 5 events appended, reconstruct_agent_context() called
without in-memory agent, verify reconstructed context is sufficient to continue.
"""
from __future__ import annotations

import pytest

from src.integrity.gas_town import reconstruct_agent_context
from src.models.events import AgentContextLoaded, BaseEvent


class AgentNodeExecuted(BaseEvent):
    event_type: str = "AgentNodeExecuted"
    node_name: str


@pytest.mark.asyncio
async def test_gas_town_crash_recovery(store):
    stream_id = "agent-a1-s1"
    await store.append(
        stream_id=stream_id,
        expected_version=-1,
        events=[
            AgentContextLoaded(
                agent_id="a1",
                session_id="s1",
                context_source="fresh",
                event_replay_from_position=0,
                context_token_count=100,
                model_version="m1",
            ),
            AgentNodeExecuted(node_name="load_inputs"),
            AgentNodeExecuted(node_name="run_analysis"),
            AgentNodeExecuted(node_name="write_output"),
            AgentNodeExecuted(node_name="PendingReview"),
        ],
    )
    reconstructed = await reconstruct_agent_context(store, "a1", "s1")
    assert reconstructed["last_event_position"] == 5
    assert reconstructed["context_text"]
    assert reconstructed["session_health_status"] == "NEEDS_RECONCILIATION"
