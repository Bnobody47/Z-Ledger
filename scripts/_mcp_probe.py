import asyncio, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.mcp.server import build_server

async def main():
    os.environ["DATABASE_URL"]="postgresql://bnobody:beahhal@localhost:5432/z_ledger"
    mcp, _daemon = build_server()
    res = await mcp.read_resource("ledger://ledger/health")
    print(type(res))
    print(res)

asyncio.run(main())
