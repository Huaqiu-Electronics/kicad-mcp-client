import sys
import os

try:
    MODULE_ROOT = os.path.dirname(os.path.abspath(__file__))
    if MODULE_ROOT not in sys.path:
        sys.path.append(MODULE_ROOT)
    from kicad_mcp_client.launch_mcp_client import launch_mcp_client

    launch_mcp_client()

except Exception as e:
    import logging

    logger = logging.getLogger()
    logger.debug(repr(e))
