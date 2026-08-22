# Network and security

## Local endpoint

The server uses Unreal’s shared HTTP server and binds only to loopback (`127.0.0.1`, `localhost`, or `::1`). Browser `Origin` values must also be loopback or absent. A non-loopback configured bind is refused. The endpoint is not a public internet service and the plugin has no product-owned outbound network client.

The default URL is `http://127.0.0.1:19782/mcp`. There is no TLS and no authentication. A native local process that can reach the port may initialize a session when it sends a valid request; this is a local-process trust boundary, not remote-user authorization. Do not expose the endpoint through port forwarding, a reverse proxy, a VPN, a container bridge, or a shared untrusted machine.

## Request and session protections

- Request bodies larger than 4 MiB are rejected.
- MCP protocol and session headers are validated.
- Sessions are created by `initialize` and should be deleted when finished.
- JSON schemas, capability prerequisites, and exact identities are validated before mutation.
- Destructive intent is required for guarded delete/remove operations.
- Arbitrary Python, console, C++, and unrestricted reflected invocation are not exposed. Generic reflection requires exact identities and strict typed parameters; every PIE identity is bound to the current `sessionSerial`, editor calls are pure/const only, and mutations require an explicit active PIE target and confirmation.

## Data and editor effects

User-authorized capabilities can read supplied local import/reimport paths, write project and Editor configuration, launch supported Unreal commandlet work, and mutate or persist project assets. Calls may dirty, compile, save, reload, import, reimport, rename, move, or delete data. Keep source control and backups available. After any client timeout, inspect authoritative Editor state before retrying because a synchronous GameThread operation is not preempted by client cancellation.

Stop or disable the server when it is not needed. Review the exact capability metadata and returned readback before accepting an operation with consequential project effects.
