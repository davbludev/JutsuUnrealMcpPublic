"""An MCP server over stdio that forwards every call to a running Jutsu Unreal MCP editor.

The agent host launches this as a child process and sees an ordinary MCP server. It never learns
that an HTTP hop, a port or an Unreal editor exists behind it.

Nothing about the surface is authored here. The tool list, the input schemas, the ``instructions``
string, the server name and version, capability ids, error codes and ``recovery`` arrays are
whatever the live server answered; this module reframes JSON-RPC ids and forwards the rest
unchanged. Response bodies are not rendered or projected yet - that is task ``06.07``.
"""

import argparse
import json
import sys

from . import __version__
from .transport import Client, SessionExpired, TransportError, resolve_port

CLIENT_NAME = "jutsu-mcp-cli"

#: JSON-RPC implementation-defined server error, used only for the CLI's own transport failures.
TRANSPORT_ERROR_CODE = -32000

_STARTUP_FAILURE = 2


def _write(stream, message):
    # ensure_ascii=False keeps the server's own text byte-identical once encoded as UTF-8, and
    # json.dumps preserves nested arrays, which is what a document's connections depend on.
    stream.write(json.dumps(message, ensure_ascii=False) + "\n")
    stream.flush()


def _error(request_id, message):
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": TRANSPORT_ERROR_CODE, "message": message},
    }


class Bridge:
    """Translates the host's stdio JSON-RPC into calls on one live upstream session."""

    def __init__(self, client):
        self.client = client

    def handle(self, message):
        """Return the response to send back, or ``None`` for a notification.

        Only ``initialize`` is answered locally, from the handshake this process already
        completed; a second upstream ``initialize`` would open a second session and orphan the
        first. Every other method - including ones this build does not implement - is forwarded,
        so a method the registry gains works through the CLI with no edit here.
        """
        method = message.get("method")
        request_id = message.get("id")
        params = message.get("params")

        if method == "initialize":
            return {"jsonrpc": "2.0", "id": request_id, "result": self.client.initialize_result}

        if request_id is None:
            if method != "notifications/initialized":
                self.client.notify(method, params)
            return None

        response = self._forward(method, params)
        response["id"] = request_id
        return response

    def _forward(self, method, params):
        try:
            return self.client.call(method, params)
        except SessionExpired:
            self.client.connect(_client_info())
            return self.client.call(method, params)


def _client_info():
    return {"name": CLIENT_NAME, "version": __version__}


def serve(client, stdin, stdout):
    """Read newline-delimited JSON-RPC from ``stdin`` until it closes."""
    bridge = Bridge(client)
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except ValueError:
            _write(stdout, _error(None, "The CLI received a line that is not JSON-RPC."))
            continue
        if not isinstance(message, dict):
            _write(stdout, _error(None, "The CLI received a JSON-RPC message that is not an object."))
            continue

        try:
            response = bridge.handle(message)
        except TransportError as failure:
            request_id = message.get("id")
            if request_id is None:
                print("%s: %s" % (CLIENT_NAME, failure), file=sys.stderr, flush=True)
                continue
            response = _error(request_id, str(failure))
        if response is not None:
            _write(stdout, response)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog=CLIENT_NAME,
        description="Serve a running Unreal editor's Jutsu MCP tools over stdio.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Loopback port of the editor to talk to. Without it the port comes from "
             "JUTSU_MCP_PORT, then .jutsu-mcp.json, then discovery.",
    )
    arguments = parser.parse_args(argv)

    try:
        port = resolve_port(arguments.port)
        client = Client(port)
        client.connect(_client_info())
    except TransportError as failure:
        print("%s: %s" % (CLIENT_NAME, failure), file=sys.stderr, flush=True)
        return _STARTUP_FAILURE

    # The console default on Windows is a legacy code page, which would raise on any non-ASCII
    # character the server returned. MCP stdio is UTF-8 with newline-delimited messages.
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")

    try:
        serve(client, sys.stdin, sys.stdout)
    finally:
        client.close()
    return 0
