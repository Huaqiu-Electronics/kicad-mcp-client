import pynng
import json
from kicad_mcp_client.client.mcp_client import MCPClient
from kicad_mcp_client.proto.cmd_type import CmdType
import sys
from kicad_mcp_client.proto.cmd_apply_setting import CmdApplySetting
from kicad_mcp_client.proto.cmd_complete import CmdComplete
from mcp_agent.config import Settings
from mcp_agent.app import MCPApp
import pathlib
from kicad_mcp_client.proto.mcp_agent_msg import (
    MCP_AGENT_CNF_CHANGED,
    MCP_AGENT_EXCEPTION,
    MCP_AGENT_LOG,
)
from kicad_mcp_client.utils.get_cmd_absolute_path_and_args import get_cmd_absolute_path_and_args
from kicad_mcp_client.utils.get_kicad_mcp_server_setting import (
    KICAD_MCP_SERVER_NAME,
    get_kicad_mcp_server_setting,
)

# Import necessary logging components
from mcp_agent.logging.transport import AsyncEventBus
from mcp_agent.logging.listeners import EventListener
from mcp_agent.logging.events import Event
import os

DEBUG_MCP_CLIENT = os.getenv("DEBUG_MCP_CLIENT", "0") == "1"

# Determine OS-independent writable directory
if os.name == "nt":  # Windows
    LOG_DIR = os.path.join(os.getenv("APPDATA", os.getenv("TEMP", os.getcwd())), "kicad-mcp", "kicad-mcp-server")
else:  # Linux/MacOS
    LOG_DIR = os.path.join(os.getenv("XDG_CACHE_HOME", os.path.join(os.getenv("HOME"), ".cache")), "kicad-mcp", "kicad-mcp-server")
os.makedirs(LOG_DIR, exist_ok=True)


class NNGForwardingLogListener(EventListener):
    """
    Listener that forwards MCP Agent log events through the NNG socket.
    """

    def __init__(self, sock: pynng.Pair0):
        self.sock = sock

    async def handle_event(self, event: Event):
        """Processes an incoming event and sends it over NNG."""

        if event.type == "debug":
            return  # Skip debug logs

        try:
            # Map the Event to your protocol's log model
            log_msg = MCP_AGENT_LOG(
                level=event.type,
                namespace=event.namespace,
                message=event.message,
                data=event.data,
                timestamp=event.timestamp.isoformat(),
            )

            # Send the serialized JSON over the socket
            self.sock.send(log_msg.model_dump_json(exclude_none=True).encode("utf-8"))
        except Exception as e:
            # Prevent logging errors from crashing the server
            print(f"[NNG Log Forwarder] Error: {e}")


class NNG_SERVER:
    mcp_client: MCPClient | None = None

    def __init__(self, sock: pynng.Pair0, kicad_sdk_url: str):
        self.sock = sock
        self.kicad_sdk_url = kicad_sdk_url
        self._setup_logging_bridge()

    def _setup_logging_bridge(self):
        """Registers the NNG listener with the global event bus."""
        bus = AsyncEventBus.get()
        bus.add_listener("nng_forwarder", NNGForwardingLogListener(self.sock))

    def setup_mcp(self, mcp_settings: Settings):
        server_names = []
        if mcp_settings.mcp:
            if not mcp_settings.mcp.servers:
                mcp_settings.mcp.servers = {}

            api_key = os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("OPENAI_BASE_URL")
            default_model = os.getenv("OPENAI_DEFAULT_MODEL")

            if mcp_settings.openai:
                api_key = mcp_settings.openai.api_key
                base_url = mcp_settings.openai.base_url
                default_model = mcp_settings.openai.default_model

            mcp_settings.mcp.servers[KICAD_MCP_SERVER_NAME] = (
                get_kicad_mcp_server_setting(self.kicad_sdk_url , api_key, base_url, default_model)
            )

            for name, server_config in mcp_settings.mcp.servers.items():
                original_cmd = server_config.command
                if not original_cmd:
                    continue
                resolved_cmd, resolved_args = get_cmd_absolute_path_and_args(original_cmd, server_config.args)
                print(f"[MCP] Resolved server '{name}' command: {original_cmd} -> {resolved_cmd} , args: {resolved_args} ")                    
                server_config.command = resolved_cmd
                server_config.args = resolved_args
            if mcp_settings.logger:
                if DEBUG_MCP_CLIENT:
                    log_path = (
                        pathlib.Path(LOG_DIR) / "mcp-agent-{unique_id}.jsonl"
                    ).absolute()
                    mcp_settings.logger.path_settings.path_pattern = str(log_path)  # type: ignore
                else:
                    mcp_settings.logger.type = "console"
                    mcp_settings.logger.level = "info"

            server_names = list(mcp_settings.mcp.servers.keys())
        self.mcp_client = MCPClient(
            MCPApp(name="kicad_mcp_client", settings=mcp_settings)
        )
        return server_names

    async def _route(self, msg: str):
        parsed = json.loads(msg)
        cmd_base = parsed.get("cmd_type", None)

        if cmd_base == CmdType.apply_settings.value:
            cmd = CmdApplySetting.model_validate(parsed)
            server_names = self.setup_mcp(cmd.mcp_settings)

            if self.mcp_client is None:
                raise Exception("Initialize the MCPClient failed")

            servers_assets = await self.mcp_client.get_servers_assets(server_names)
            return MCP_AGENT_CNF_CHANGED(
                servers_assets=servers_assets,
                mcp_settings=cmd.mcp_settings,
            )

        elif cmd_base == CmdType.complete.value:
            cmd = CmdComplete.model_validate(parsed)
            if self.mcp_client is None and cmd.mcp_settings is not None:
                self.setup_mcp(cmd.mcp_settings)

            if self.mcp_client is None:
                raise Exception("MCPClient is not initialized")

            return await self.mcp_client.complete(cmd)
        elif cmd_base == CmdType.quit.value:
            self.sock.close()
            sys.exit(0)

        raise Exception(f"Invalid cmd : {cmd_base}")

    async def rec_send(self):
        while True:
            try:
                # recv() is blocking; in a real async app consider sock.arecv()
                msg = self.sock.recv().decode()
                print("Receive msg: ", msg)
                res = await self._route(msg)
                try:
                    self.sock.send(
                        res.model_dump_json(exclude_none=True).encode("utf-8")
                    )
                except pynng.Timeout:
                    print("NNG send timeout")
                except Exception as e:
                    self.sock.send(
                        (MCP_AGENT_EXCEPTION(msg=str(e)))
                        .model_dump_json(exclude_none=True)
                        .encode("utf-8")
                    )

            except pynng.Timeout:
                pass

            except Exception as e:
                print(e)
