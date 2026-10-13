# Scripting the Editor with run_python

`run_python` globals outlive the call: set every UObject they hold to `None` before deleting or
moving its asset (or delete with `delete_assets`), or `EditorAssetLibrary.delete_asset` can crash
the Editor. Switch levels with `open_level`, not Python or a console `open`: it sets the globals
holding the old level to `None`, whose leftover package would otherwise crash the Editor.
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
- Stop PIE before a script creates, duplicates or deletes assets: the editor refuses them in play
  mode while the script carries on.
- A struct or array from `get_editor_property` is a live view; build a new value and set it (or call
  the class's setter), so the object hears the change.
- `set_properties` writes `EditDefaultsOnly` properties that `set_editor_property` refuses on
  instances.
- On UE 5.8 with the experimental Toolset Registry plugin enabled, Epic's editor toolsets reach
  further (Niagara stack modules and inputs, for one): list them with
  `unreal.ToolsetRegistry.get_all_toolset_json_schemas()`, run one with
  `unreal.ToolsetRegistry.execute_tool`.

A duplicated primary data asset shares its source's Primary Asset Id and the Asset Manager hands the
id to the copy (engine behaviour): change the copy's id property at once; restart the editor if the
source has dropped out of `get_primary_asset_id_list`.
Pass `uv0` with one entry per vertex on every GeometryScript `append_buffers_to_mesh` call; a
mesh saved without UVs by `create_new_static_mesh_asset_from_mesh` crashes the Editor.
