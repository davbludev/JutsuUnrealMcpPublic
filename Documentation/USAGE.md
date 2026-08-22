# Usage

Jutsu Unreal MCP is designed for an agent to navigate Unreal state with bounded, composable calls.

## Recommended sequence

1. Search natural language with `jutsu_capabilities_search` mode `search`, optionally narrowing candidates with OR-composed catalog tags.
2. Pass the returned exact capability IDs to `jutsu_capabilities_describe` in one call; `requests` is an array, so describe everything the plan needs at once. The default compact invocation contract contains only fields needed for the next call.
3. Satisfy documented prerequisites and use canonical asset, object, graph, node, pin, class, or GUID identities.
4. Inspect the current state and record the returned identity/readback. A successful result is authoritative: do not read it back a second time to confirm it.
5. Apply changes with `jutsu_execute`. `steps` is an array, so send every mutation you already know you need in one call. A single step needs no `stepId` and no batch policy; `compile`, `save`, `transaction`, and `$ref` backward references need capability metadata that says batching and transaction policy are supported.
6. Compile, save, or reload only when the capability contract requests it; mutations remain dirty unless explicitly persisted.
7. A successful `jutsu_execute` means every step applied exactly as sent, so do not inspect to verify it. Inspect afterwards only after a client timeout, a compile diagnostic, or when a later step contradicts what you were told.

## Public tools

- `jutsu_capabilities_search`: grouped tag catalog or deterministic natural-language ranking that returns concrete `{id, version, title, kind}` summaries.
- `jutsu_capabilities_describe`: exact compact invocation contracts. `requests` is always an array, even for one id; use `detail: "full"` only for debugging or documentation. Successes land in `results[]` and failures in `failures[]`, addressed by request index.
- `jutsu_inspect`: invoke read-only capabilities. `requests` is always an array, even for a single object; batch every read you already know you need into one call. Successes land in `results[]` and failures in `failures[]`, both addressed by request index, so one bad request never discards the others.
- `jutsu_execute`: preflight and apply up to 100 ordered mutating steps. `steps` is always an array, even for one change. `stepId` is optional and defaults to `step<index>`; name a step explicitly only when a later step references its result with `{"$ref":"earlierStep#/result/field"}`.

The capability registry covers supported asset lifecycle, Blueprint, world, material, animation, audio, Niagara, PCG, PIE, UMG, StateTree, Gameplay Ability, input, physics, localization, and related editor domains. Unsupported or unsafe paths return a diagnostic rather than executing arbitrary Python, console, C++, or unrestricted CallInEditor work.

Every fixed tool shares the root `page` continuation contract. Follow the exact returned `page.continuation` route until `page.complete` is true; large execute results continue through `jutsu_inspect` without repeating the mutation. See [Bounded responses and continuation](BOUNDED_RESPONSES.md) for byte budgets, semantic pages, cursor lifetime, text compatibility, and error recovery.

`jutsu_capabilities_search` has only `catalog` and `search` modes. To retrieve exact contracts, call `jutsu_capabilities_describe` with `requests: [{ "id": "capability.id" }]`; domain-wide describe requests are still rejected.

## Reflection fallback

Prefer specialized native capabilities. When no domain capability fits, use `core.reflect.type.search` to page loaded native types and unloaded Blueprint/User Defined type records without loading search results. Reuse one returned canonical identity with `core.reflect.query`; exact inspection may load that selected type. The query preserves legacy `{class, kind}` member searches and also accepts exact class, struct, enum, or member identities with paged properties, functions, and enum values.

Properties route to `core.property.describe/get/set`. Eligible functions route to `core.function.invoke`; native or Blueprint `CallInEditor` actions route only to `core.call_in_editor.invoke`. Generic editor invocation is read-only and limited to public `BlueprintCallable` pure/const functions. Every PIE target must include the current `sessionSerial` from `pie.session.inspect`, preventing paths/GUIDs from rebinding after PIE restart. Side-effect invocation also requires `allowSideEffects: true`; static Blueprint Function Library side effects require the declared `WorldContext` input to equal the exact PIE world. Calls never infer targets or context, compile, save, open a transaction, create undo state, retry, or use Editor selection.

Function parameters use named canonical typed values. Supported shapes include bool, lossless integer, float/double, enum/bitflag, string/name/text, reflected struct, object/class/interface and soft references, array/set/map, and optional. Inspect the function first for parameter direction, defaults, supported shape, return type, policy, rejection reason, and route. A post-invocation error reports both `sideEffects.mutationMayHaveOccurred: true` and `sideEffects.possiblePartialMutation: true`; inspect live state before retrying.

## Side effects

Depending on the capability, calls can create, modify, compile, save, import, reimport, rename, move, or delete project assets and configuration data. Destructive operations require explicit destructive intent. Use source control or backups and read back the canonical result after every consequential operation.

## PIE verification loop

Use `pie.session.inspect` before starting. `pie.session.start` requests one native in-process standalone PIE session and returns pollable lifecycle state. Inspect exact PIE world contexts, run or poll one exact placed Functional Test when needed, and use `pie.diagnostics.inspect` for bounded runtime/editor log diagnostics. Always call `pie.session.stop` and wait for `idle` before resuming editor-world authoring. A failed verification can then be fixed and retried without UI automation.

## PCG authoring loop

Search or create a PCG graph, inspect its bounded topology, discover a concrete loaded settings class, add/configure nodes, set typed settings properties, and connect compatible native pins. For a weighted Static Mesh Spawner, use `pcg.static_mesh_spawner.inspect` and `pcg.static_mesh_spawner.entries.edit`; these accept practical mesh/weight/descriptor overrides and do not require serializing Unreal's internal descriptor hierarchy. Configure an exact editor-world PCG component using a component name or canonical path returned by `actor.inspect`, request generation or refresh, and poll component state. Treat `semanticOutcome`, `managedInstanceCount`, and semantic diagnostics as verification; generated point data alone does not prove that mesh resources exist. Save the graph and level through the normal asset/world save capabilities, then reload and regenerate when persistence matters. Cleanup and cancel operations remain explicit.
