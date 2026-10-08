# Usage

The connected server's `tools/list` is authoritative: every tool and parameter is described there. This page summarizes the conventions they share.

## Naming things

| Thing | Accepted forms |
| --- | --- |
| Asset | package path `/Game/UI/WBP_HUD`, object path `/Game/UI/WBP_HUD.WBP_HUD`, file path `Content/UI/WBP_HUD.uasset`, or a unique asset name `WBP_HUD` |
| Class | `StaticMeshActor`, `AStaticMeshActor`, `/Script/Engine.StaticMeshActor`, or a Blueprint path (its generated class) |
| Actor | outliner label `Door 2`, name `BP_Door_C_2`, or object path; `Door 2.Mesh` names a component |
| Any object | its object path, including PIE objects |
| Project settings | the settings class name, such as `GameMapsSettings` |

`world` is `editor` (default) or `pie` where it matters; a PIE object path selects PIE by itself. A Blueprint given to a property or function tool means its class defaults.

## Values

Values are plain JSON, converted to the target property's type: numbers, booleans, strings, enum names, asset paths for references, `{member: value}` for structs (only the given members change), and arrays. Unreal text syntax such as `(X=1,Y=2,Z=3)` is accepted anywhere a value is.

## Assets as text

`read_asset(path)` returns an outline of the asset's sections; `read_asset(path, section)` returns one section as text. `write_asset(path, section, text)` makes the section match the text, removing what the text leaves out; `edit_asset(path, section, old_text, new_text)` applies one exact text replacement, like a file edit. A write is all or nothing, compiles Blueprints, reports what changed with any compiler messages, and saves the asset. Node positions are never part of the text: every graph a write changes is laid out again by the plugin, so it stays readable without anyone arranging nodes.

| Asset | Sections |
| --- | --- |
| Blueprint | `Variables`, `Defaults`, `EventGraph` and other graph pages, `Function:Name`, `Macro:Name`; Actor Blueprints also `Components`; Widget Blueprints also `WidgetTree`; Animation Blueprints also `State:Machine/State` and `Transition:Machine/From->To` (the AnimGraph is `Function:AnimGraph`) |
| Material, Material Function, Sound Cue | `Graph` |
| Material Instance | `Parameters` |
| DataTable | `Rows` |
| StateTree, Behavior Tree, Niagara, PCG, MetaSound, Level Sequence, Control Rig, Animation Blueprint state machines, maps | `Document` (a JSON document) |
| Other assets | `Properties`; some also a read-only `Details` |

Writing a section that does not exist creates it (a new function, macro or graph page); writing empty text to a function, macro or page deletes it. Read a section before writing it: the read is the format to write.

## Saving

Asset edits through `write_asset`, `edit_asset`, `set_properties` and the asset tools are saved as they are made. Level edits (`spawn_actor`, `delete_actors`, `set_actor_transform`, properties of placed actors) stay unsaved until `save_assets`.

## Play In Editor

`start_pie` returns once the game is running and `stop_pie` once it has ended. `send_input` presses a key or drives an Enhanced Input action for some seconds; `wait` lets the game run. Both return what the game printed. `take_screenshot` returns the PIE view with its UI, or the level viewport, as a PNG and saves it under `Saved/Screenshots/MCP`. Actors and properties in the running game are reached with `world: "pie"`.

## Python and console

`run_python` runs Python with the `unreal` module and returns what it printed; globals persist between calls and a one-line expression prints its value. `run_console_command` runs cvars, cheats, exec functions and stat commands. Use them for anything the other tools do not cover.

## Errors

A failed call returns `isError` with text naming the argument at fault and the valid choices. Unknown arguments are refused with the accepted list. A failed asset write leaves the asset as it was.
