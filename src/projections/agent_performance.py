"""
AgentPerformanceLedger projection: metrics per agent model version.
"""
from src.projections.daemon import Projection


class AgentPerformanceProjection(Projection):
    name = "agent_performance"

    async def handle(self, event) -> None:
        raise NotImplementedError
