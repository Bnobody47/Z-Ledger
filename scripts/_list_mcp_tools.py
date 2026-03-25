import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.mcp.server import build_server


async def main() -> None:
    mcp, daemon = build_server()
    tools = await mcp.list_tools()
    print("TOOLS:")
    for t in tools:
        # FastMCP tool objects expose name
        print("-", t.name)
    resources = await mcp.list_resources()
    print("RESOURCES:")
    for r in resources:
        print("-", r.uri)


if __name__ == "__main__":
    asyncio.run(main())

