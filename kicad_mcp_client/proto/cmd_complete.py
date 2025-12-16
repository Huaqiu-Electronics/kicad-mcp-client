from typing import List
from .cmd_base import CmdBase
from mcp_agent.config import Settings
from mcp_agent.config import Settings


class CmdComplete(CmdBase):
    msg : str
    server_names : List[str]
    mcp_settings: Settings | None = None



