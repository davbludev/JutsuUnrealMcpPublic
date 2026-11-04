# Scripting the Editor with run_python

Delete assets with `delete_assets`: `EditorAssetLibrary.delete_asset` on an asset a global still
holds can crash the Editor. Switch levels with `open_level`, not Python or a console `open`: a
global holding the old level leaves its package behind, which crashes the Editor.
Right after a level opens, the editor world's navigation build stays locked until loading settles
(at least 2 s, no assets still compiling): a `RebuildNavigation` then logs `navigation build is
locked (flags: 0x20)`. `wait` a few seconds and run it again, or query paths in PIE.
A headless `UnrealEditor-Cmd` run of the same project serves the MCP port too; `get_editor_state`
`pid` tells which process answered.

Scripting through `run_python`:
- Each call runs inside one editor frame. To sample over time, register
  `unreal.register_slate_post_tick_callback`, `wait`, then unregister and read the samples.
- Python spawns and edits in the editor world, and its handles to PIE objects die with each PIE
  session: spawn into PIE with `spawn_actor` `world: "pie"`, and fetch PIE objects again after every
  `start_pie`.
- Multiplayer PIE: `start_pie` with `netMode` `listen` (the first player hosts) or `client` (a hidden dedicated server) and
  `players` runs every player in the editor process and lists them as `pie:0`, `pie:1`, ... (`pie:<n>` is the `UEDPIE_<n>_` of
  that player's object paths; `pie` means the one in the level viewport). Pass `world: "pie:<n>"` to `get_properties`,
  `set_properties`, `call_function`, `list_actors`, `run_console_command`, `send_input` and `take_screenshot` to act in
  that player's game: set a replicated property on the server's actor (`pie:0`), `wait` a second or two, then read it on a
  client's with that client's `world`. Find an actor in each world by `list_actors` `class`, since a replicated actor's name
  can differ between worlds. Place fixtures in the level before `start_pie`. Drive a client with `send_input` and its
  `world` (a key or an Enhanced Input action), not by calling its gameplay functions from `run_python`. Log lines carry
  `pie:<n>` while several instances run.
- Stop PIE before a script creates, duplicates or deletes assets: the editor refuses them in play
  mode while the script carries on.
- A struct or array from `get_editor_property` is a live view; build a new value and set it (or call
  the class's setter), so the object hears the change.
- `set_properties` writes `EditDefaultsOnly` properties that `set_editor_property` refuses on
  instances.
- On UE 5.8 with the experimental Toolset Registry plugin enabled, Epic's editor toolsets are
  scriptable too: list them with
  `unreal.ToolsetRegistry.get_all_toolset_json_schemas()`, run one with
  `unreal.ToolsetRegistry.execute_tool`.

A primary data asset copied in Python shares its source's Primary Asset Id and the Asset Manager hands the
id to the copy (engine behaviour): change the copy's id property at once; restart the editor if the
source has dropped out of `get_primary_asset_id_list`.
Pass `uv0` with one entry per vertex on every GeometryScript `append_buffers_to_mesh` call; a
mesh saved without UVs by `create_new_static_mesh_asset_from_mesh` crashes the Editor.
