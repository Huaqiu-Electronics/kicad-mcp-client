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
from kicad_mcp_server.proto.mcp_complete_msg import MCP_COMPLETE_MSG
from kicad_mcp_server.proto.mcp_status import MCP_STATUS
from kicad_mcp_server.proto.mcp_status_msg import MCP_STATUS_MSG, MCP_STATUS_MSG_SUCCESS
from kicad_mcp_server.utils.usage import usage

class MCPClient :
    app : MCPApp | None = None

    def __init__(self , sock : pynng.Pair0 ) -> None:
        self.sock = sock

    async def complete(self, cmd :CmdComplete):

        if self.app is None:
            return MCP_STATUS_MSG(msg="Without valid settings, MCP app is not initialized" , code= MCP_STATUS.FAILURE)

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
                msg = await llm.generate_str(
                    [
                      cmd.msg
                    ]
                )
                logger.info(f"Summary: {msg}")   

                return MCP_COMPLETE_MSG(msg=msg)

    def setup_app(self , cmd: CmdApplySetting) :        
        try:
            self.app = MCPApp(name="kicad_mcp_client", settings=cmd.mcp_settings)
            return MCP_STATUS_MSG_SUCCESS
            
        except Exception as e:
             return MCP_STATUS_MSG(msg=str(e) , code= MCP_STATUS.FAILURE)

    async def hdl_msg(self, msg :str):
        try: 
            parsed = json.loads(msg)
            cmd_base = parsed.get("cmd_type", None)

            if cmd_base == CmdType.apply_settings.value :
                cmd = CmdApplySetting.model_validate(parsed)
                return self.setup_app(cmd)
            elif cmd_base == CmdType.complete.value:
                cmd = CmdComplete.model_validate(parsed)
                return await self.complete(cmd)
            elif cmd_base == CmdType.quit.value:
                self.sock.close()
                sys.exit(0)                
    
            return MCP_STATUS_MSG(msg=f'Invalid cmd : {cmd_base}', code= MCP_STATUS.FAILURE)

        except Exception as e:
            return MCP_STATUS_MSG(msg=str(e), code= MCP_STATUS.FAILURE)
    
   
    async def start(self):
        while True:
            try:
                msg = self.sock.recv().decode()
                print("Receive msg: ", msg)
                res= await self.hdl_msg(msg)
                
                try:
                    self.sock.send(res.model_dump_json().encode('utf-8'))
                except pynng.Timeout:
                    print("NNG send timeout")
                
            except pynng.Timeout:
                pass

def start_client():
    with pynng.Pair0(recv_timeout=100, send_timeout=100) as sock:
        url = "ipc:///tmp/kicad_copilot_pair.ipc" if len(sys.argv) < 2 else sys.argv[1]
        sock.listen(url)
        client = MCPClient(sock)
        asyncio.run(client.start())