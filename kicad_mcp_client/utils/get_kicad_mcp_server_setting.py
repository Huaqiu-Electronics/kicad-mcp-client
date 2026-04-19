from mcp_agent.config import MCPServerSettings

from kicad_mcp_client import MODULE_ROOT_DIR

SERVER_DIR = (MODULE_ROOT_DIR / ".." / ".." / "kicad-mcp").resolve()
KICAD_MCP_SERVER_NAME = "kicad"


def get_kicad_mcp_server_setting(
    url: str | None,
    api_key: str | None,
    base_url: str | None,
    default_model: str | None,
    editor_type: str | None,
):
    print(f"[get_kicad_mcp_server_setting]: kicad-mcp dir is {SERVER_DIR}")

    if not url and not editor_type:
        raise ValueError("Either url or editor_type must be provided")    

    args = [
        "--directory",
        str(SERVER_DIR),
        "run",
        "kicad-mcp",
    ]
    if url:
        args.extend(["--socket-url", url])

    if api_key:
        args.extend(["--api-key", api_key])

    if base_url:
        args.extend(["--base-url", base_url])

    if default_model:
        args.extend(["--model", default_model])

    if editor_type:
        args.extend(["--editor-type", editor_type])
        
    print(f"[MCP] Launch args: {args}")
    return MCPServerSettings(
        name=KICAD_MCP_SERVER_NAME,
        description="KiCad MCP server for schematic and PCB automation",
        transport="stdio",
        command="uv",
        args=args,
    )
