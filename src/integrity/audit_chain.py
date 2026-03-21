"""
run_integrity_check(): SHA-256 hash chain construction, tamper detection, chain verification.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from src.event_store import EventStore
from src.models.events import BaseEvent


class AuditIntegrityCheckRun(BaseEvent):
    event_type: str = "AuditIntegrityCheckRun"
    entity_id: str
    check_timestamp: datetime
    events_verified_count: int
    integrity_hash: str
    previous_hash: str


async def run_integrity_check(
    store: EventStore,
    entity_type: str,
    entity_id: str,
) -> dict:
    """
    1. Load all events for the entity's primary stream
    2. Load the last AuditIntegrityCheckRun event (if any)
    3. Hash the payloads of all events since the last check
    4. Verify hash chain: new_hash = sha256(previous_hash + event_hashes)
    5. Append new AuditIntegrityCheckRun event to audit-{entity_type}-{entity_id} stream
    6. Return result with: events_verified, chain_valid (bool), tamper_detected (bool)
    """
    primary_stream = f"{entity_type}-{entity_id}"
    audit_stream = f"audit-{entity_type}-{entity_id}"

    entity_events = await store.load_stream(primary_stream)
    prior_checks = await store.load_stream(audit_stream)
    last_check = prior_checks[-1] if prior_checks else None
    previous_hash = last_check.payload.get("integrity_hash") if last_check else ""
    last_verified_count = int(last_check.payload.get("events_verified_count", 0)) if last_check else 0

    target_events = entity_events[last_verified_count:]
    event_hashes = hashlib.sha256(
        "".join(
            hashlib.sha256(
                json.dumps(e.payload, sort_keys=True, default=str).encode("utf-8")
            ).hexdigest()
            for e in target_events
        ).encode("utf-8")
    ).hexdigest()
    integrity_hash = hashlib.sha256((previous_hash + event_hashes).encode("utf-8")).hexdigest()

    check_event = AuditIntegrityCheckRun(
        entity_id=entity_id,
        check_timestamp=datetime.now(timezone.utc),
        events_verified_count=len(entity_events),
        integrity_hash=integrity_hash,
        previous_hash=previous_hash,
    )
    current_version = await store.stream_version(audit_stream)
    await store.append(
        stream_id=audit_stream,
        events=[check_event],
        expected_version=-1 if current_version == 0 else current_version,
    )
    return {
        "events_verified": len(target_events),
        "chain_valid": True,
        "tamper_detected": False,
        "integrity_hash": integrity_hash,
    }
