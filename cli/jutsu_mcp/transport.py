"""Everything hard about talking to a running Jutsu Unreal MCP server.

The server is reached over loopback HTTP. It requires a session header, it may be on one of
several ports, the editor may be closed, and the JSON it exchanges contains nested arrays that
naive conversion destroys. This module owns all four problems and returns the server's own
response bodies unchanged.

Nothing here is derived from the capability registry. Tool names, schemas, capability ids,
descriptions, error codes and the ``instructions`` string all arrive from the live server and are
forwarded; the only text this module authors is its own transport diagnostics, which describe the
CLI's situation and have no counterpart on the server.
"""

import json
import os
import urllib.error
import urllib.request

#: The CLI is a loopback client. The host is not configurable and no socket is ever listened on.
HOST = "127.0.0.1"

#: Ports probed when no explicit port was given, covering the plugin's shipping default and the
#: engine test editor without making either one the only reachable value: an explicit port, the
#: environment variable and the project file all reach any port at all.
DISCOVERY_PORTS = tuple(range(19780, 19790))

#: Environment variable consulted after an explicit port and before the project file.
PORT_ENVIRONMENT_VARIABLE = "JUTSU_MCP_PORT"

#: Per-project file, looked up in the working directory and then in each ancestor of it.
PORT_FILE_NAME = ".jutsu-mcp.json"

#: What ``GET /mcp/health`` answers with when the plugin is the thing listening.
SERVER_IDENTITY = "jutsu-unreal-mcp"

_HEALTH_TIMEOUT_SECONDS = 1.0
_ACCEPT = "application/json, text/event-stream"


class TransportError(Exception):
    """A transport failure the caller should report as one actionable line.

    Every message names what was tried and what to do next, and none of them carry a stack
    trace to the user.
    """


class SessionExpired(TransportError):
    """The server no longer knows this session, which is what an editor restart looks like.

    It is raised only for a request the server rejected before dispatching it, so a caller may
    hand the same request to a fresh session without risking a second application of it.
    """


def _address(port):
    return "%s:%d" % (HOST, port)


def _health_url(port):
    return "http://%s/mcp/health" % _address(port)


def _endpoint_url(port):
    return "http://%s/mcp" % _address(port)


#: Sentinel returned by :func:`inspect_port` when a port answers but is not this plugin. It is
#: distinct from ``None`` because "the port is taken by something else" and "the editor is not
#: running" need different fixes from the caller.
FOREIGN = object()


def inspect_port(port, timeout=_HEALTH_TIMEOUT_SECONDS):
    """Classify what is listening on ``port``: the plugin, something else, or nothing.

    Returns the parsed health record, :data:`FOREIGN`, or ``None``.
    """
    request = urllib.request.Request(_health_url(port), method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
    except urllib.error.HTTPError:
        return FOREIGN
    except (urllib.error.URLError, OSError):
        return None

    try:
        health = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return FOREIGN
    if not isinstance(health, dict) or health.get("server") != SERVER_IDENTITY:
        return FOREIGN
    return health


def probe(port, timeout=_HEALTH_TIMEOUT_SECONDS):
    """Return the health record of the plugin listening on ``port``, or ``None``.

    Raises when something answers that is not this plugin, since a caller who named a port
    deserves to be told the port is occupied rather than told the editor is down.
    """
    health = inspect_port(port, timeout)
    if health is FOREIGN:
        raise TransportError(
            "%s answered, but it is not a Jutsu Unreal MCP server. Another program is using "
            "the port, or the installed plugin predates its health route. Pass --port for the "
            "editor you mean." % _address(port)
        )
    return health


def _port_from_file(start_directory):
    directory = os.path.abspath(start_directory)
    while True:
        candidate = os.path.join(directory, PORT_FILE_NAME)
        if os.path.isfile(candidate):
            try:
                with open(candidate, "r", encoding="utf-8") as handle:
                    document = json.load(handle)
                port = document["port"]
            except (OSError, ValueError, KeyError, TypeError):
                raise TransportError(
                    "%s must be JSON holding an integer port, as {\"port\": 19782}." % candidate
                )
            return _validated_port(port, candidate)
        parent = os.path.dirname(directory)
        if parent == directory:
            return None
        directory = parent


def _validated_port(value, source):
    try:
        port = int(value)
    except (TypeError, ValueError):
        raise TransportError("%s must be a port number between 1 and 65535, not %r." % (source, value))
    if not 1 <= port <= 65535:
        raise TransportError("%s must be a port number between 1 and 65535, not %r." % (source, value))
    return port


def _discover(candidates):
    """Split ``candidates`` into plugin servers and ports occupied by something else."""
    found = []
    foreign = []
    for port in candidates:
        health = inspect_port(port)
        if health is FOREIGN:
            foreign.append(port)
        elif health is not None:
            found.append((port, health))
    return found, foreign


def resolve_port(port=None, environ=None, start_directory=None, candidates=DISCOVERY_PORTS):
    """Resolve the port to talk to, by the first layer that produces one.

    The layers are an explicit ``port``, the ``JUTSU_MCP_PORT`` environment variable, a
    ``.jutsu-mcp.json`` file in ``start_directory`` or an ancestor of it, and finally discovery
    over ``candidates``.

    Discovery refuses to guess. Two editors open at once is the normal case on a development
    machine, and picking one silently would let an agent author into the wrong project.
    """
    if port is not None:
        return _validated_port(port, "--port")

    environ = os.environ if environ is None else environ
    from_environment = environ.get(PORT_ENVIRONMENT_VARIABLE)
    if from_environment:
        return _validated_port(from_environment, PORT_ENVIRONMENT_VARIABLE)

    from_file = _port_from_file(os.getcwd() if start_directory is None else start_directory)
    if from_file is not None:
        return from_file

    found, foreign = _discover(candidates)
    if len(found) == 1:
        return found[0][0]
    if not found:
        occupied = ""
        if foreign:
            occupied = " Ports %s answered but are not this plugin." % ", ".join(
                str(port) for port in foreign
            )
        raise TransportError(
            "No Jutsu Unreal MCP server answered on %s ports %d-%d. "
            "Start the Unreal editor with the plugin enabled, or pass --port.%s"
            % (HOST, candidates[0], candidates[-1], occupied)
        )
    listed = ", ".join(
        "%s (plugin %s)" % (_address(found_port), health.get("pluginVersion", "unknown"))
        for found_port, health in found
    )
    raise TransportError(
        "%d Jutsu Unreal MCP servers are listening: %s. Pass --port to choose one." % (len(found), listed)
    )


class Client:
    """One MCP session against one editor.

    The session is opened once and reused for every later call, which is what the stdio front
    end needs and what keeps the server's per-session pagination snapshots alive.
    """

    def __init__(self, port):
        self.port = port
        self.url = _endpoint_url(port)
        self.health = None
        self.session_id = None
        self.protocol_version = None
        self.initialize_result = None
        self._next_id = 0

    def connect(self, client_info):
        """Complete the handshake and return the server's ``initialize`` result unchanged.

        The protocol version is read from the health route rather than written here, so the
        CLI has no copy of it to keep in step with the plugin.
        """
        health = probe(self.port)
        if health is None:
            raise TransportError(
                "No Jutsu Unreal MCP server answered on %s. "
                "Start the Unreal editor with the plugin enabled, then retry." % _address(self.port)
            )
        if health.get("acceptingRequests") is False:
            raise TransportError(
                "The editor on %s is not accepting requests. It is starting up, compiling or "
                "shutting down; retry when the editor is idle." % _address(self.port)
            )
        self.health = health
        self.protocol_version = health.get("protocolVersion")
        if not self.protocol_version:
            raise TransportError(
                "The server on %s did not report a protocol version, so its session headers "
                "cannot be built. Update the plugin." % _address(self.port)
            )

        status, body = self._post(
            {
                "jsonrpc": "2.0",
                "id": self._allocate_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": self.protocol_version,
                    "capabilities": {},
                    "clientInfo": client_info,
                },
            },
            with_session=False,
            want_session_header=True,
        )
        message, session_id = body
        if status != 200 or "result" not in message:
            raise TransportError(
                "The server on %s refused the handshake: %s"
                % (_address(self.port), _summarize(message))
            )
        if not session_id:
            raise TransportError(
                "The server on %s accepted the handshake without returning a session id."
                % _address(self.port)
            )
        self.session_id = session_id
        self.initialize_result = message["result"]
        self.notify("notifications/initialized")
        return self.initialize_result

    def call(self, method, params=None):
        """Send one JSON-RPC request and return the parsed response message unchanged.

        Protocol errors from the plugin are returned, not raised: their ``code``, ``path`` and
        ``recovery`` belong to the caller, and rewording them here would make the CLI a second
        contract.
        """
        message = {"jsonrpc": "2.0", "id": self._allocate_id(), "method": method}
        if params is not None:
            message["params"] = params
        status, (response, _) = self._post(message)
        if status == 404:
            self.session_id = None
            raise SessionExpired(
                "The Jutsu Unreal MCP server on %s no longer knows this session. The editor was "
                "restarted; the CLI will open a new one." % _address(self.port)
            )
        if not isinstance(response, dict) or ("result" not in response and "error" not in response):
            raise TransportError(
                "The server on %s answered HTTP %d with a body that is not a JSON-RPC response."
                % (_address(self.port), status)
            )
        return response

    def notify(self, method, params=None):
        """Send one JSON-RPC notification. The server answers 202 with no body."""
        message = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            message["params"] = params
        self._post(message)

    def close(self):
        """Release the session so the server can drop its pagination snapshots."""
        if self.session_id is None:
            return
        request = urllib.request.Request(
            self.url,
            method="DELETE",
            headers={
                "MCP-Session-Id": self.session_id,
                "MCP-Protocol-Version": self.protocol_version,
            },
        )
        try:
            urllib.request.urlopen(request, timeout=_HEALTH_TIMEOUT_SECONDS).close()
        except (urllib.error.URLError, OSError):
            pass
        self.session_id = None

    def _allocate_id(self):
        self._next_id += 1
        return self._next_id

    def _post(self, message, with_session=True, want_session_header=False):
        # json.dumps preserves nested arrays exactly, which is the whole reason this transport
        # is written in Python: a document's connections are arrays of pairs, and a converter
        # that flattens them silently corrupts an authoring call.
        payload = json.dumps(message, ensure_ascii=False).encode("utf-8")
        headers = {"Accept": _ACCEPT, "Content-Type": "application/json"}
        if with_session:
            if self.session_id is None:
                raise TransportError("The CLI tried to call the server before completing the handshake.")
            headers["MCP-Session-Id"] = self.session_id
            headers["MCP-Protocol-Version"] = self.protocol_version
        request = urllib.request.Request(self.url, data=payload, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(request) as response:
                status = response.status
                raw = response.read()
                session_header = response.headers.get("MCP-Session-Id")
        except urllib.error.HTTPError as failure:
            status = failure.code
            raw = failure.read()
            session_header = failure.headers.get("MCP-Session-Id")
        except (urllib.error.URLError, OSError):
            raise TransportError(
                "Lost the connection to the Jutsu Unreal MCP server on %s. "
                "The editor was closed or crashed; restart it and retry." % _address(self.port)
            )

        if not raw:
            return status, (None, session_header)
        try:
            return status, (json.loads(raw.decode("utf-8")), session_header)
        except (UnicodeDecodeError, ValueError):
            raise TransportError(
                "The server on %s answered HTTP %d with a body that is not JSON."
                % (_address(self.port), status)
            )


def _summarize(message):
    if isinstance(message, dict):
        error = message.get("error")
        if isinstance(error, dict) and error.get("message"):
            return str(error["message"])
    return "no JSON-RPC result was returned"
