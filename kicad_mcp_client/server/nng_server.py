import pynng
import json
from kicad_mcp_client.client.mcp_client import MCPClient
from kicad_mcp_client.proto.cmd_type import CmdType
import sys
from kicad_mcp_client.proto.cmd_apply_setting import CmdApplySetting
from kicad_mcp_client.proto.cmd_complete import CmdComplete
from kicad_mcp_client.proto.mcp_status import MCP_STATUS
from kicad_mcp_client.proto.mcp_status_msg import MCP_STATUS_MSG, MCP_STATUS_MSG_SUCCESS
from mcp_agent.config import Settings
from mcp_agent.app import MCPApp

from kicad_mcp_client.utils.get_kicad_mcp_server_setting import (
    KICAD_MCP_SERVER_NAME,
    get_kicad_mcp_server_setting,
)


class NNG_SERVER:
    mcp_client: MCPClient | None = None

    def __init__(self, sock: pynng.Pair0, kicad_sdk_port: int):
        self.sock = sock
        self.kicad_sdk_port = kicad_sdk_port

    def setup_mcp(self, mcp_settings: Settings):
        try:
            if mcp_settings.mcp and mcp_settings.mcp.servers:
                mcp_settings.mcp.servers[KICAD_MCP_SERVER_NAME] = (
                    get_kicad_mcp_server_setting(self.kicad_sdk_port)
                )
            self.mcp_client = MCPClient(
                MCPApp(name="kicad_mcp_client", settings=mcp_settings)
            )
            return MCP_STATUS_MSG_SUCCESS
        except Exception as e:
            return MCP_STATUS_MSG(msg=str(e), code=MCP_STATUS.FAILURE)

    async def _route(self, msg: str):
        try:
            parsed = json.loads(msg)
            cmd_base = parsed.get("cmd_type", None)

            if cmd_base == CmdType.apply_settings.value:
                cmd = CmdApplySetting.model_validate(parsed)
                return self.setup_mcp(cmd.mcp_settings)
            elif cmd_base == CmdType.complete.value:
                cmd = CmdComplete.model_validate(parsed)
                if self.mcp_client is None and cmd.mcp_settings is not None:
                    self.setup_mcp(cmd.mcp_settings)

                if self.mcp_client is None:
                    return MCP_STATUS_MSG(
                        msg="Without valid settings, MCP app is not initialized",
                        code=MCP_STATUS.FAILURE,
                    )
                return await self.mcp_client.complete(cmd)
            elif cmd_base == CmdType.quit.value:
                self.sock.close()
                sys.exit(0)

            return MCP_STATUS_MSG(
                msg=f"Invalid cmd : {cmd_base}", code=MCP_STATUS.FAILURE
            )

        except Exception as e:
            return MCP_STATUS_MSG(msg=str(e), code=MCP_STATUS.FAILURE)

    async def rec_send(self):
        while True:
            try:
                msg = self.sock.recv().decode()
                print("Receive msg: ", msg)
                res = await self._route(msg)
                try:
                    self.sock.send(res.model_dump_json().encode("utf-8"))
                except pynng.Timeout:
                    print("NNG send timeout")

            except pynng.Timeout:
                pass
