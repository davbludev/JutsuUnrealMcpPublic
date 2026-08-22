# Known limitations

These are current buyer-relevant boundaries, not hidden feature promises.

- PIE automation intentionally uses one native in-process standalone client. Multiplayer, separate-process sessions, viewport/UI control, and automatic dirty/out-of-date Blueprint compilation are not exposed.
- Functional Test control targets one exact placed test actor in one exact PIE world. Broad test discovery/runs are excluded. Generic runtime function invocation is limited to public synchronous `BlueprintCallable` calls on an explicit active PIE target; RPC, latent, delegate, wildcard/custom-thunk, deprecated, internal, stale, and unsupported signatures are rejected.
- PIE diagnostics retain a bounded in-memory log window. They are not a replacement for the complete Editor log.
- PCG authoring operates on exact editor assets/components and loaded concrete `UPCGSettings` classes. Bespoke PCG editor widgets, runtime PIE component mutation, and arbitrary private PCG internals are excluded.
- Generic Blueprint State Machine lifecycle is intentionally rejected. Use the dedicated Animation Blueprint state-machine/state/transition capabilities.
- Standalone Niagara emitter assets are create/inspect-only. Author emitter modules and parameters through a system-owned emitter handle.
- Client cancellation cannot preempt a synchronous GameThread operation. After a timeout, inspect authoritative state before retrying.
- MetaSound builder handles are transient to the Editor session. Save the built asset and reopen it with a new handle after release or restart.
- Some package-only asset reference records do not compose directly to asset inspection; resolve a canonical asset identity first.
- Reflection type search covers loaded native types plus Asset Registry Blueprint-generated classes, User Defined Structs, and User Defined Enums. It does not scan unloaded native modules, infer short ambiguous identities, or eagerly load search results.
- `core.function.invoke` never injects World Context, Default To Self, or Auto Create Ref Term values and never saves, compiles, opens a transaction, supplies undo, retries, or performs selection lookup. Generic editor mutation remains property-based or native CallInEditor.
- PIE function targets expire when the PIE session serial changes. Refresh `pie.session.inspect` and rebuild the target after every restart; stale or missing serials are rejected before invocation.

The repository’s internal `Limitations/` register contains reproduction evidence and may include development paths that are intentionally excluded from buyer documentation.
