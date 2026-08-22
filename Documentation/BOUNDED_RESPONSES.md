# Bounded responses and continuation

Jutsu Unreal MCP bounds every `tools/call` result. The default maximum is 65,536 serialized UTF-8 bytes and the default soft page target is 50 records. The byte ceiling is authoritative: a page may contain fewer records when the complete MCP call result would otherwise exceed its budget.

The measured value is the complete call-result object, including `content`, `structuredContent`, `isError` when present, domain data, pagination metadata, and the compatibility text. It is not only the size of the selected capability's domain result.

## Initial request

All six public tools accept the same optional root `page` object. This does not add another MCP tool.

```json
{
  "id": "core.authoring.apply",
  "detail": "full",
  "page": {
    "budgetBytes": 16384,
    "textMode": "summary"
  }
}
```

- `budgetBytes` requests a final call-result ceiling between 1,024 bytes and the configured server maximum.
- `limit` is a soft record target from 1 to 1,000.
- `textMode` is `auto`, `summary`, or `mirror`.

Omitting `page` uses server defaults. The server still pages an otherwise oversized result.

## Page response and continuation

Completeness data always lives under root `structuredContent.page`; it never shares names with domain fields inside `structuredContent.result`. Every successful result carries it, including one that fits in a single page: that page reports `section: "result"` with an empty `sectionPath`, `complete: true`, and no continuation. `page.registryVersion` is the capability registry version of the running plugin build, on every page. Compare it before concluding that a documented capability, field, or error route does not exist - an older version means the installed build predates the contract you are reading. `core.registry.inspect` remains the full report.

```json
{
  "capability": {},
  "page": {
    "section": "capability",
    "sectionPath": "/capability",
    "complete": false,
    "returned": 4,
    "budgetBytes": 16384,
    "sections": [],
    "remainingSections": ["capability"],
    "nextCursor": "1042",
    "continuation": {
      "tool": "jutsu_capabilities_describe",
      "arguments": { "page": { "cursor": "1042" } }
    }
  }
}
```

Follow `page.continuation.tool` and `page.continuation.arguments` exactly. Cursors are opaque process-scoped nonzero `uint64` identities serialized as canonical decimal JSON strings; they are never JSON numbers. Do not construct, increment, decode, persist across Editor restarts, or combine a cursor with changed arguments. Clients must use `complete`, `sections`, and `remainingSections`; `total` and `totalPages` are optional and may be absent when expensive or incompatible with byte-budget pagination.

Cursors bind the MCP session, fixed tool, capability, normalized original arguments, asset/object/view/section identity, registry and response-contract versions, relevant Unreal state, and immutable snapshot. Their default TTL is a sliding 15 minutes, refreshed after every successful continuation. A cursor becomes unusable when its session ends, its snapshot expires or is evicted, or relevant live Unreal state changes.

Errors have actionable codes:

- `invalid_cursor`: cursor is missing, malformed, overflowed, zero/reserved, or unknown. Follow an exact returned route or repeat the original request.
- `cursor_mismatch`: session, request identity, page controls, or detail selector differs. Use the exact route; repeat the original request when controls must change.
- `cursor_stale`: snapshot expired, was evicted, or its bound Unreal state changed. Repeat the original inspection for current authoritative state.
- `response_budget_too_small`: metadata cannot fit. Repeat the original request without the cursor and raise `page.budgetBytes` within the server maximum.
- `snapshot_too_large` or `snapshot_storage_failed`: narrow the semantic request or free local storage before retrying.

## Semantic and oversized records

Flat collections use generic source-order paging. Composite graphs, hierarchies, trees, stacks, and similar responses use semantic section plans so nodes remain coherent with their relevant pins/properties and stable references remain usable across pages. `page.sections` lists the section catalog only when a result has more than one section; with a single section, `page.section`, `page.sectionPath`, and `page.total` already describe it.

When one coherent record cannot fit, it is reported rather than returned, and the records behind it are still returned on the same page: `page.returned` counts them, and `page.oversizedRecord` describes the one that was skipped - `identity` names it (a capability id for a describe, a target for an inspect), `serializedBytes` measures it, and `detailRoute` is an exact route into it on the same tool that produced the page.

Follow `detailRoute` to receive bounded JSON-Pointer field pages, then reconstruct that one record before merging it into its named section. This avoids splitting arbitrary UTF-8 bytes or requiring one giant in-memory JSON string. That first detail call accepts an added `page.limit` (up to 1000) and `page.budgetBytes`: they describe the new field-paged snapshot rather than the page you came from, so they do not answer `cursor_mismatch`. Setting them matters - a 2,660-field record walks in 3 calls at `limit: 1000` and 54 at the default 50.

`page.budgetBytes` cannot raise the server's own ceiling (**Maximum Call Result Bytes**, 64 KB by default). The oversized-record message states that ceiling, so a record larger than it needs the detail route, not a larger budget.

## Batched inspection

`jutsu_inspect` answers an array of read requests in one call. Its pageable sections are `results` and `failures`, and one record is one whole per-request answer, so a record stays coherent with the request it belongs to. A per-request failure is reported in `failures[]` and never fails the call or the sibling requests; only a malformed request array, an unusable cursor, or a budget failure produces a tool error. When a single request's answer cannot fit one page, it surfaces through `page.oversizedRecord.detailRoute` below - prefer the capability's own `offset`/`limit` arguments when it declares them.

## Mutation results

`jutsu_execute` returns `{ "success": true }` after every step succeeds. Errors retain bounded actionable diagnostics and identify only the failed step. Use top-level `response: { "detail": "full" }` only when returned mutation values are required. Full results retain immutable pagination through `jutsu_inspect`; following a continuation never executes mutation again. Backward references always resolve against internal step results, including compact mode.

## `structuredContent` and text compatibility

Treat `structuredContent` as authoritative. `content[0].text` carries a compact non-JSON summary and does not duplicate the payload: **Text Mirror Threshold Bytes** defaults to `0`. Raise it if a client cannot consume `structuredContent`, and every result at or below that size is sent twice. `textMode: "mirror"` requests an exact JSON mirror for one call, error responses included; the byte budget then includes both copies and may reduce records per page.

## Limits, storage, and pressure

Response settings are under **Editor Preferences > Jutsu Unreal MCP > Responses**:

- maximum call result: 64 KiB;
- soft default records: 50;
- sliding cursor TTL: 900 seconds;
- cache: 32 snapshots and 32 MiB in memory;
- individual in-memory snapshot threshold: 64 MiB;
- aggregate temporary snapshot storage: 256 MiB;
- automatic text mirror threshold: 8 KiB.

Snapshots above the individual memory threshold spill to bounded plugin-owned files under the project `Saved/JutsuUnrealMcp/Continuation` directory. LRU eviction enforces count, memory, and temporary-storage limits. Session deletion and normal shutdown remove owned snapshots; startup removes orphaned `snapshot-*.json` files left by an interrupted Editor. `core.registry.inspect.responseCache` reports active usage, spills, evictions, pressure errors, oversized-record routes, and orphan cleanup so large real assets can be monitored before raising limits.

Command-line overrides use the corresponding `-JutsuMcpMaxCallResultBytes=`, `-JutsuMcpDefaultPageRecords=`, `-JutsuMcpCursorTtlSeconds=`, `-JutsuMcpMaxResponseSnapshots=`, `-JutsuMcpMaxSnapshotMemoryBytes=`, `-JutsuMcpMaxIndividualSnapshotBytes=`, `-JutsuMcpMaxTemporarySnapshotBytes=`, and `-JutsuMcpTextMirrorThresholdBytes=` arguments. They affect only that Editor process.
