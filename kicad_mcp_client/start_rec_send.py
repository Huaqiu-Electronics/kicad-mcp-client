import asyncio

import pynng
import sys
import logging

from kicad_mcp_client.server.nng_server import NNG_SERVER

LOGGER = logging.getLogger()


def start_rec_send():
    LOGGER.info("Starting MCP Client")
    with pynng.Pair0(recv_timeout=100, send_timeout=100) as sock:
        if len(sys.argv) < 3:
            print("Usage: python mcp_client.py <url> <kicad_sdk_port>")
        url = sys.argv[1]
        LOGGER.info("Listening to: ", url)
        print("Listening to: ", url)
        sock.listen(url)
        server = NNG_SERVER(sock, int(sys.argv[2]))
        asyncio.run(server.rec_send())
