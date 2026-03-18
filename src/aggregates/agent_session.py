"""
AgentSessionAggregate: Gas Town context enforcement, model version tracking.
Stream: agent-{agent_id}-{session_id}
"""
from src.models.events import StoredEvent
from src.event_store import EventStore


class AgentSessionAggregate:
    def __init__(self, agent_id: str, session_id: str):
        self.agent_id = agent_id
        self.session_id = session_id
        self.version = 0
        self.context_loaded = False
        self.model_version: str | None = None

    @classmethod
    async def load(
        cls, store: EventStore, agent_id: str, session_id: str
    ) -> "AgentSessionAggregate":
        stream_id = f"agent-{agent_id}-{session_id}"
        events = await store.load_stream(stream_id)
        agg = cls(agent_id=agent_id, session_id=session_id)
        for event in events:
            agg._apply(event)
        return agg

    def _apply(self, event: StoredEvent) -> None:
        handler = getattr(self, f"_on_{event.event_type}", None)
        if handler:
            handler(event)
        self.version = event.stream_position

    def _on_AgentContextLoaded(self, event: StoredEvent) -> None:
        self.context_loaded = True
        self.model_version = event.payload.get("model_version")

    def assert_context_loaded(self) -> None:
        if not self.context_loaded:
            raise ValueError("AgentSession must have AgentContextLoaded before decisions")

    def assert_model_version_current(self, model_version: str) -> None:
        if self.model_version and self.model_version != model_version:
            raise ValueError(f"Model version mismatch: expected {self.model_version}, got {model_version}")
