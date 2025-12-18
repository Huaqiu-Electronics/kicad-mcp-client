from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
from kicad_mcp_client.proto.cmd_complete import CmdComplete
from kicad_mcp_client.proto.mcp_complete_msg import MCP_COMPLETE_MSG
from kicad_mcp_client.proto.mcp_status import MCP_STATUS
from kicad_mcp_client.proto.mcp_status_msg import MCP_STATUS_MSG


class MCPClient:
    def __init__(self, app: MCPApp):
        self.app = app

    async def complete(self, cmd: CmdComplete):
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
