"""
ComplianceRecordAggregate: mandatory check tracking, regulation version references.
Stream: compliance-{application_id}
"""
from src.models.events import StoredEvent
from src.event_store import EventStore


class ComplianceRecordAggregate:
    def __init__(self, application_id: str):
        self.application_id = application_id
        self.version = 0

    @classmethod
    async def load(cls, store: EventStore, application_id: str) -> "ComplianceRecordAggregate":
        events = await store.load_stream(f"compliance-{application_id}")
        agg = cls(application_id=application_id)
        for event in events:
            agg._apply(event)
        return agg

    def _apply(self, event: StoredEvent) -> None:
        handler = getattr(self, f"_on_{event.event_type}", None)
        if handler:
            handler(event)
        self.version = event.stream_position
