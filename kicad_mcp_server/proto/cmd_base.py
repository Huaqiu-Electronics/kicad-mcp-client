from pydantic import BaseModel
from .cmd_type import CmdType

class CmdBase(BaseModel):
    cmd_type : CmdType