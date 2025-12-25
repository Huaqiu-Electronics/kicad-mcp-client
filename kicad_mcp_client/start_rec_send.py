import asyncio

import pynng
import sys

from kicad_mcp_client.server.nng_server import NNG_SERVER


def start_rec_send():
    with pynng.Pair0(recv_timeout=100, send_timeout=100) as sock:
        if len(sys.argv) < 3:
            print("Usage: python mcp_client.py <pair_url> <kicad_sdk_url>")
        pair_url = sys.argv[1]
        print("[start_rec_send]: Listening to: ", pair_url)
        sock.listen(pair_url)
        kicad_sdk_url = NNG_SERVER(sock, sys.argv[2])
        asyncio.run(kicad_sdk_url.rec_send())
