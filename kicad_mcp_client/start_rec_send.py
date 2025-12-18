import asyncio

import pynng
import sys

from kicad_mcp_client.server.nng_server import NNG_SERVER


def start_rec_send():
    with pynng.Pair0(recv_timeout=100, send_timeout=100) as sock:
        if len(sys.argv) < 3:
            print("Usage: python mcp_client.py <url> <kicad_sdk_port>")
        url = sys.argv[1]
        print("[start_rec_send]: Listening to: ", url)
        sock.listen(url)
        server = NNG_SERVER(sock, int(sys.argv[2]))
        asyncio.run(server.rec_send())
