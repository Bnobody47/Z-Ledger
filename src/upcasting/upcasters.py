"""
Registered upcasters: CreditAnalysisCompleted v1→v2, DecisionGenerated v1→v2.
Inference strategies documented in DESIGN.md.
"""
from src.upcasting.registry import UpcasterRegistry

registry = UpcasterRegistry()


@registry.register("CreditAnalysisCompleted", from_version=1)
def upcast_credit_v1_to_v2(payload: dict) -> dict:
    return {
        **payload,
        "model_version": "legacy-pre-2026",
        "confidence_score": None,
        "regulatory_basis": None,
    }


@registry.register("DecisionGenerated", from_version=1)
def upcast_decision_v1_to_v2(payload: dict) -> dict:
    return {
        **payload,
        "model_versions": {},
    }
