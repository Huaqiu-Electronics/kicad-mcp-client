import sys
import os

BASE_PATH = os.path.dirname(os.path.abspath(sys.executable))
SEARCH_PATHS = [BASE_PATH]
CMD_SUFFIXES = [".exe"]


def get_cmd_absolute_path(cmd: str) -> str:
    """
    Searches for the command in SEARCH_PATHS.
    Returns the absolute path if found, otherwise returns the original cmd.
    """
    # If the user provided a full path that exists, return it immediately
    if os.path.isfile(cmd):
        return os.path.abspath(cmd)

    for path in SEARCH_PATHS:
        # Check specific suffixes (e.g., cmd.exe)
        for suffix in [""] + CMD_SUFFIXES:
            full_path = os.path.join(path, cmd + suffix)
            if os.path.isfile(full_path):
                return os.path.abspath(full_path)

    # If not found in bundled paths, return the command as-is
    # (so the system PATH can handle it or it fails naturally later)
    return cmd
