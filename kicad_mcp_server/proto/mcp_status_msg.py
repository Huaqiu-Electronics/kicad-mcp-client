from pydantic import BaseModel

from kicad_mcp_server.proto.mcp_status import MCP_STATUS

class  MCP_STATUS_MSG(BaseModel):
    code : MCP_STATUS
    msg :str | None= None


MCP_STATUS_MSG_SUCCESS = MCP_STATUS_MSG(code=MCP_STATUS.SUCCESS)
