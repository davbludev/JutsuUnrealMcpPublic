# MCP client configuration

## Endpoint

The default Streamable HTTP endpoint is:

```text
http://127.0.0.1:19782/mcp
```

If the port was changed in Editor Preferences, use the configured port after selecting **Restart**. The status-bar menu shows the active port. Do not configure a hostname, LAN address, forwarded port, reverse proxy, or container address.

## Protocol and lifecycle

The current implementation negotiates MCP protocol version `2025-11-25`.

1. Send `initialize` without `MCP-Session-Id` and request `2025-11-25`.
2. Retain the returned `MCP-Session-Id`.
3. Send `notifications/initialized` with the session and protocol headers.
4. Use the five public tools: `jutsu_recommend`, `jutsu_capabilities_search`, `jutsu_capabilities_describe`, `jutsu_inspect`, and `jutsu_execute`.
5. Delete the session when finished.

The client must send JSON with `Content-Type: application/json` and accept JSON or `text/event-stream`. Requests larger than 4 MiB are rejected.

## Discovery-first workflow

Use `jutsu_capabilities_search` in `search` mode with a natural-language `query` as the normal discovery path, optionally narrowing candidates with OR-composed tags. Use `catalog` mode only when canonical tags themselves are unknown. Search returns ordered concrete capability summaries without implementation scores. Pass one selected exact `id` to `jutsu_capabilities_describe`; omitted `detail` defaults to the compact invocation contract. Request `detail: "full"` only for debugging or documentation. Inspect authoritative Unreal identities before mutation. For a timeout, inspect the Editor state before retrying; a synchronous GameThread operation may have completed after the client deadline.

Registry contract 3.0 adds one shared bounded-response layer while retaining exactly five public tools. All five input schemas accept optional root `page` controls, and all five output schemas expose optional root `page` completeness metadata. Clients should treat `structuredContent` as authoritative, follow the exact returned continuation route, and support compact non-JSON `content` text for large results. See [Bounded responses and continuation](BOUNDED_RESPONSES.md).

Search contract 2.0 migration:

- Replace `jutsu_capabilities_search {"mode":"invoke","id":"..."}` with `jutsu_capabilities_describe {"id":"..."}`.
- Consume the required `mode` discriminator in catalog/search results.
- Replace domain/score query handling with ordered `{id, version, title, kind}` summaries.
- Discard cached registry metadata and cursors from earlier registry versions.

Named client examples and verified client versions must be added to this document before the Fab listing advertises them. Do not infer compatibility from an untested client.
