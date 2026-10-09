# Jutsu Unreal MCP

Jutsu Unreal MCP is an Unreal Editor plugin that serves an MCP endpoint to a coding agent on the
same machine. The agent reads and edits assets as text, sets properties, calls functions, runs
Python and console commands, places actors, and plays and captures PIE.

## Requirements

| Requirement | Supported configuration |
| --- | --- |
| Plugin version | **5.1.0** |
| Unreal Engine | **5.5, 5.6, 5.7, 5.8** (a separate package per version) |
| Platform | **Windows 64-bit Unreal Editor** |
| Plugin type | Editor-only Code Plugin; not loaded in commandlets or packaged games |
| MCP client | Streamable HTTP |

The plugin enables UE-supplied plugins only, including the **Python Editor Script Plugin** and
**Editor Scripting Utilities**. No separate Python install, server or project plugin is needed.

## Tools

Every tool is listed in `tools/list` with a one-sentence description and a described parameter
for every argument. There is no discovery step and no session.

| Group | Tools |
| --- | --- |
| Editor | `get_editor_state`, `get_log`, `run_console_command`, `run_python`, `live_coding_compile` |
| Assets | `find_assets`, `create_asset`, `duplicate_asset`, `rename_asset`, `delete_assets`, `save_assets`, `import_assets`, `get_asset_references`, `compile_assets` |
| Assets as text | `read_asset`, `edit_asset`, `write_asset` |
| Objects | `get_properties`, `set_properties`, `call_function`, `describe_class` |
| Level | `open_level`, `list_actors`, `spawn_actor`, `delete_actors`, `set_actor_transform` |
| Play | `start_pie`, `stop_pie`, `send_input`, `wait`, `take_screenshot` |

Objects are named by the path or name the agent already has: `/Game/UI/WBP_HUD`,
`Content/UI/WBP_HUD.uasset`, `WBP_HUD`, an actor label such as `Door 2`, a class such as
`StaticMeshActor`. Values are plain JSON; Unreal text such as `(X=1,Y=2,Z=3)` is also accepted.
Asset edits are saved; level edits stay unsaved until `save_assets`. See [Usage](Documentation/USAGE.md).

## Install and connect

1. Install **Jutsu Unreal MCP** through Fab/Launcher for your engine version.
2. In **Edit > Plugins**, enable **Jutsu Unreal MCP** and restart the Editor.
3. The **Jutsu MCP** item in the Level Editor status bar shows **Running** and the active port.
4. Add a Streamable HTTP MCP server in your client:

   ```text
   http://127.0.0.1:19782/mcp
   ```

To change the port, use **Edit > Editor Preferences > Plugins > Jutsu Unreal MCP**, then **Restart**
from the status-bar menu. See [MCP client configuration](Documentation/MCP_CLIENT_CONFIGURATION.md).

## Security

The endpoint listens on loopback only, with no TLS and no authentication. Any process on the
machine that can reach the port can run Python and console commands in the editor. Do not expose
it through port forwarding, a proxy, a VPN or a container bridge. See
[network and security](Documentation/NETWORK_AND_SECURITY.md).

## More

[Installation](Documentation/INSTALLATION.md) · [Usage](Documentation/USAGE.md) ·
[Troubleshooting](Documentation/TROUBLESHOOTING.md) · [Known limitations](Documentation/KNOWN_LIMITATIONS.md) ·
[Dependencies](Documentation/DEPENDENCIES.md) ·
[Agent skill for the asset-text formats](using-jutsu-unreal-mcp/SKILL.md)

## Support

Open a [GitHub Issue](https://github.com/davbludev/JutsuUnrealMcpPublic/issues) with your Unreal
Engine version, the status-bar state and port, the tool call, and the reply.

Jutsu Unreal MCP is an independent product and is not affiliated with, sponsored by, or endorsed by
Epic Games.
