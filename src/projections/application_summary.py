"""
ApplicationSummary projection: one row per application, current state.
SLO: lag < 500ms.
"""
from src.projections.daemon import Projection


class ApplicationSummaryProjection(Projection):
    name = "application_summary"

    async def handle(self, event) -> None:
        raise NotImplementedError
