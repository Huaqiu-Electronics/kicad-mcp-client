import pynng
import json
from kicad_mcp_client.client.mcp_client import MCPClient
from kicad_mcp_client.logs import LOG_DIR
from kicad_mcp_client.proto.cmd_type import CmdType
import sys
from kicad_mcp_client.proto.cmd_apply_setting import CmdApplySetting
from kicad_mcp_client.proto.cmd_complete import CmdComplete
from mcp_agent.config import Settings
from mcp_agent.app import MCPApp
import pathlib
from kicad_mcp_client.proto.mcp_agent_msg import (
    MCP_AGENT_CNF_CHANGED,
    MCP_AGENT_EXCEPTION,
)
from kicad_mcp_client.utils.get_cmd_absolute_path import get_cmd_absolute_path
from kicad_mcp_client.utils.get_kicad_mcp_server_setting import (
    KICAD_MCP_SERVER_NAME,
    get_kicad_mcp_server_setting,
)


class NNG_SERVER:
    mcp_client: MCPClient | None = None

    def __init__(self, sock: pynng.Pair0, kicad_sdk_url: str):
        self.sock = sock
        self.kicad_sdk_url = kicad_sdk_url

    def setup_mcp(self, mcp_settings: Settings):
        server_names = []
        if mcp_settings.mcp:
            if not mcp_settings.mcp.servers:
                mcp_settings.mcp.servers = {}

            mcp_settings.mcp.servers[KICAD_MCP_SERVER_NAME] = (
                get_kicad_mcp_server_setting(self.kicad_sdk_url)
            )

            for name, server_config in mcp_settings.mcp.servers.items():
                original_cmd = server_config.command
                if not original_cmd:
                    continue
                resolved_cmd = get_cmd_absolute_path(original_cmd)
                if resolved_cmd != original_cmd:
                    print(
                        f"[MCP] Resolved server '{name}' command: {original_cmd} -> {resolved_cmd}"
                    )
                    server_config.command = resolved_cmd
            if mcp_settings.logger:
                log_path = (
                    pathlib.Path(LOG_DIR) / "logs/mcp-agent-{unique_id}.jsonl"
                ).absolute()
                mcp_settings.logger.path_settings.path_pattern = str(log_path)  # type: ignore

            server_names = list(mcp_settings.mcp.servers.keys())
        self.mcp_client = MCPClient(
            MCPApp(name="kicad_mcp_client", settings=mcp_settings)
        )
        return server_names

    async def _route(self, msg: str):
        parsed = json.loads(msg)
        cmd_base = parsed.get("cmd_type", None)

        if cmd_base == CmdType.apply_settings.value:
            cmd = CmdApplySetting.model_validate(parsed)
            server_names = self.setup_mcp(cmd.mcp_settings)

            if self.mcp_client is None:
                raise Exception("Initialize the MCPClient failed")

            servers_assets = await self.mcp_client.get_servers_assets(server_names)
            return MCP_AGENT_CNF_CHANGED(
                servers_assets=servers_assets,
                mcp_settings=cmd.mcp_settings,
            )

        elif cmd_base == CmdType.complete.value:
            cmd = CmdComplete.model_validate(parsed)
            if self.mcp_client is None and cmd.mcp_settings is not None:
                self.setup_mcp(cmd.mcp_settings)

            if self.mcp_client is None:
                raise Exception("MCPClient is not initialized")

            return await self.mcp_client.complete(cmd)
        elif cmd_base == CmdType.quit.value:
            self.sock.close()
            sys.exit(0)

        raise Exception(f"Invalid cmd : {cmd_base}")

    async def rec_send(self):
        while True:
            try:
                msg = self.sock.recv().decode()
                print("Receive msg: ", msg)
                res = await self._route(msg)
                try:
                    self.sock.send(
                        res.model_dump_json(exclude_none=True).encode("utf-8")
                    )
                except pynng.Timeout:
                    print("NNG send timeout")
                except Exception as e:
                    self.sock.send(
                        (MCP_AGENT_EXCEPTION(msg=str(e)))
                        .model_dump_json(exclude_none=True)
                        .encode("utf-8")
                    )

            except pynng.Timeout:
                pass

            except Exception as e:
                print(e)
