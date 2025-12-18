from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
from kicad_mcp_client.proto.cmd_complete import CmdComplete
from kicad_mcp_client.proto.mcp_complete_msg import MCP_COMPLETE_MSG
from kicad_mcp_client.proto.servers_assets import ServersAssets


class MCPClient:
    def __init__(self, app: MCPApp):
        self.app = app

    async def complete(self, cmd: CmdComplete):
        async with self.app.run() as agent_app:
            logger = agent_app.logger
            context = agent_app.context

            agent = Agent(
                name="agent",
                server_names=cmd.server_names,
            )

            async with agent:
                llm = await agent.attach_llm(OpenAIAugmentedLLM)
                msg = await llm.generate_str([cmd.msg])
                logger.info(f"Summary: {msg}")

                if len(msg) == 0:
                    raise Exception(
                        f"No result from LLM, please check your MCP Settings : {context.config}"
                    )
                return MCP_COMPLETE_MSG(msg=msg)

    async def get_servers_assets(self):
        async with self.app.run():
            agent = Agent(
                name="agent",
            )
            assets = ServersAssets(assets={})
            async with agent:
                for server_name in agent.server_names:
                    assets.assets[server_name] = [
                        await agent.list_tools(server_name),
                        await agent.list_prompts(server_name),
                        await agent.list_resources(server_name),
                    ]
