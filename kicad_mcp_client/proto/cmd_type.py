from enum import Enum


class CmdType(str, Enum):
    invalid = "invalid"
    apply_settings = "apply_settings"
    complete = "complete"
    quit = "quit"
