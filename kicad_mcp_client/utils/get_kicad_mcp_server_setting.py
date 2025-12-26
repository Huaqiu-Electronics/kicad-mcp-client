from mcp_agent.config import MCPServerSettings

from kicad_mcp_client import MODULE_ROOT_DIR

SERVER_DIR = (MODULE_ROOT_DIR / ".." / ".." / "kicad-mcp-server").resolve()
KICAD_MCP_SERVER_NAME = "kicad"


def get_kicad_mcp_server_setting(
    url: str, api_key: str | None, base_url: str | None, default_model: str | None
):
    print(f"[get_kicad_mcp_server_setting]: kicad-mcp-server dir is {SERVER_DIR}")
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
            url,
        ],
    )
