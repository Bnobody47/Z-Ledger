"""
run_integrity_check(): SHA-256 hash chain construction, tamper detection, chain verification.
"""
from src.event_store import EventStore


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
    raise NotImplementedError
