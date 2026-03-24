"""
Credit Analysis Agent — LangGraph agent that produces CreditAnalysisCompleted.
Reads from loan stream + applicant registry, writes to loan stream.
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from typing import Any, TypedDict

from langgraph.graph import StateGraph, END

from src.agents.base_agent import BaseApexAgent
from src.models.events import (
    CreditAnalysisCompleted,
    CreditAnalysisRequested,
)


class CreditState(TypedDict):
    application_id: str
    applicant_id: str | None
    requested_amount_usd: float | None
    loan_purpose: str | None
    company_profile: dict | None
    historical_financials: list | None
    compliance_flags: list | None
    loan_history: list | None
    credit_decision: dict | None
    errors: list[str]


class CreditAnalysisAgent(BaseApexAgent):
    """LangGraph credit analysis agent. Output: CreditAnalysisCompleted on loan stream."""

    def build_graph(self):
        g = StateGraph(CreditState)
        g.add_node("validate_inputs", self._node_validate_inputs)
        g.add_node("load_registry", self._node_load_registry)
        g.add_node("analyze", self._node_analyze)
        g.add_node("write_output", self._node_write_output)

        g.set_entry_point("validate_inputs")
        g.add_edge("validate_inputs", "load_registry")
        g.add_edge("load_registry", "analyze")
        g.add_edge("analyze", "write_output")
        g.add_edge("write_output", END)
        return g.compile()

    def _initial_state(self, application_id: str) -> CreditState:
        return CreditState(
            application_id=application_id,
            applicant_id=None,
            requested_amount_usd=None,
            loan_purpose=None,
            company_profile=None,
            historical_financials=None,
            compliance_flags=None,
            loan_history=None,
            credit_decision=None,
            errors=[],
        )

    async def process_application(self, application_id: str) -> None:
        if not hasattr(self, "_graph") or self._graph is None:
            self._graph = self.build_graph()
        self.application_id = application_id
        self.session_id = f"sess-credit-{application_id[:12]}"
        self._t0 = time.time()
        state = await self._graph.ainvoke(self._initial_state(application_id))
        if state and state.get("errors"):
            raise ValueError(f"Credit analysis failed: {state['errors']}")

    async def _node_validate_inputs(self, state: CreditState) -> CreditState:
        stream_id = f"loan-{state['application_id']}"
        events = await self.store.load_stream(stream_id)
        applicant_id = None
        requested = None
        purpose = None
        for e in events:
            p = getattr(e, "payload", None) or {}
            if isinstance(p, dict):
                applicant_id = applicant_id or p.get("applicant_id")
                requested = requested if requested is not None else p.get("requested_amount_usd")
                purpose = purpose or p.get("loan_purpose")

        return {
            **state,
            "applicant_id": applicant_id or "COMP-001",
            "requested_amount_usd": float(requested or 500_000),
            "loan_purpose": purpose or "WorkingCapital",
            "errors": state.get("errors", []),
        }

    async def _node_load_registry(self, state: CreditState) -> CreditState:
        applicant_id = state.get("applicant_id") or "COMP-001"
        profile = None
        financials: list[dict] = []
        flags: list[dict] = []
        loans: list[dict] = []

        try:
            if self.registry:
                profile_obj = await self.registry.get_company(applicant_id)
                if profile_obj:
                    profile = {
                        "name": profile_obj.name,
                        "industry": profile_obj.industry,
                        "jurisdiction": profile_obj.jurisdiction,
                        "legal_type": profile_obj.legal_type,
                        "trajectory": profile_obj.trajectory,
                    }
                financials_raw = await self.registry.get_financial_history(applicant_id)
                financials = [
                    {
                        "fiscal_year": f.fiscal_year,
                        "total_revenue": f.total_revenue,
                        "ebitda": f.ebitda,
                        "net_income": f.net_income,
                        "debt_to_equity": f.debt_to_equity,
                        "debt_to_ebitda": f.debt_to_ebitda,
                    }
                    for f in financials_raw
                ]
                flags_raw = await self.registry.get_compliance_flags(applicant_id)
                flags = [{"flag_type": f.flag_type, "severity": f.severity, "is_active": f.is_active} for f in flags_raw]
                loans = await self.registry.get_loan_relationships(applicant_id)
        except Exception:
            profile = {"name": "Company", "industry": "technology", "trajectory": "STABLE", "jurisdiction": "CA", "legal_type": "LLC"}

        return {
            **state,
            "company_profile": profile or {"name": "Unknown", "industry": "unknown", "trajectory": "STABLE"},
            "historical_financials": financials,
            "compliance_flags": flags,
            "loan_history": loans,
        }

    async def _node_analyze(self, state: CreditState) -> CreditState:
        hist = state.get("historical_financials") or []
        profile = state.get("company_profile") or {}
        flags = state.get("compliance_flags") or []
        loans = state.get("loan_history") or []
        requested = state.get("requested_amount_usd") or 500_000

        fins_table = "\n".join(
            f"FY{f.get('fiscal_year','')}: Revenue=${f.get('total_revenue',0):,.0f} EBITDA=${f.get('ebitda',0):,.0f}"
            for f in hist
        ) or "No historical data"

        system = """You are a commercial credit analyst. Return ONLY a JSON object:
{"risk_tier":"LOW"|"MEDIUM"|"HIGH","recommended_limit_usd":<int>,"confidence":<float 0-1>,
 "rationale":"<2-4 sentences>"}
Rules: recommended_limit_usd <= revenue*0.35; prior default → HIGH risk; active HIGH flag → confidence ≤ 0.50"""
        user = f"""Applicant: {profile.get('name','Unknown')} ({profile.get('industry','Unknown')})
Requested: ${requested:,.0f} for {state.get('loan_purpose','unknown')}
Financials:\n{fins_table}
Compliance: {json.dumps(flags)}
Prior loans: {json.dumps(loans)}
Return JSON only."""

        decision: dict[str, Any]
        try:
            content, _, _, _ = await self._call_llm(system, user, max_tokens=512)
            m = re.search(r"\{.*\}", content, re.DOTALL)
            decision = json.loads(m.group()) if m else {}
        except Exception as e:
            decision = {
                "risk_tier": "MEDIUM",
                "recommended_limit_usd": int(requested * 0.75),
                "confidence": 0.45,
                "rationale": f"Analysis deferred: {e}",
            }

        return {**state, "credit_decision": decision}

    async def _node_write_output(self, state: CreditState) -> CreditState:
        app_id = state["application_id"]
        d = state.get("credit_decision") or {}
        session_id = getattr(self, "session_id", f"credit-{app_id}")

        event = CreditAnalysisCompleted(
            application_id=app_id,
            agent_id=getattr(self, "agent_id", "credit-agent-1"),
            session_id=session_id,
            model_version=self.model,
            confidence_score=float(d.get("confidence", 0.5)),
            risk_tier=str(d.get("risk_tier", "MEDIUM")),
            recommended_limit_usd=float(d.get("recommended_limit_usd", 0)),
            analysis_duration_ms=int((time.time() - (self._t0 or time.time())) * 1000),
            input_data_hash=self._sha(state),
        )

        stream_id = f"loan-{app_id}"
        ver = await self.store.stream_version(stream_id) if await self.store.stream_exists(stream_id) else -1
        await self._append_with_retry(stream_id, [event], expected_version=ver)
        return state
