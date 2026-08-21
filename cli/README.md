# Jutsu Unreal MCP CLI

A second way for an agent to reach the Jutsu Unreal MCP plugin. The plugin serves MCP over
loopback HTTP from inside the Unreal editor; this CLI registers with an agent host as an ordinary
stdio MCP server and forwards everything to it.

The plugin is complete without this. Any MCP client that speaks HTTP can talk to it directly, and
that route is the one the Fab listing supports. The CLI is for hosts that prefer to launch a
child process, and for driving the plugin from a shell.

## What it needs

- An Unreal editor running, with the plugin enabled.
- Any Python 3 interpreter. The CLI uses only the standard library, so nothing is installed:
  no `pip`, no package manager, no third-party code.

If Python is not on `PATH`, the engine already ships one at
`Engine/Binaries/ThirdParty/Python3/<Platform>/python.exe` under your engine root (Python 3.11 on
UE 5.8). Use the absolute path to it in the configuration below. The CLI never looks for an
interpreter itself - by the time any of its code runs, one has already been chosen, and choosing
it is the launcher's job.

## Registering it with an agent host

Most hosts take a command and its arguments. The shape below is the one to adapt:

```json
{
  "mcpServers": {
    "jutsu-unreal": {
      "command": "python",
      "args": ["C:/path/to/JutsuUnrealMcpPublic/cli/jutsu_mcp_stdio.py", "--port", "19782"]
    }
  }
}
```

`19782` is the plugin's shipping default. Change it to match the editor you want, or drop
`--port` entirely and let the CLI work the port out.

## Which editor it talks to

The host is always `127.0.0.1`. The CLI opens no listening socket of its own and reaches nothing
else on the network.

The port is the first of these that answers:

1. `--port <N>`.
2. The `JUTSU_MCP_PORT` environment variable.
3. A `.jutsu-mcp.json` file in the working directory or any ancestor of it, holding
   `{"port": 19782}`.
4. Discovery: ports 19780 to 19789 are probed, and the one running the plugin is used.

**Two editors open at once is refused, not guessed.** Discovery names every candidate it found
and asks for `--port`, because picking one silently would let an agent author into the wrong
project. For the same reason a port that answers but is not this plugin is reported as occupied
rather than as an editor that is down.

## When the editor is not running

The CLI writes one line saying which port it tried and exits non-zero, before the host's
`initialize` is answered. There is no offline mode and no mocked tool list: an empty list would
tell the agent the server has no capabilities, which is false.

The practical consequence: start the editor first. A host that launches its MCP servers when a
session begins needs this one restarted after the editor comes up.

## Compatibility

There is no compatibility matrix, because there is nothing here to keep in step. The CLI declares
no tool names, no schemas, no descriptions, no error codes and no registry version. It asks the
live server for all of them at run time and forwards what it gets, so a plugin release that
changes a schema reaches your agent with no CLI update at all.

The rule is enforced rather than promised - see `tools/` below.

## Checks

```
python cli/tools/check_cli_vocabulary.py       # no editor needed
python cli/tools/check_cli_forwarding.py       # needs a running editor
python -m unittest discover -s cli/tests       # no editor needed
python cli/tests/check_live_transport.py       # needs a running editor
cd cli/tests/client-compatibility && npm ci && npm test   # needs a running editor and Node
```

`check_cli_vocabulary.py` refuses CLI source that carries a tool name, a capability id or an
Unreal object path. `check_cli_forwarding.py` is the stronger one: it harvests every tool name,
canonical tag, capability id and routing sentence from a running server and searches the package
for each, so the forbidden list is never something anyone maintains by hand.

`check_live_transport.py` compares the CLI against a raw HTTP client written from scratch, call
by call, including a document whose `connections` are arrays of pairs. The client-compatibility
test drives the CLI with the official MCP client and compares everything it sees - instructions,
tool list, successes and errors - against the same official client talking straight to the
plugin.

## What it changes about a response

One thing, and it was measured before it was written. A response stays JSON, because re-encoding
one into indented lines, flattened paths or Markdown costs **more** tokens than the JSON it
replaces - measured at 115% to 252% of it on 204 recorded responses with the `o200k_base`
tokenizer. Modern tokenizers pack JSON punctuation into single tokens, and these payloads are
already compact.

The exception is a JSON Schema document, and it is a large one. Three quarters of a schema's
tokens are structure rather than prose, so the CLI renders any schema inside a *result* as a
signature:

```
object
  target: string minLength=1  # Canonical Unreal object path returned by discovery...
  aspect?: "<one selector>"|"<another selector>"
  options?: object open       # Extra arguments forwarded to the selected aspect
```

(The selectors above are shown as placeholders on purpose - every real name in that output comes
from the live server, and none of them is written down here.)

Every type, bound, enum, branch count and description survives; what goes is the JSON around
them. A describe of one authoring capability with its domain selector measured **4,031 tokens
to 1,185** that way. A response carrying no schema is unchanged, and costs nothing.

The published tool list is never rendered - the host builds calls from those input schemas, so
they stay real JSON Schema documents. `--json` turns rendering off everywhere and forwards the
server's bodies untouched.

## Status

The transport core, the stdio front end and the schema renderer. Field projection and the
`jutsu <cmd>` shell front end are not built yet.
