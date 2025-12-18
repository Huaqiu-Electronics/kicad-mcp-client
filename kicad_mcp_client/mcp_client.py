import json
from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.config import MCPServerSettings
from pathlib import Path

from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
import pynng
import sys
from kicad_mcp_client.proto.cmd_apply_setting import CmdApplySetting
from kicad_mcp_client.proto.cmd_complete import CmdComplete
from kicad_mcp_client.proto.cmd_type import CmdType
from kicad_mcp_client.proto.mcp_complete_msg import MCP_COMPLETE_MSG
from kicad_mcp_client.proto.mcp_status import MCP_STATUS
from kicad_mcp_client.proto.mcp_status_msg import MCP_STATUS_MSG, MCP_STATUS_MSG_SUCCESS
from mcp_agent.config import Settings

KICAD_MCP_SERVER_NAME = "kicad-mcp-server"

class MCPClient:
    app: MCPApp | None = None

    def get_kicad_mcp_server_setting(self) -> MCPServerSettings:
        client_dir = Path(__file__).resolve().parent
        server_dir = (client_dir / ".." / ".." / "kicad-mcp-server").resolve()
        return MCPServerSettings(
            name=KICAD_MCP_SERVER_NAME,
            description="KiCad MCP server for schematic and PCB automation",
            transport="stdio",
            command="uv",
            args=[
                "--directory",
                str(server_dir),
                "run",
                "main.py",
                str(self.kicad_sdk_port),
            ],
        )

    def __init__(self, sock: pynng.Pair0, sdk_port: int) -> None:
        self.sock = sock
        self.kicad_sdk_port = sdk_port

    async def complete(self, cmd: CmdComplete):
        if self.app is None and cmd.mcp_settings is not None:
            await self.setup_app(cmd.mcp_settings)

        if self.app is None:
            return MCP_STATUS_MSG(
                msg="Without valid settings, MCP app is not initialized",
                code=MCP_STATUS.FAILURE,
            )

        async with self.app.run() as agent_app:
            logger = agent_app.logger
            context = agent_app.context

            if context.config is not None:
                logger.info("Current config:", data=context.config.model_dump())
            else:
                logger.info("Current config: config is None")

            agent = Agent(
                name="agent",
                server_names=cmd.server_names,
            )

            async with agent:
                try:
                    llm = await agent.attach_llm(OpenAIAugmentedLLM)
                    msg = await llm.generate_str([cmd.msg])
                    logger.info(f"Summary: {msg}")

                    if len(msg) == 0:
                        return MCP_STATUS_MSG(
                            msg="No result from LLM, please check your MCP Settings",
                            code=MCP_STATUS.FAILURE,
                        )

                    return MCP_COMPLETE_MSG(msg=msg)
                except Exception as e:
                    return MCP_STATUS_MSG(msg=str(e), code=MCP_STATUS.FAILURE)

    async def setup_app(self, mcp_settings: Settings):
        try:
            if mcp_settings.mcp and mcp_settings.mcp.servers:
                mcp_settings.mcp.servers[KICAD_MCP_SERVER_NAME] = (
                    self.get_kicad_mcp_server_setting()
                )
            self.app = MCPApp(name="kicad_mcp_client", settings=mcp_settings)
            return MCP_STATUS_MSG_SUCCESS

        except Exception as e:
            self.app = None
            return MCP_STATUS_MSG(msg=str(e), code=MCP_STATUS.FAILURE)

    async def hdl_msg(self, msg: str):
        try:
            parsed = json.loads(msg)
            cmd_base = parsed.get("cmd_type", None)

            if cmd_base == CmdType.apply_settings.value:
                cmd = CmdApplySetting.model_validate(parsed)
                await self.setup_app(cmd.mcp_settings)
            elif cmd_base == CmdType.complete.value:
                cmd = CmdComplete.model_validate(parsed)
                return await self.complete(cmd)
            elif cmd_base == CmdType.quit.value:
                self.sock.close()
                sys.exit(0)

            return MCP_STATUS_MSG(
                msg=f"Invalid cmd : {cmd_base}", code=MCP_STATUS.FAILURE
            )

        except Exception as e:
            return MCP_STATUS_MSG(msg=str(e), code=MCP_STATUS.FAILURE)

    async def start(self):
        while True:
            try:
                msg = self.sock.recv().decode()
                print("Receive msg: ", msg)
                res = await self.hdl_msg(msg)

                try:
                    self.sock.send(res.model_dump_json().encode("utf-8"))
                except pynng.Timeout:
                    print("NNG send timeout")

            except pynng.Timeout:
                pass


