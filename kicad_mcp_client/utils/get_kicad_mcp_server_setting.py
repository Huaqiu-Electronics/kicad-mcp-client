from mcp_agent.config import MCPServerSettings
from pathlib import Path

SERVER_DIR = (
    Path(__file__).resolve().parent / ".." / ".." / "kicad-mcp-server"
).resolve()
KICAD_MCP_SERVER_NAME = "kicad-mcp-server"


def get_kicad_mcp_server_setting(port: int):
    return MCPServerSettings(
        name=KICAD_MCP_SERVER_NAME,
        description="KiCad MCP server for schematic and PCB automation",
        transport="stdio",
        command="uv",
        args=[
            "--directory",
            str(SERVER_DIR),
            "run",
            "main.py",
            str(port),
        ],
    )
