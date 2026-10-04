---
name: using-jutsu-unreal-mcp
description: Text formats of the Jutsu Unreal MCP server's read_asset / write_asset / edit_asset sections (Blueprint graphs, variables, components, widget trees, materials) and how to report trouble. Use when editing Unreal assets through Jutsu as text, or when a Jutsu tool gave you trouble worth reporting.
---

# Using Jutsu Unreal MCP

The tools describe themselves; this page only adds the asset-text formats, so writes are right the
first time.

## Assets as text

`read_asset(path)` lists an asset's sections; `read_asset(path, section)` returns one. Change a part
with `edit_asset(path, section, old_text, new_text)` (exact, unique match, like a file edit), or
replace a section with `write_asset`. The written text is the whole resulting section: what it leaves
out is removed (in a `Document` section, listed items are created or updated and the rest stay).
Writes are all or nothing, compile a Blueprint whose structure or graphs change, report the
compiler's messages and save.

Blueprint graph (`EventGraph`, `Function:Name`, `Macro:Name`):

```
n4a2877 Event ReceiveBeginPlay
  then -> check
check Branch
  Condition = n85ea8a.bIsOpen
  then -> say
n85ea8a Get bIsOpen
say Call KismetSystemLibrary.PrintString
  InString = "Open"
```

- `<id> <type>`; existing ids are GUID prefixes, new nodes take any unused name.
- Under a node: `Pin = literal`, `Pin = <id>.OutPin`, `ExecPin -> <id>` or `-> <id>.Pin`.
- Types: `Event Name`, `CustomEvent Name(P: type)`, `ComponentEvent Comp.Delegate`,
  `Call Class.Function` / `Call self.Function`, `Message Interface.Function`, `CallParent Function`,
  `Get Var`, `Set Var`, `Branch`, `Sequence`, `Cast Class`, `PureCast Class`, `Self`, `Reroute`,
  `Macro ForEachLoop`, `MakeStruct S`, `BreakStruct S`, `FunctionEntry(P: type)`,
  `FunctionResult(P: type)` (in a `Macro:` graph these are its tunnels; exec pins are type `exec`),
  `Comment "text"`, or a node class with JSON: `SpawnActorFromClass`,
  `SwitchEnum {"Enum":"/Script/Engine.ECollisionChannel"}`.
- Literals: as read prints them; vectors and rotators also `1,2,3` or `(Pitch=0,Yaw=90,Roll=0)`,
  enums by display name; string, name and text literals are quoted (an unquoted word is a link).
  A rejected value fails the write and names the valid choices.
- Split struct pins read as `Position_X = ...`; naming a member splits the pin, naming it whole
  (`Position = v.ReturnValue`) recombines it.
- A new function: `write_asset(path, "Function:Open", "e FunctionEntry(Speed: float)\n  then -> ...")`;
  a new event-graph page: any free section name, e.g. `write_asset(path, "Combat", ...)`.

Variables: `Health: float = 100 [EditAnywhere, Category="Stats"]`; types `bool int int64 float
double string name text Vector Actor /Game/Path/BP_Door class<Actor> soft<Texture2D> T[] set<T>
map<K, V>` (Blueprint classes, user structs and enums by asset path; event dispatchers are not
listed); flags `EditAnywhere BlueprintReadOnly ExposeOnSpawn Private Replicated RepNotify=Fn
Transient SaveGame Config Category= Tooltip=`, and `was="OldName"` renames. Writing back what was
read replies `No change.` and saves nothing.

Components / WidgetTree: indented `Name: Class {"Prop":value}`; widget slots `@{"LayoutData":...}`;
inherited components are marked `[inherited]` and keep their line.

Material `Graph`: `<id> Multiply` with `A = <id>.RGB` inputs, then an `Output` block of
`BaseColor = <id>` lines. Material instance `Parameters`, `Defaults`, `Properties`: `Name = <json>`.

`Document` (StateTree, Behavior Tree, Niagara, PCG, MetaSound, Level Sequence, Control Rig, Anim
Blueprint state machines, maps): the JSON read returns. Copy a clause's shape to add an item
(most domains write `"create": {...}`); a clause with an existing item's `authoringId` (or its name
and type) updates it; items left out stay. Remove with `{"remove": {"authoringId": "..."},
"destructive": true}`.

Anything without a text section (sequencer keys, animation edits, editor utilities) is reachable
through `call_function` on Unreal's scripting libraries or `run_python` with the full `unreal` API.
Pass `uv0` with one entry per vertex on every GeometryScript `append_buffers_to_mesh` call; a
mesh saved without UVs by `create_new_static_mesh_asset_from_mesh` crashes the Editor.

## Reporting trouble

If the server refused something that looked valid, gave an error that did not say what to do next,
or forced hand work in the Editor, report it: exact call, exact response, no paraphrase, and say
when you guessed. Append the entry to the plugin checkout's `MCP_FEEDBACK.md` in the format its
header gives when you have that file; otherwise open a
[GitHub Issue](https://github.com/davbludev/JutsuUnrealMcpPublic/issues). If nothing gave you
trouble, write nothing.
