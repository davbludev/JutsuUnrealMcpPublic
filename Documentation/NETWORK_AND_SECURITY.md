# Network and security

## Local endpoint

The server uses Unreal's shared HTTP server and binds only to loopback (`127.0.0.1`, `localhost`, or `::1`). Browser `Origin` values must also be loopback or absent. A non-loopback configured bind is refused. The plugin has no outbound network client of its own.

The default URL is `http://127.0.0.1:19782/mcp`. There is no TLS and no authentication: any local process that can reach the port can call every tool, including `run_python` and `run_console_command`, which run arbitrary code and commands with the Editor's privileges. This is a local-process trust boundary. Do not expose the endpoint through port forwarding, a reverse proxy, a VPN, a container bridge, or a shared untrusted machine.

## Request handling

- Request bodies larger than 4 MiB are rejected.
- The transport is stateless: no session is created or required.
- Unknown arguments are refused before anything changes.

## Data and editor effects

Tools can read local files given to `import_assets`, write project assets and configuration, and create, modify, compile, save, rename, move, or delete project data. Asset edits are saved as they are made. Keep source control and backups available. After a client timeout, check Editor state before retrying: an operation running on the game thread is not stopped by client cancellation.

Stop or disable the server when it is not needed.
