# Jutsu Unreal MCP Lite

Lite is the free edition: same endpoint, port and tool names as the full edition. A Lite server says so in
`get_editor_state` (`"edition": "lite"`; the full edition has no `edition` field), in its `initialize`
instructions, and in the status bar ("Jutsu MCP Lite").

## What Lite writes

- Blueprints whose class is exactly Blueprint: actor, component, object, function library and interface
  Blueprints, every section they have (`Variables`, `Components`, `Defaults`, graphs, ...).
- User-defined structs (`Fields`) and enums (`Entries`).
- For each of these assets: `create_asset`, `duplicate_asset`, `rename_asset`, `delete_assets`, `write_asset`,
  `edit_asset`, `set_properties`, `compile_assets`, `save_assets`.
- Actors of the open level and their components: `spawn_actor`, `delete_actors`, `set_actor_transform`,
  `set_properties`. Saving them and the level (`save_assets`, `open_level`).
- PIE: `start_pie`, `stop_pie`, `send_input`, `wait`, `take_screenshot`.

Existing assets of any kind can be referenced from what Lite writes: a mesh or material on a Blueprint component, a
widget a Blueprint creates, a sound played by a node.

## What Lite only reads

Everything else: `read_asset` of every section, `get_properties`, `find_assets`, `find_in_blueprints`,
`get_asset_references`, `describe_class`, `list_actors`, `get_log`. A write to any other asset is refused:
Widget Blueprints, materials (Material Functions, Instances, Layers, Parameter Collections), Animation, Control Rig,
Editor Utility and Gameplay Ability Blueprints, Editor Utility Widgets, the level Blueprint, Niagara, AI (Behavior Tree, Blackboard, StateTree), GAS assets, audio, Level Sequences, PCG,
physics, data tables and data assets, input, localization, project settings, landscape and foliage, the map's text
sections (`Actors`, `Actor:<label>`), and actors inside a Level Instance.

Also refused, because each would write outside that set: `save_assets` naming such a package (without paths it saves
the Lite ones and names the rest left unsaved), `open_level` while another dirty map would be saved,
`rename_asset` when a referencer outside the set would be resaved, `delete_assets` when such a referencer would
change, `set_properties` on settings (config class defaults), a Blueprint graph write that places a node running
Python (`PythonScriptLibrary.*`, Execute Python Script) or changes the values or links of one the graph already holds, and `set_properties` on a graph
node. A console-command node (`KismetSystemLibrary.ExecuteConsoleCommand`) is written like any other node.

## What Lite does not have

`run_python`, `run_console_command`, `live_coding_compile`, `import_assets` and `call_function` are not in
`tools/list`, and the script libraries (`JutsuLevelLibrary`, `JutsuLandscapeLibrary`, `JutsuPhysicsLibrary`, `JutsuDestructionLibrary`, `JutsuFractureLibrary`)
do not exist. The recipes of the other pages of this skill that use them do not apply.

## A refusal, and what to tell the user

A refused write is one sentence: what was asked, that it needs the full edition of Jutsu Unreal MCP, its Fab link,
and what Lite writes. Nothing was changed.

When the user asks for something only the full edition does, tell them once: name the thing, say the full edition
of Jutsu Unreal MCP does it, give the link https://www.fab.com/listings/7af5d379-9f12-4396-960b-a9e6428b3a33, then
carry on with what Lite can do (for a Niagara effect, a Blueprint that spawns an existing one; for a HUD, the
gameplay Blueprint that creates an existing widget and feeds it; for an Animation Blueprint, the gameplay Blueprint
around an existing one). The full edition installs beside Lite and wins when both are installed;
the agent's configuration does not change.
