from enum import IntEnum
from pydantic import BaseModel
from mcp import ListPromptsResult, ListResourcesResult, ListToolsResult
from mcp_agent.config import Settings


class MCP_AGENT_MSG_TYPE(IntEnum):
    INVALID = 0
    exception = 1
    complete = 2
    cnf_changed = 3


class MCP_AGENT_EXCEPTION(BaseModel):
    type: MCP_AGENT_MSG_TYPE = MCP_AGENT_MSG_TYPE.exception
    msg: str


class MCP_AGENT_COMPLETE(BaseModel):
    type: MCP_AGENT_MSG_TYPE = MCP_AGENT_MSG_TYPE.complete
    msg: str


class MCP_AGENT_CNF_CHANGED(BaseModel):
    type: MCP_AGENT_MSG_TYPE = MCP_AGENT_MSG_TYPE.cnf_changed
    servers_assets: dict[
        str, list[ListResourcesResult | ListPromptsResult | ListToolsResult]
    ]
    mcp_settings: Settings
