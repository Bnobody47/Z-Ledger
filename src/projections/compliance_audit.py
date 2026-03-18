"""
ComplianceAuditView projection: temporal query support (get_compliance_at),
snapshot strategy, rebuild_from_scratch(). SLO: lag < 2s.
"""
from src.projections.daemon import Projection


class ComplianceAuditProjection(Projection):
    name = "compliance_audit"

    async def handle(self, event) -> None:
        raise NotImplementedError
