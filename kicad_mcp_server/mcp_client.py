import asyncio
import time
import json
from pathlib import Path
from mcp_agent.app import MCPApp
from mcp_agent.config import Settings
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
import pynng
import sys
from kicad_mcp_server.utils.usage import usage
from kicad_mcp_server.utils.load_settings_from_json import load_settings_from_json



class MCPClient :
    app : MCPApp | None = None
    settings : Settings | None = None

    def __init__(self , sock : pynng.Pair0 ) -> None:
        self.sock = sock

    async def complete(self, msg :str):

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
                server_names=["markitdown", "playwright"],
            )

            async with agent:
                llm = await agent.attach_llm(OpenAIAugmentedLLM)
                res = await llm.generate_str(
                    [
                      msg
                    ]
                )
                logger.info(f"Summary: {res}")
                try:
                    self.sock.send(res.encode())
                except pynng.Timeout:
                    pass

    def setup_app(self , config_str: str) :        
        try:
            self.settings = load_settings_from_json("mcp_agent.config.json")
            self.app = MCPApp(name="kicad_mcp_client", settings=self.settings)
            
        except Exception as e:
            print("Error:", e)

    async def hdl_msg(self, msg :str):
        await self.complete(msg)
   
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