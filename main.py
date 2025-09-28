import asyncio
import time
import json
from pathlib import Path
from mcp_agent.app import MCPApp
from mcp_agent.config import Settings
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM

# Load settings directly using Pydantic's model capabilities
def load_settings_from_json(config_path: str) -> Settings:
    """Load settings from JSON file using Pydantic's model construction"""
    config_data = json.loads(Path(config_path).read_text(encoding='utf-8'))
    # Remove the $schema field as it's not part of the Settings model
    config_data.pop('$schema', None)
    return Settings.model_validate(config_data)

# Load settings from JSON file
settings = load_settings_from_json("mcp_agent.config.json")

app = MCPApp(name="kicad_mcp_client", settings=settings)

async def std_usage():
    async with app.run() as agent_app:
        logger = agent_app.logger
        context = agent_app.context

        logger.info("Current config:", data=context.config.model_dump())

        agent = Agent(
            name="agent",
            server_names=["markitdown", "playwright"],
        )

        async with agent:
            llm = await agent.attach_llm(OpenAIAugmentedLLM)
            res = await llm.generate_str(
                [
                    "从https://kicad.eda.cn/download上下载Windows 9.0.4的安装包",
                ]
            )
            logger.info(f"Summary: {res}")

if __name__ == "__main__":
    start = time.time()
    asyncio.run(std_usage())
    end = time.time()
    t = end - start
    print(f"Total run time: {t:.2f}s")