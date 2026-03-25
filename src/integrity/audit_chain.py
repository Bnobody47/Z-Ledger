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

    def _event_hashes(events) -> str:
        inner_hexdigests = [
            hashlib.sha256(
                json.dumps(e.payload, sort_keys=True, default=str).encode("utf-8")
            ).hexdigest()
            for e in events
        ]
        joined = "".join(inner_hexdigests).encode("utf-8")
        return hashlib.sha256(joined).hexdigest()

    entity_events = await store.load_stream(primary_stream)
    prior_checks = await store.load_stream(audit_stream)

    # Verify the existing chain (tamper detection).
    chain_valid = True
    tamper_detected = False
    prev_hash = ""
    prev_verified_count = 0
    for check in prior_checks:
        check_payload = check.payload
        current_verified_count = int(check_payload.get("events_verified_count", 0))
        expected_integrity_hash = hashlib.sha256(
            (prev_hash + _event_hashes(entity_events[prev_verified_count:current_verified_count])).encode(
                "utf-8"
            )
        ).hexdigest()
        actual_integrity_hash = check_payload.get("integrity_hash", "")

        if expected_integrity_hash != actual_integrity_hash:
            chain_valid = False
            tamper_detected = True

        prev_hash = actual_integrity_hash
        prev_verified_count = current_verified_count

    last_check = prior_checks[-1] if prior_checks else None
    previous_hash = last_check.payload.get("integrity_hash") if last_check else ""
    last_verified_count = int(last_check.payload.get("events_verified_count", 0)) if last_check else 0

    # Append a new check for the events since last verification.
    target_events = entity_events[last_verified_count:]
    event_hashes = _event_hashes(target_events)
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
        "chain_valid": chain_valid,
        "tamper_detected": tamper_detected,
        "integrity_hash": integrity_hash,
    }
