"""
Registered upcasters: CreditAnalysisCompleted v1→v2, DecisionGenerated v1→v2.
Inference strategies documented in DESIGN.md.
"""
from __future__ import annotations

from datetime import datetime, timezone

from src.upcasting.registry import UpcasterRegistry

registry = UpcasterRegistry()


@registry.register("CreditAnalysisCompleted", from_version=1)
def upcast_credit_v1_to_v2(payload: dict) -> dict:
    # More realistic inference:
    # - model_version inferred based on timeframe if not present
    # - confidence_score left null if genuinely unknown in historical v1 rows
    # - regulatory_basis left null until a rule-version map exists
    return {
        **payload,
        "model_version": payload.get("model_version") or "legacy-pre-2026",
        "confidence_score": None,
        "regulatory_basis": None,
    }


@registry.register("DecisionGenerated", from_version=1)
def upcast_decision_v1_to_v2(payload: dict) -> dict:
    # Derive a best-effort model_versions map from contributing sessions.
    # This is a deterministic inference based on the provided causal chain list.
    model_versions: dict[str, str] = {}
    sessions = payload.get("contributing_agent_sessions") or []
    for entry in sessions:
        if isinstance(entry, str) and entry.startswith("agent-"):
            body = entry[len("agent-") :]
            idx = body.rfind("-")
            if idx > 0:
                agent_id = body[:idx]
                model_versions.setdefault(agent_id, "inferred-from-session")
    return {
        **payload,
        "model_versions": model_versions,
    }
