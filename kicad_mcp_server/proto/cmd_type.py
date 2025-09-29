from enum import Enum


class CmdType(str,Enum):
    invalid = "invalid"
    apply_setting = "apply_setting"
    complete = "complete"
    quit = "quit"

