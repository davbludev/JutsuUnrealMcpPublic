# Troubleshooting

## Server does not start

Check the status-bar state and the active and configured ports. If another process owns the configured port, choose an unused port in Editor Preferences and select **Restart**. A non-loopback bind is intentionally refused. Confirm the built-in dependencies in [Dependencies](DEPENDENCIES.md) are enabled, then restart the Editor.

## Client cannot connect

Use `http://127.0.0.1:<active-port>/mcp` as a Streamable HTTP server. Do not use a LAN hostname or proxy. `GET http://127.0.0.1:<active-port>/mcp/health` shows whether the server is accepting requests. After an Editor restart no reconnect is needed: the endpoint keeps no session.

## `run_python` fails to start

The Python Editor Script Plugin must be enabled. Check **Edit > Plugins > Python Editor Script Plugin** and restart the Editor.

## A call fails

Read the error text: it names the argument at fault and lists the valid choices. `get_log` returns recent Output Log lines, where compiler, save and import errors appear.

## Timeout

A client timeout does not stop an operation that is already running on the game thread; it may still complete. Read the affected asset or actor before retrying.

## Compile, save or import failure

`compile_assets` and `write_asset` report compiler messages; `get_log` shows save and import errors. Resolve the reported cause, then read the asset again. Keep source control or a backup before destructive recovery.

## Support

Open a [GitHub Issue](https://github.com/davbludev/JutsuUnrealMcpPublic/issues) with your Unreal Engine version, the status-bar state and port, the tool call, and the reply.
