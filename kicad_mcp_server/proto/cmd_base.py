from pydantic import BaseModel

class CmdBase(BaseModel):
    cmd_type : str
