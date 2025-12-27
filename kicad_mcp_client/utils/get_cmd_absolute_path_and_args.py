import os
import sys
from typing import List, Tuple

BASE_PATH = os.path.dirname(os.path.abspath(sys.executable))
CMD_SUFFIXES = [".exe"]


def _resolve_cmd(cmd: str) -> str:
    """
    Resolve command from BASE_PATH (bundled executables).
    """
    if os.path.isfile(cmd):
        return os.path.abspath(cmd)

    for suffix in [""] + CMD_SUFFIXES:
        full_path = os.path.join(BASE_PATH, cmd + suffix)
        if os.path.isfile(full_path):
            return os.path.abspath(full_path)

    return cmd


def get_cmd_absolute_path_and_args(
    cmd: str, args: List[str] | None
) -> Tuple[str, List[str]]:
    """
    Resolve command and args.

    Rewrite:
        npx <args>  →  bun.exe x <args>
    """

    args = list(args or [])

    # ---- npx → bun x ----
    if cmd == "npx":
        resolved_bun = _resolve_cmd("bun")
        return resolved_bun, ["x"] + args

    # ---- normal resolution ----
    resolved_cmd = _resolve_cmd(cmd)
    return resolved_cmd, args
