"""Offline tests for the transport core.

They run without an engine, against a stub that answers the plugin's health route and its MCP
handshake. What they exist for is the cases a live editor cannot produce on demand: no editor at
all, two editors at once, a port occupied by an unrelated program, and a nested array surviving
the exact serialization the CLI performs.

    python -m unittest discover -s cli/tests
"""

import io
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jutsu_mcp import stdio, transport  # noqa: E402

PROTOCOL_VERSION = "2025-11-25"
SESSION_ID = "stub-session"
INSTRUCTIONS = "Instructions the server owns and the CLI only forwards."


class _StubHandler(BaseHTTPRequestHandler):
    """Answers the plugin's health route and enough of the MCP surface to handshake and echo."""

    identity = transport.SERVER_IDENTITY

    def log_message(self, *_):
        pass

    def _send(self, status, body=None, headers=None):
        payload = b"" if body is None else json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        if payload:
            self.wfile.write(payload)

    def do_GET(self):
        if self.path != "/mcp/health":
            self._send(404, {})
            return
        self._send(200, {
            "server": self.identity,
            "pluginVersion": "9.9.9",
            "protocolVersion": PROTOCOL_VERSION,
            "acceptingRequests": True,
        })

    def do_DELETE(self):
        self._send(204)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        message = json.loads(self.rfile.read(length).decode("utf-8"))
        method = message.get("method")
        if method == "initialize":
            self._send(200, {
                "jsonrpc": "2.0",
                "id": message["id"],
                "result": {"protocolVersion": PROTOCOL_VERSION, "instructions": INSTRUCTIONS},
            }, {"MCP-Session-Id": SESSION_ID})
            return
        if message.get("id") is None:
            self._send(202)
            return
        # Echo the params straight back, so a test can compare what arrived with what was sent.
        self._send(200, {"jsonrpc": "2.0", "id": message["id"], "result": message.get("params")})


class _ForeignHandler(_StubHandler):
    identity = "something-else"


class Stub:
    """A stub server on an ephemeral loopback port, usable as a context manager."""

    def __init__(self, handler=_StubHandler):
        self.server = ThreadingHTTPServer((transport.HOST, 0), handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


def free_port():
    """A port nothing is listening on, for the editor-not-running cases."""
    with Stub() as stub:
        return stub.port


class PortResolutionTests(unittest.TestCase):
    def test_explicit_port_wins(self):
        self.assertEqual(transport.resolve_port(4242, environ={transport.PORT_ENVIRONMENT_VARIABLE: "1"}), 4242)

    def test_environment_is_consulted_after_the_flag(self):
        with tempfile.TemporaryDirectory() as directory:
            resolved = transport.resolve_port(
                environ={transport.PORT_ENVIRONMENT_VARIABLE: "4243"}, start_directory=directory
            )
        self.assertEqual(resolved, 4243)

    def test_project_file_is_consulted_after_the_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            with open(os.path.join(directory, transport.PORT_FILE_NAME), "w", encoding="utf-8") as handle:
                json.dump({"port": 4244}, handle)
            nested = os.path.join(directory, "a", "b")
            os.makedirs(nested)
            self.assertEqual(transport.resolve_port(environ={}, start_directory=nested), 4244)

    def test_a_malformed_project_file_names_itself(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, transport.PORT_FILE_NAME)
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("{}")
            with self.assertRaises(transport.TransportError) as raised:
                transport.resolve_port(environ={}, start_directory=directory)
        self.assertIn(transport.PORT_FILE_NAME, str(raised.exception))

    def test_a_port_outside_the_valid_range_is_refused(self):
        with self.assertRaises(transport.TransportError):
            transport.resolve_port(70000)

    def test_discovery_finds_one_server(self):
        with tempfile.TemporaryDirectory() as directory, Stub() as stub:
            resolved = transport.resolve_port(
                environ={}, start_directory=directory, candidates=(stub.port,)
            )
        self.assertEqual(resolved, stub.port)

    def test_two_servers_are_refused_by_name(self):
        with tempfile.TemporaryDirectory() as directory, Stub() as one, Stub() as two:
            with self.assertRaises(transport.TransportError) as raised:
                transport.resolve_port(
                    environ={}, start_directory=directory, candidates=(one.port, two.port)
                )
            message = str(raised.exception)
        self.assertIn(str(one.port), message)
        self.assertIn(str(two.port), message)
        self.assertIn("--port", message)

    def test_no_server_is_one_actionable_line(self):
        closed = free_port()
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(transport.TransportError) as raised:
                transport.resolve_port(environ={}, start_directory=directory, candidates=(closed,))
            message = str(raised.exception)
        self.assertNotIn("\n", message)
        self.assertIn("--port", message)

    def test_an_unrelated_program_on_the_port_is_named(self):
        with tempfile.TemporaryDirectory() as directory, Stub(_ForeignHandler) as stub:
            with self.assertRaises(transport.TransportError) as raised:
                transport.resolve_port(environ={}, start_directory=directory, candidates=(stub.port,))
            self.assertIn(str(stub.port), str(raised.exception))
            with self.assertRaises(transport.TransportError) as explicit:
                transport.probe(stub.port)
        self.assertIn("not a Jutsu Unreal MCP server", str(explicit.exception))


class ClientTests(unittest.TestCase):
    def test_handshake_forwards_the_servers_initialize_result(self):
        with Stub() as stub:
            client = transport.Client(stub.port)
            result = client.connect({"name": "test", "version": "1"})
            self.assertEqual(result["instructions"], INSTRUCTIONS)
            self.assertEqual(client.session_id, SESSION_ID)
            self.assertEqual(client.protocol_version, PROTOCOL_VERSION)
            client.close()

    def test_nested_arrays_survive_the_round_trip(self):
        connections = [
            [{"alias": "begin", "port": {"name": "then", "index": 0}},
             {"alias": "printer", "port": {"name": "execute", "index": 0}}],
            [{"alias": "printer", "port": {"name": "then", "index": 0}},
             {"alias": "done", "port": {"name": "execute", "index": 0}}],
        ]
        with Stub() as stub:
            client = transport.Client(stub.port)
            client.connect({"name": "test", "version": "1"})
            echoed = client.call("tools/call", {"connections": connections})["result"]
            client.close()
        self.assertEqual(echoed["connections"], connections)
        self.assertEqual(
            json.dumps(echoed["connections"], sort_keys=True),
            json.dumps(connections, sort_keys=True),
        )

    def test_calling_before_the_handshake_is_refused(self):
        with Stub() as stub:
            with self.assertRaises(transport.TransportError):
                transport.Client(stub.port).call("tools/list")

    def test_connecting_to_nothing_names_the_port(self):
        closed = free_port()
        with self.assertRaises(transport.TransportError) as raised:
            transport.Client(closed).connect({"name": "test", "version": "1"})
        self.assertIn(str(closed), str(raised.exception))


class StdioTests(unittest.TestCase):
    def test_startup_without_an_editor_exits_non_zero_with_one_line(self):
        closed = free_port()
        stderr = io.StringIO()
        original = sys.stderr
        sys.stderr = stderr
        try:
            code = stdio.main(["--port", str(closed)])
        finally:
            sys.stderr = original
        self.assertEqual(code, 2)
        self.assertEqual(len(stderr.getvalue().strip().splitlines()), 1)
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_initialize_is_answered_from_the_upstream_handshake(self):
        with Stub() as stub:
            client = transport.Client(stub.port)
            client.connect({"name": "test", "version": "1"})
            bridge = stdio.Bridge(client)
            response = bridge.handle({"jsonrpc": "2.0", "id": 7, "method": "initialize", "params": {}})
            client.close()
        self.assertEqual(response["id"], 7)
        self.assertEqual(response["result"]["instructions"], INSTRUCTIONS)

    def test_a_forwarded_call_keeps_the_hosts_request_id(self):
        with Stub() as stub:
            client = transport.Client(stub.port)
            client.connect({"name": "test", "version": "1"})
            bridge = stdio.Bridge(client)
            response = bridge.handle(
                {"jsonrpc": "2.0", "id": 11, "method": "tools/call", "params": {"nested": [[1, 2], [3]]}}
            )
            client.close()
        self.assertEqual(response["id"], 11)
        self.assertEqual(response["result"]["nested"], [[1, 2], [3]])

    def test_a_transport_failure_becomes_a_json_rpc_error_rather_than_a_crash(self):
        with Stub() as stub:
            client = transport.Client(stub.port)
            client.connect({"name": "test", "version": "1"})
        # The stub is gone now, which is what a closed editor looks like from here.
        output = io.StringIO()
        stdio.serve(client, io.StringIO('{"jsonrpc":"2.0","id":3,"method":"tools/list"}\n'), output)
        response = json.loads(output.getvalue())
        self.assertEqual(response["id"], 3)
        self.assertEqual(response["error"]["code"], stdio.TRANSPORT_ERROR_CODE)
        self.assertIn(str(client.port), response["error"]["message"])


if __name__ == "__main__":
    unittest.main()
