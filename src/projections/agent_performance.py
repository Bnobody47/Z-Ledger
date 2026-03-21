"""
AgentPerformanceLedger projection: metrics per agent model version.
"""
from src.projections.daemon import Projection


class AgentPerformanceProjection(Projection):
    name = "agent_performance"

    async def handle(self, event, store) -> None:
        if event.event_type != "CreditAnalysisCompleted":
            return
        agent_id = event.payload.get("agent_id")
        model_version = event.payload.get("model_version")
        if not agent_id or not model_version:
            return

        await store.execute(
            """
            INSERT INTO projection_agent_performance (
                agent_id, model_version, analyses_completed, avg_confidence_score, avg_duration_ms,
                first_seen_at, last_seen_at
            ) VALUES ($1, $2, 1, $3, $4, NOW(), NOW())
            ON CONFLICT (agent_id, model_version)
            DO UPDATE SET analyses_completed = projection_agent_performance.analyses_completed + 1,
                          avg_confidence_score =
                              (COALESCE(projection_agent_performance.avg_confidence_score, 0)
                              * projection_agent_performance.analyses_completed + EXCLUDED.avg_confidence_score)
                              / (projection_agent_performance.analyses_completed + 1),
                          avg_duration_ms =
                              (COALESCE(projection_agent_performance.avg_duration_ms, 0)
                              * projection_agent_performance.analyses_completed + EXCLUDED.avg_duration_ms)
                              / (projection_agent_performance.analyses_completed + 1),
                          last_seen_at = NOW()
            """,
            agent_id,
            model_version,
            float(event.payload.get("confidence_score") or 0),
            float(event.payload.get("analysis_duration_ms") or 0),
        )
