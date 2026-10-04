# MCP client configuration

## Endpoint

```text
http://127.0.0.1:19782/mcp
```

If the port was changed in Editor Preferences, use the configured port after selecting **Restart**. The status-bar menu shows the active port. Do not configure a hostname, LAN address, forwarded port, reverse proxy, or container address.

## Protocol

- Streamable HTTP, JSON-RPC 2.0, `POST` with `Content-Type: application/json`. Responses are JSON.
- Stateless: no `MCP-Session-Id` is issued or required, and any `MCP-Protocol-Version` header is accepted, so a client keeps working across an Editor restart. `initialize` answers the requested protocol version when it is `2025-11-25`, `2025-06-18` or `2025-03-26`, otherwise `2025-11-25`.
- `DELETE` is accepted and does nothing; `GET` (a server event stream) is not offered and returns 405.
- `tools/list` returns every tool with its input schema and does not change while the Editor runs (`listChanged: false`).
- `GET /mcp/health` reports the plugin and protocol versions, the endpoint, whether requests are accepted, and the tool count.

Example for a client configured by JSON:

```json
{
  "mcpServers": {
    "unreal": { "type": "http", "url": "http://127.0.0.1:19782/mcp" }
  }
}
```

## Results

A tool answers with text content (JSON for structured data) and, for `take_screenshot`, a PNG image. A failure is a tool result with `isError: true` and text that names the bad argument and the valid choices. Resources and prompts are not used.
