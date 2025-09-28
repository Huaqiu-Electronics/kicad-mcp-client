import asyncio
import time
import json
from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
import pynng
import sys
from kicad_mcp_server.proto.cmd_apply_setting import CmdApplySetting
from kicad_mcp_server.proto.cmd_complete import CmdComplete
from kicad_mcp_server.proto.cmd_type import CmdType
from kicad_mcp_server.utils.usage import usage

class MCPClient :
    app : MCPApp | None = None

    def __init__(self , sock : pynng.Pair0 ) -> None:
        self.sock = sock

    async def complete(self, cmd :CmdComplete):

        if self.app is None:
            return

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
                llm = await agent.attach_llm(OpenAIAugmentedLLM)
                res = await llm.generate_str(
                    [
                      cmd.msg
                    ]
                )
                logger.info(f"Summary: {res}")
                try:
                    self.sock.send(res.encode('utf-8'))
                except pynng.Timeout:
                    pass

    def setup_app(self , cmd: CmdApplySetting) :        
        try:
            self.app = MCPApp(name="kicad_mcp_client", settings=cmd.mcp_settings)
            
        except Exception as e:
            print("Error:", e)

    async def hdl_msg(self, msg :str):
        try: 
            parsed = json.loads(msg)
            cmd_base = parsed.get("cmd_type", None)
            if cmd_base is None:
                print("Invalid command, missing cmd_type")
                return
            if cmd_base == CmdType.apply_setting.value :
                cmd = CmdApplySetting.model_validate(parsed)
                self.setup_app(cmd)
            elif cmd_base == CmdType.complete.value:
                cmd = CmdComplete.model_validate(parsed)
                await self.complete(cmd)
            else:
                print("Invalid command:", cmd_base)
        except Exception as e:
            print("Error:", e)

   
    async def start(self):
        while True:
            try:
                msg = self.sock.recv().decode()
                print("got message from", msg)
                await self.hdl_msg(msg)

            except pynng.Timeout:
                pass

            time.sleep(0.05)

def start_client():
    if len(sys.argv) < 2:
        usage()

    with pynng.Pair0(recv_timeout=100, send_timeout=100) as sock:
        sock.dial(sys.argv[1])
        client = MCPClient(sock)
        asyncio.run(client.start())