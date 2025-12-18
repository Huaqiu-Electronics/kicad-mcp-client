from .cmd_base import CmdBase
from mcp_agent.config import Settings


class CmdApplySetting(CmdBase):
    mcp_settings: Settings
