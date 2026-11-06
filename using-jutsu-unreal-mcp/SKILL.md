---
name: using-jutsu-unreal-mcp
description: Jutsu Unreal MCP asset text formats for read_asset / write_asset / edit_asset (Blueprints, materials, Niagara, animation, AI, GAS, audio and more), plus maps, landscapes and run_python in the Editor or PIE. Use before editing Unreal assets or levels through Jutsu.
---

# Using Jutsu Unreal MCP

The tools describe themselves; this page adds the asset-text formats, so writes are right the first
time, and names the file to read for each area.

Do the work with the plugin's MCP tools and asset text: they validate the input, compile, save and
report what changed. `run_python` is the last resort, for a result no tool reaches: check the tool
list, the asset's `read_asset` sections and `call_function` first, and when one of them does the
job, use it, even if it takes several calls. The files below name where Python is the intended
route (landscapes, World Partition, Level Instances).

Read the file that matches the task before the first write in its area:

| Task | Read |
| --- | --- |
| Widget Blueprints: `WidgetTree` canvas slots, `bIsVariable`, `[bind ...]` property bindings, `Animations`, widget events, driving a widget in PIE | [widget.md](widget.md) |
| Anim Blueprint graphs and `Machine:` state machines; Montage `Sections`, `Notifies`, `Sockets`; Anim Sequence, Montage and Blend Space data | [animation.md](animation.md) |
| Gameplay tags (path `GameplayTags`), tags used in nodes or pins | [gameplay-tags.md](gameplay-tags.md) |
| DataTable `Rows`: one `RowName: Column=value ...` line per row, renames, removal, nested struct and array columns | [data-table.md](data-table.md) |
| Gameplay Ability System: Gameplay Effects (modifiers, magnitudes, executions, components), Ability defaults, Cues, attribute references | [gas.md](gas.md) |
| Material and Material Function `Graph` and `Properties`, Material Instance `Parameters` | [material.md](material.md) |
| Sound Cue `Graph` | [sound-cue.md](sound-cue.md) |
| Niagara System, Emitter and Script assets (`Parameters`, `Emitters`, `System`, `Emitter`, `ScratchPad:`, `Graph`, compile reply) | [niagara.md](niagara.md) |
| MetaSound `Graph` (classes, wiring, interfaces), presets, member settings | [metasound.md](metasound.md) |
| Behavior Tree `Tree`, Blackboard `Keys` | [behavior-tree.md](behavior-tree.md) |
| StateTree `Tree`, StateTree components with parameter overrides | [state-tree.md](state-tree.md) |
| Smart Object `Definition` (slots, behaviors, annotations, parameters), Smart Object components | [smart-object.md](smart-object.md) |
| Customizable Object (Mutable) `Graph`, Macro Library `Macro:Name`, instance `Parameters` | [mutable.md](mutable.md) |
| Pose Search (Motion Matching) schemas and databases (`create_asset` parents, database `Assets`), Chooser Tables (`Table`), Proxy Tables (`Entries`) | [motion-matching.md](motion-matching.md) |
| Level Sequences: `Sequence` (playback, bindings, spawnables, event keys), `Binding:<Name>` tracks and keys, the `Director` and `Function:` graphs | [level-sequence.md](level-sequence.md) |
| Control Rig `Hierarchy`, `Rig` and `Function:` graphs, Sequencer Control Rig tracks, loading an animation onto them, baking; IK Rig, IK Retargeter | [control-rig.md](control-rig.md) |
| PCG graph `Graph` text: nodes, node settings, links, dynamic inputs, subgraphs, parameters | [pcg.md](pcg.md) |
| Maps (classic, partitioned): actors as text by Outliner folder (`Actors`, `Actors:<Folder>`), one actor's properties and components (`Actor:<label>`), the placeable classes and one class's components and properties (`Actors@<query>`), the `World` overview, World Partition loading and descriptors, Data Layers, HLOD, sublevels, Level Instances and Packed Level Actors (`unreal.JutsuLevelLibrary`), World Partition commandlets | [world.md](world.md) |
| Landscapes through `unreal.JutsuLandscapeLibrary`: create, sculpt, edit layers, Landscape Patch, target layers and paint, save | [landscape.md](landscape.md) |
| Landscape dressing: roads (splines), Water, PCG scatter, grass, physical material and Nanite builds | [landscape-dressing.md](landscape-dressing.md) |
| Multiplayer PIE (`netMode`, `players`, `world: "pie:<n>"`), navigation rebuilds, which editor answers | [pie.md](pie.md) |
| Any `run_python` script: crash gotchas (deleting assets, switching levels, GeometryScript UVs, primary data assets), frame rules, PIE handles | [run-python.md](run-python.md) |

Editor-state calls (`start_pie`, `stop_pie`, `live_coding_compile`, `open_level`) go one per
message, each after the previous one answered. `write_asset`, `edit_asset` and `compile_assets` on a
Blueprint of any kind (Actor, Widget, Anim, Control Rig) are refused while PIE runs: `stop_pie` first, write, then `start_pie`.
`start_pie` ignores the editor's saved Play settings and runs one standalone player: pass `netMode` and `players` for multiplayer. Multiplayer sessions: [pie.md](pie.md).

## Assets as text

`read_asset(path)` lists an asset's sections; `read_asset(path, section)` returns one. Change a part
with `edit_asset(path, section, old_text, new_text)` (exact, unique match, like a file edit), or
replace a section with `write_asset`. The written text is the whole resulting section: what it leaves
out is removed.
Node positions are not part of the text, so never try to place nodes.

`Properties`, `Defaults` and `Parameters` lines are `Name = <json>`; a single instanced subobject is
`{"class": "InputTriggerPressed", ...}` (`get_properties` adds its `path`, which writes ignore).
**An array of structs or instanced objects is a block, never JSON**: `Name =` and one indented line per
element, `Field=value` items split at spaces with nested members dotted, an instanced element led by its class,
only members that differ from the default, `()` for an all-default element. The lines are the whole array
(drop a line to remove its element; `Name =` alone or `Name = []` clears it):

    DefaultKeyMappings.Mappings =       (UE 5.6 and earlier: Mappings =)
      Action=/Game/Input/IA_Jump.IA_Jump Key=SpaceBar Triggers=[InputTriggerPressed ActuationThreshold=0.75] Modifiers=[InputModifierNegate]
      Action=/Game/Input/IA_Move.IA_Move Key=W Modifiers=[InputModifierDeadZone LowerThreshold=0.3, InputModifierScalar]

Items may come in any order; a read prints a struct's identity fields first (a mapping's `Action` and `Key`; a Gameplay Effect
modifier's `Attribute`, see gas.md), then the rest as the struct declares them, and writing that back is `No change.`;
a list in a line is `Field=[Class a=1, Class b=2]`. In a child Blueprint an element is written against the parent's element at
the same index (`()` keeps it). A member of a struct property is a dotted name, `Struct.Member = value`. Errors name the line and
element (`line 3: Modifiers[1].Attribute ...`). A String Table text reads `"LOCTABLE(\"/Game/ST_X.ST_X\", \"Key\")"`; write that string to bind a text to a table key, and copy a read line as it is to keep the binding (a new plain string writes a literal).

A read's `# note:` lines name what it does not show; writes skip them. A refusal
that names a read-only section `<Section>@<query>` points at the full list of valid names.

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
- Types: `Event Name`, `CustomEvent Name(P: type)` (an RPC: append `[Server]`, `[Client]` or `[Multicast]`, plus
  `[Reliable]`, or `[Server, Reliable]`; no flags clears it; a `{...}` on a node kind that takes none is refused),
  `ComponentEvent Comp.Delegate`,
  `Call Class.Function` / `Call self.Function`, `Message Interface.Function`, `CallParent Function`,
  `Get Var`, `Set Var` (another object's variable: `Get Class.Var` with `self` linked to it), `Branch`, `Sequence`, `Cast Class`, `PureCast Class`, `Self`, `Reroute`,
  `Macro ForEachLoop`, `MakeStruct S`, `BreakStruct S`, `FunctionEntry(P: type)` (append
  ` [Pure]` for a pure function; also `[Const] [ThreadSafe] [Category "x"] [Keywords "y"]`; `[Exec]` makes it a console command, reached on the PlayerController, its Pawn, HUD, CheatManager or
  PlayerCameraManager, the GameMode, GameState or GameInstance),
  `FunctionResult(P: type)` (in a `Macro:` graph these are its tunnels; exec pins are type `exec`),
  `Comment "text"`, or a node class with JSON: `SpawnActorFromClass`,
  `SwitchEnum {"Enum":"/Script/Engine.ECollisionChannel"}`.
- Switch cases: `SwitchInteger` (optionally `{"StartIndex":1}`) takes `0 -> a`, `2 -> c`; naming
  a case adds it and any before it, and unnamed cases stay. `SwitchString`/`SwitchName` take
  their cases from `{"PinNames":["A","B"]}`, then `A -> a`. `SwitchGameplayTag` takes
  `{"PinTags":["A.B"]}`, then `A.B -> a`. A Gameplay Tag multi-compare
  (`MultiCompareGameplayTagContainer`) adds `TagCase_<n>` and `Case_<n> True` when named. Tags in
  node JSON and pin values must be registered first ([gameplay-tags.md](gameplay-tags.md)).
- Nodes with an **Add pin** button (`Sequence`, `K2Node_MakeArray`, `K2Node_DoOnceMultiInput`, ...)
  add the pins a line names, up to the node's limit; write the pin name bare: `-> d.C In`. A name
  the node cannot grow to fails the write and lists its pins.
- `FormatText`: a literal `Format = "{a} {b}"` makes the argument pins `a` and `b` in the same write
  (link them: `a = count`; a literal text comes from a linked `MakeLiteralText`); a changed format
  drops the pins it no longer names. A linked Format keeps its arguments in `{"PinNames":["a"]}`.
- Binding an event to another object's dispatcher: `bind AddDelegate {"DelegateReference":
  {"MemberParent":"/Script/Game.Door","MemberName":"OnOpened"}}` with `self = <target>` and
  `Delegate = <event>.OutputDelegate`, where `<event>` is a `CustomEvent` named unlike any parent
  function; the Blueprint's own dispatcher is `{"MemberName":"OnOpened"}` alone. The event takes the delegate's parameters, so write them as the delegate has them, by
  reference included: `ev CustomEvent OnDone(Context: ref const UpdateContext)`; other text is refused
  with the line that fits.
- A parameter passed by reference is `Name: ref Type` or `ref const Type`; `T&` and `const T&` also work.
- Literals: as read prints them; vectors and rotators also `1,2,3` or `(Pitch=0,Yaw=90,Roll=0)`,
  enums by display name, keys by name (`B = "Escape"`); string, name and text literals are quoted
  (an unquoted word is a link, except a name of the pin's enum).
  A rejected value fails the write and names the valid choices.
- Split struct pins read as `Position_X = ...`; naming a member splits the pin, naming it whole
  (`Position = v.ReturnValue`) recombines it.
- A new function: `write_asset(path, "Function:Open", "e FunctionEntry(Speed: float)\n  then -> ...")`;
  `Function:OnKeyDown` (a parent function) creates the override, while an event-style parent
  function is `Event Name` in the event graph; a new event-graph page: any free section name, e.g.
  `write_asset(path, "Combat", ...)`.

Variables: `Health: float = 100 [EditAnywhere, Category="Stats"]`; types `bool int int64 float
double string name text Vector Actor /Game/Path/BP_Door class<Actor> soft<Texture2D> T[] set<T>
map<K, V>` (Blueprint classes, user structs and enums by asset path); flags `EditAnywhere BlueprintReadOnly ExposeOnSpawn Private Replicated RepNotify=Fn
Transient SaveGame Config Category= Tooltip=`, and `was="OldName"` renames; a name that is not an
identifier reads quoted (`"My Speed": float`). Writing back what was read replies `No change.` and
saves nothing. Any other write replies `ok`, then only lines you cannot know from your own text:
`ids: <written>=<stored>, ...` for nodes stored under another id (name them
by the stored id in your next edit), `removed: ...` after a `write_asset` (what the text left out; at
most 20 names, then `+N`), `compile:` with its messages when the compile was not clean, and `warning:`
lines. A clean compile, the saved asset and what you added or changed are not repeated: `read_asset` the
section to see them. When the asset stores a write differently (ids replaced, order normalised,
defaults dropped), one line says so, `stored differently: <ids, at most 10, then +N>`; `read_asset`
them before the next `edit_asset` on them. An `edit_asset` miss shows the nearest lines.

Components / WidgetTree: indented `Name: Class {"Prop":value}` (a Components name that is not an
identifier reads quoted, as in Variables: `"My Mesh": StaticMeshComponent`); widget slots as a record, `@ Anchors=0,1 Offsets=40,-40,300,24 Alignment=0,1` (widget.md);
`[socket="hand_r"]` attaches a component to its parent's socket or bone; inherited components are
marked `[inherited]` and keep their line, whose `{json}` overrides their properties. A changed default reaches placed instances that kept the
old value.

A Blueprint's `Defaults` starts with `Parent: Pawn`, its parent class; write another class to reparent it
(`Parent: Pawn` alone is a whole write; a text without the line keeps the parent, a refusal names the line).

One line per item: `Dispatchers` `OnHit(Damage: float)`; `Interfaces` an interface path; user
struct `Fields` `Count: int = 3` (the Variables types but `map`, `softclass<Actor>` too; names read quoted as in Variables); user enum `Entries` a name; String Table `Entries`
`Key = "Text"`.

No asset has a `Document` section: asking for it is refused, and the refusal names the text section to use (Blueprint
`Variables`/`Defaults`/graphs, Widget Blueprint `WidgetTree`, Material and MetaSound `Graph`, StateTree and Behavior
Tree `Tree`, Control Rig `Hierarchy`/`Rig`/`Function:Name`).

Anything without a text section (animation curves and sync markers, editor utilities) is reachable
through `call_function` on Unreal's scripting libraries, and past that through `run_python`.
Curve assets (`CurveFloat`, `CurveVector`, `CurveLinearColor`) have a `Keys` section: one key per line,
`0.5: 1 linear`, `1: 2 cubic user arrive=0.5 leave=0.5` (`constant`/`linear`/`cubic`; cubic may add
`smart_auto`, or `user`/`break` with `arrive=` `leave=`, and `arrive_weight=` `leave_weight=`). Vector and
colour curves put keys under `X:` / `R:` channel headers; a channel left out is cleared. Check values
with `get_float_value(t)`.
`create_asset` `options` set factory properties: a BlendSpace needs `{"TargetSkeleton": path}`; a
Blueprint interface is `class Blueprint`, `parent Interface`, `{"BlueprintType": "BPTYPE_Interface"}`.
