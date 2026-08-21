"""Prove the transport core against a running editor by comparing it with a raw HTTP client.

Run it with any Python 3 while an Unreal editor with the plugin is open:

    python cli/tests/check_live_transport.py --port 19781

The raw client below is written from scratch on ``urllib`` and shares no code with the transport
core, so an agreement between them is evidence rather than a tautology. Every call is issued
twice - once through each client - and the response bodies are compared exactly.

This file is a test, not CLI source, so it is allowed to name capabilities. The vocabulary check
only scans the package the agent actually talks to.
"""

import argparse
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jutsu_mcp.transport import Client, TransportError, resolve_port  # noqa: E402

ASSET = "/Game/JutsuMcpCli/BP_CliTransportProof.BP_CliTransportProof"
PACKAGE_PATH = "/Game/JutsuMcpCli"
ASSET_NAME = "BP_CliTransportProof"

#: connections are arrays of pairs. A converter that flattens a nested array corrupts this
#: document silently, which is the failure mode the transport is tested against.
CONNECTIONS = [
    [
        {"alias": "begin", "port": {"name": "then", "direction": "output", "index": 0}},
        {"alias": "printer", "port": {"name": "execute", "direction": "input", "index": 0}},
    ]
]

DOCUMENT = {
    "documentVersion": "1.0",
    "target": {"domain": "blueprint.graph", "asset": ASSET, "graph": {"name": "EventGraph"}},
    "requirements": [],
    "nodes": {
        "begin": {
            "create": {"kind": "event", "owner": "/Script/Engine.Actor", "member": "ReceiveBeginPlay"},
            "authoringId": "cli-begin",
        },
        "printer": {
            "create": {
                "kind": "function_call",
                "owner": "/Script/Engine.KismetSystemLibrary",
                "member": "PrintString",
            },
            "authoringId": "cli-printer",
        },
    },
    "pinDefaults": [
        {
            "target": {
                "alias": "printer",
                "port": {"name": "InString", "direction": "input", "type": {"category": "string"}, "index": 0},
            },
            "value": "nested arrays survived the CLI",
        }
    ],
    "connections": CONNECTIONS,
    "properties": [],
    "lifecycle": {"compile": "if_changed", "save": "explicit"},
}


class RawClient:
    """A minimal MCP-over-HTTP client that shares nothing with the transport core."""

    def __init__(self, port):
        self.url = "http://127.0.0.1:%d/mcp" % port
        self.session_id = None
        self.protocol_version = None
        self.next_id = 1000

    def post(self, body, headers=None):
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        merged = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
        merged.update(headers or {})
        request = urllib.request.Request(self.url, data=payload, headers=merged, method="POST")
        with urllib.request.urlopen(request) as response:
            return response.read(), dict(response.headers)

    def connect(self):
        with urllib.request.urlopen("http://127.0.0.1:%d/mcp/health" % _PORT) as response:
            self.protocol_version = json.loads(response.read().decode("utf-8"))["protocolVersion"]
        body, headers = self.post(
            {
                "jsonrpc": "2.0",
                "id": 999,
                "method": "initialize",
                "params": {
                    "protocolVersion": self.protocol_version,
                    "capabilities": {},
                    "clientInfo": {"name": "raw-check", "version": "1"},
                },
            }
        )
        self.session_id = headers["MCP-Session-Id"]
        self.post(
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            self._session_headers(),
        )
        return json.loads(body.decode("utf-8"))["result"]

    def _session_headers(self):
        return {"MCP-Session-Id": self.session_id, "MCP-Protocol-Version": self.protocol_version}

    def call(self, name, arguments):
        self.next_id += 1
        body, _ = self.post(
            {
                "jsonrpc": "2.0",
                "id": self.next_id,
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            },
            self._session_headers(),
        )
        return json.loads(body.decode("utf-8"))["result"]

    def close(self):
        request = urllib.request.Request(self.url, method="DELETE", headers=self._session_headers())
        urllib.request.urlopen(request).close()


_PORT = 0
_FAILURES = []


def check(label, condition, detail=""):
    if condition:
        print("  ok   %s" % label)
    else:
        print("  FAIL %s %s" % (label, detail))
        _FAILURES.append(label)


def cli_call(client, name, arguments):
    """Return the JSON-RPC result of one tools/call, exactly as the server framed it."""
    return client.call("tools/call", {"name": name, "arguments": arguments})["result"]


def main(argv=None):
    global _PORT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=None)
    arguments = parser.parse_args(argv)

    try:
        _PORT = resolve_port(arguments.port)
    except TransportError as failure:
        print("check_live_transport: %s" % failure, file=sys.stderr)
        return 2
    print("editor on 127.0.0.1:%d" % _PORT)

    cli = Client(_PORT)
    cli_initialize = cli.connect({"name": "check-live-transport", "version": "1"})
    raw = RawClient(_PORT)
    raw_initialize = raw.connect()

    try:
        check(
            "initialize instructions are byte-identical",
            cli_initialize["instructions"] == raw_initialize["instructions"],
        )
        check(
            "initialize results agree",
            cli_initialize == raw_initialize,
            "%r vs %r" % (cli_initialize, raw_initialize),
        )

        cli_tools = cli.call("tools/list")["result"]["tools"]
        raw_body, _ = raw.post(
            {"jsonrpc": "2.0", "id": 5000, "method": "tools/list"}, raw._session_headers()
        )
        raw_tools = json.loads(raw_body.decode("utf-8"))["result"]["tools"]
        check("tools/list agrees", cli_tools == raw_tools)
        check("tools/list is the five fixed tools", len(cli_tools) == 5, str(len(cli_tools)))

        describe_arguments = {"requests": [{"id": "core.authoring.apply"}, {"id": "core.inspect"}]}
        check(
            "describe agrees",
            cli_call(cli, "jutsu_capabilities_describe", describe_arguments)
            == raw.call("jutsu_capabilities_describe", describe_arguments),
        )

        # Fixture, created through the raw client so the comparison below starts from a state
        # neither client produced on its own.
        raw.call(
            "jutsu_execute",
            {"steps": [{"stepId": "clean", "capability": "asset.delete",
                        "arguments": {"asset": ASSET, "destructive": True, "force": True,
                                      "allowMissing": True}}]},
        )
        created = raw.call(
            "jutsu_execute",
            {"steps": [{"stepId": "create", "capability": "blueprint.create",
                        "arguments": {"packagePath": PACKAGE_PATH, "name": ASSET_NAME,
                                      "parentClass": "/Script/Engine.Actor",
                                      "blueprintType": "class"}}]},
        )
        check("fixture blueprint created", "error" not in created, json.dumps(created)[:400])

        inspect_arguments = {"requests": [{"capability": "core.inspect", "arguments": {"asset": ASSET}}]}
        check(
            "inspect agrees",
            cli_call(cli, "jutsu_inspect", inspect_arguments)
            == raw.call("jutsu_inspect", inspect_arguments),
        )

        # An execute batch carrying nested arrays. The first application changes the graph, so
        # the comparison is made between two later re-applications of the same document: both
        # start from a satisfied graph and must answer identically.
        execute_arguments = {
            "steps": [{"stepId": "apply", "capability": "core.authoring.apply", "arguments": DOCUMENT}],
            "response": {"detail": "full"},
        }
        first = raw.call("jutsu_execute", execute_arguments)
        check("first apply succeeded", "error" not in first and first.get("status") != "failed",
              json.dumps(first)[:600])
        raw_repeat = raw.call("jutsu_execute", execute_arguments)
        cli_repeat = cli_call(cli, "jutsu_execute", execute_arguments)
        check("execute batch with nested-array connections agrees", raw_repeat == cli_repeat,
              json.dumps({"raw": raw_repeat, "cli": cli_repeat})[:800])

        read_arguments = {"requests": [{"capability": "core.authoring.read",
                                        "arguments": {"target": DOCUMENT["target"]}}]}
        read = cli_call(cli, "jutsu_inspect", read_arguments)
        document = read["structuredContent"]["results"][0]["result"]["document"]
        connections = document.get("connections")
        check(
            "connections came back as arrays of pairs",
            isinstance(connections, list)
            and len(connections) == 1
            and isinstance(connections[0], list)
            and len(connections[0]) == 2
            and connections[0][0]["port"]["name"] == "then",
            json.dumps(connections)[:600],
        )

        error_arguments = {"requests": [{"id": "no.such.capability.exists"}]}
        cli_error = cli_call(cli, "jutsu_capabilities_describe", error_arguments)
        raw_error = raw.call("jutsu_capabilities_describe", error_arguments)
        check("intentional error agrees", cli_error == raw_error,
              json.dumps({"raw": raw_error, "cli": cli_error})[:800])
        check("intentional error is a diagnostic", "error" in json.dumps(cli_error),
              json.dumps(cli_error)[:400])
    finally:
        cli.close()
        raw.close()

    if _FAILURES:
        print("\n%d check(s) failed: %s" % (len(_FAILURES), ", ".join(_FAILURES)))
        return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
