"""
MCP server entry point. Tools = Commands (write), Resources = Queries (read).
"""
from __future__ import annotations

import os

from fastmcp import FastMCP

from src.event_store import EventStore
from src.mcp.resources import register_resources
from src.mcp.tools import register_tools
from src.projections.agent_performance import AgentPerformanceProjection
from src.projections.application_summary import ApplicationSummaryProjection
from src.projections.compliance_audit import ComplianceAuditProjection
from src.projections.daemon import ProjectionDaemon


def build_server() -> tuple[FastMCP, ProjectionDaemon]:
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        raise RuntimeError("DATABASE_URL is required to start MCP server.")
    store = EventStore(db_url)
    projections = [
        ApplicationSummaryProjection(),
        AgentPerformanceProjection(),
        ComplianceAuditProjection(),
    ]
    daemon = ProjectionDaemon(store, projections=projections)
    mcp = FastMCP(name="z-ledger")
    register_tools(mcp, store, daemon)
    register_resources(mcp, store, daemon)
    return mcp, daemon


if __name__ == "__main__":
    mcp, _daemon = build_server()
    mcp.run()
