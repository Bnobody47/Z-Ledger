"""
AuditLedgerAggregate: append-only enforcement, cross-stream causal ordering.
Stream: audit-{entity_type}-{entity_id}
"""
from src.models.events import StoredEvent
from src.event_store import EventStore


class AuditLedgerAggregate:
    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.version = 0

    @classmethod
    async def load(
        cls, store: EventStore, entity_type: str, entity_id: str
    ) -> "AuditLedgerAggregate":
        stream_id = f"audit-{entity_type}-{entity_id}"
        events = await store.load_stream(stream_id)
        agg = cls(entity_type=entity_type, entity_id=entity_id)
        for event in events:
            agg._apply(event)
        return agg

    def _apply(self, event: StoredEvent) -> None:
        self.version = event.stream_position
