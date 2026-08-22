# Jutsu Unreal MCP

Jutsu Unreal MCP connects an MCP-capable coding agent to the Unreal Editor through a bounded, discovery-first interface. Instead of presenting an agent with hundreds of loosely documented commands, it gives the agent five stable tools to find the right Unreal operation, obtain its current contract, inspect state, make a change, and verify the result.

It is built for practical editor work: authoring and maintaining assets, Blueprints, worlds, gameplay systems, audio, animation, UI, procedural content, and more—while keeping each request structured, validated, and traceable.

## Requirements

| Requirement | Supported configuration |
| --- | --- |
| Unreal Engine | **5.8.0** |
| Platform | **Windows 64-bit Unreal Editor** |
| Plugin type | Editor-only Code Plugin; not available in commandlets or packaged games |
| MCP client | Streamable HTTP with MCP protocol `2025-11-25` |

Jutsu uses only UE-supplied plugin dependencies. No separate Python package, third-party server, or project plugin is required.

## Why discovery first

The live registry contains **490 capabilities**, exposed through only these five MCP tools:

| Tool | Purpose |
| --- | --- |
| `jutsu_recommend` | State a goal and get one routed capability with a ready next call, or a bounded ambiguous answer with alternatives. |
| `jutsu_capabilities_search` | Find concrete capabilities from a natural-language request; optionally narrow with canonical tags. |
| `jutsu_capabilities_describe` | Load exact compact invocation contracts. Takes an array of ids and answers them in one call; full metadata requires explicit detail. |
| `jutsu_inspect` | Read supported Unreal state. Takes an array of read requests and answers them all in one call. |
| `jutsu_execute` | Preflight and run up to 100 ordered changes in one call, with internal backward references; success is compact by default, with full result detail available explicitly. |

This architecture keeps the agent's initial context small and makes the current registry—not an outdated prompt—the source of truth. An agent can ask for “create a damage Gameplay Effect” or “inspect a PCG static-mesh spawner,” receive the relevant capability IDs, read their exact contracts on demand, then act with canonical Unreal identities and typed data.

Capability records report their expected lifecycle and effects: validation errors, prerequisites, mutation/dirty state, compile and save requirements, recovery routes, and structured readback. That supports deliberate batching, diagnostics, and persistence verification instead of blind retries or UI automation.

## Dedicated Unreal workflows and reflection fallback

The 490 count is the complete live registry; it is **not** a claim of unrestricted Unreal access. Dedicated native capabilities provide the supported authoring and inspection routes for systems including:

- Assets and project settings; levels, actors, components, World Partition, and streaming.
- Blueprints, interfaces, graphs, typed pins, variables, UMG, and localization.
- Materials, animation assets and Animation Blueprints, Control Rig, IK Rig, and Sequencer.
- Gameplay Ability System, Gameplay Tags, Enhanced Input, StateTree, Smart Objects, Gameplay Interactions, and EQS.
- Niagara, MetaSound and audio assets, PCG graphs/components, physics, and PIE/Functional Test validation.

When a dedicated route does not fit, Jutsu offers a **constrained reflection fallback**. It can search and inspect exact reflected types and members, then route eligible properties or functions through their documented policies. It does not create extra dedicated capability counts and does not expose arbitrary Python, console commands, C++, unrestricted `UFunction` calls, Editor selection lookup, or inferred targets.

Generic editor function calls are limited to public `BlueprintCallable` pure/const reads. Side-effect calls require an explicit active PIE target, current PIE session identity, and explicit confirmation; native or Blueprint `CallInEditor` actions use their separate bounded route. Inspect a reflected function before calling it—the returned policy is authoritative.

## Install and connect

1. Install **Jutsu Unreal MCP** through Fab/Launcher.
2. Open a UE 5.8 project. In **Edit > Plugins**, enable **Jutsu Unreal MCP** and restart the Editor when prompted.
3. Check the **Jutsu MCP** item in the Level Editor status bar. It should report **Running** and show the active port.
4. Add a Streamable HTTP MCP server in your coding agent/client using:

   ```text
   http://127.0.0.1:19782/mcp
   ```

The default port is `19782`. To change it, use **Edit > Editor Preferences > Plugins > Jutsu Unreal MCP**, then select **Restart** from the Jutsu MCP status-bar menu. The MCP client handles session initialization; it must negotiate protocol `2025-11-25`.

Jutsu listens on loopback only. It is designed for the same machine as the Unreal Editor—do not use a LAN address, port forwarding, reverse proxy, VPN, container bridge, or shared untrusted machine. The endpoint has no TLS or authentication because its trust boundary is the local process.

## Quick start

With the Editor running and the endpoint connected, give your agent a goal such as:

> Use Jutsu discovery first. In the current Unreal project, inspect the existing player Blueprint and add a health variable with the appropriate type and default value. Compile it, save it if the capability contract requires it, then inspect the result and report the canonical asset path and readback.

The expected flow is search → describe → inspect → execute → inspect. For a multi-step edit, the agent should use a batch only after the selected capability records say batching is supported. After a timeout, it should inspect the Editor state before retrying: operations run synchronously on the Unreal Game Thread and may have completed after the client deadline.

## Important boundaries

- Jutsu is an editor tool, not a runtime, viewport/UI-control, or general automation server. PIE automation does not support multiplayer or separate-process sessions.
- Destructive operations require explicit intent. Changes can dirty, compile, save, reload, import, rename, move, or delete project data; use source control or backups for consequential work.
- PIE validation is intentionally bounded to one native in-process standalone PIE session and exact placed Functional Test targets. Generic runtime calls reject RPC, latent, delegate, wildcard/custom-thunk, deprecated, internal, and unsupported signatures.
- No AI client is named as officially tested in this documentation. Use a client that meets the Streamable HTTP and protocol requirements above.

For detailed boundaries, see [Known limitations](Documentation/KNOWN_LIMITATIONS.md) and [network and security guidance](Documentation/NETWORK_AND_SECURITY.md).

## Troubleshooting

- **Server is stopped or reports an error:** Check the Jutsu MCP status-bar menu. If the port is occupied, choose an unused port in Editor Preferences and select **Restart**. A non-loopback bind is intentionally refused.
- **Client cannot initialize:** Use the exact active endpoint (`http://127.0.0.1:<port>/mcp`), Streamable HTTP, and MCP `2025-11-25`; do not substitute a hostname, LAN address, or proxy.
- **A request timed out or has an unknown outcome:** Do not repeat it immediately. Inspect the relevant asset/object and its compile, dirty, and save state first.

More help: [installation](Documentation/INSTALLATION.md), [MCP client configuration](Documentation/MCP_CLIENT_CONFIGURATION.md), [usage](Documentation/USAGE.md), [troubleshooting](Documentation/TROUBLESHOOTING.md), and [dependencies](Documentation/DEPENDENCIES.md).

## Support

For bugs, setup issues, and capability requests, open a [GitHub Issue](https://github.com/davbludev/JutsuUnrealMcpPublic/issues). Include your Unreal Engine version, the Jutsu status-bar state/active port, the capability ID or agent request, and the returned diagnostic where possible.

Jutsu Unreal MCP is an independent product and is not affiliated with, sponsored by, or endorsed by Epic Games.
