import asyncio

import pynng
import sys
from kicad_mcp_client.mcp_client import MCPClient
import logging

LOGGER = logging.getLogger()

def launch_mcp_client():
    LOGGER.info("Starting MCP Client")
    with pynng.Pair0(recv_timeout=100, send_timeout=100) as sock:
        if len(sys.argv) < 3:
            print("Usage: python mcp_client.py <url> <kicad_sdk_port>")
        url = sys.argv[1]
        LOGGER.info("Listening to: ", url)
        print("Listening to: ", url)
        sock.listen(url)
        client = MCPClient(sock, int(sys.argv[2]))
        asyncio.run(client.start())
