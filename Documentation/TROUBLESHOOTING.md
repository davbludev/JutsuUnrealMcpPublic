# Troubleshooting

## Server does not start

Check the status-bar state and active/configured ports. If another process owns the configured port, choose an unused port in Editor Preferences and select **Restart**. A non-loopback bind is intentionally refused. Confirm the built-in dependencies are installed and enabled, then restart the Editor.

## MCP client cannot initialize

Use `http://127.0.0.1:<active-port>/mcp`, request protocol `2025-11-25`, omit `MCP-Session-Id` on `initialize`, then retain the returned session header. Send `notifications/initialized` before tool calls. Use JSON content type and an accepted JSON/SSE response type. Do not add a LAN hostname or proxy.

## Timeout or unknown result

Do not blindly retry. Inspect the relevant asset, object, package, compile state, and dirty/save state through MCP or the Editor. The client deadline does not preempt an already-running synchronous GameThread operation.

## Continuation fails or response is incomplete

Follow `structuredContent.page.continuation` exactly and keep the same MCP session. Do not change arguments, byte budget, record limit, or text mode while using a cursor. `cursor_stale` means the snapshot expired, was evicted, or relevant Unreal state changed; repeat the original inspection. `cursor_mismatch` means the session or request identity changed. `invalid_cursor` means the cursor is absent or unknown. For `response_budget_too_small`, repeat the original request without that cursor and request a larger byte budget. See [Bounded responses and continuation](BOUNDED_RESPONSES.md).

## Capability or dependency error

Follow the diagnostic's targeted `jutsu_capabilities_search` recovery and retry with an exact returned ID; an unknown capability does not require loading the catalog. Use bounded `expected`, `actual`, `schema`, `retryable`, recovery, related-capability, and mutation/dirty/save side-effect fields when present. Check the dependency table, including the optional Audio Modulation plugin and the Experimental/Beta UE plugins. Unsupported arbitrary execution paths are intentional.

## Compile, save, import, or reload failure

Read the structured diagnostic and Editor log. Resolve the reported prerequisite or dirty/conflict state, then inspect again. Use explicit compile/save/reload operations only where the capability contract permits them. Keep source control or a backup before destructive recovery.

## Support

Use the monitored support destination published in the Fab listing. The publisher must add the durable public support URL to release metadata before submission.
