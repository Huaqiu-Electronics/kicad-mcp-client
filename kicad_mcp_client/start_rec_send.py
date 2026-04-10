import asyncio
import argparse
import pynng

from kicad_mcp_client.server.nng_server import NNG_SERVER


VALID_EDITORS = ["schematic", "pcb", "footprint", "symbol"]


def parse_args():
    parser = argparse.ArgumentParser(
        description="NNG MCP Client - Receive and send messages"
    )

    parser.add_argument(
        "pair_url",
        type=str,
        help="NNG pair socket URL to listen on (e.g., ipc:///tmp/pair.sock)",
    )

    parser.add_argument(
        "kicad_sdk_url",
        type=str,
        help="KiCad SDK server URL",
    )

    parser.add_argument(
        "editor_type",
        type=str,
        choices=VALID_EDITORS,
        help="Editor type (schematic, pcb, footprint, symbol)",
    )

    parser.add_argument(
        "--recv-timeout",
        type=int,
        default=100,
        help="Receive timeout in milliseconds (default: 100)",
    )

    parser.add_argument(
        "--send-timeout",
        type=int,
        default=100,
        help="Send timeout in milliseconds (default: 100)",
    )

    return parser.parse_args()


def start_rec_send():
    args = parse_args()

    with pynng.Pair0(
        recv_timeout=args.recv_timeout,
        send_timeout=args.send_timeout
    ) as sock:
        print(f"[start_rec_send]: Listening to: {args.pair_url}")
        print(f"[start_rec_send]: Editor type: {args.editor_type}")

        sock.listen(args.pair_url)

        server = NNG_SERVER(sock, args.kicad_sdk_url, args.editor_type)
        asyncio.run(server.rec_send())


if __name__ == "__main__":
    start_rec_send()