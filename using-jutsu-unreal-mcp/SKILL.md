---
name: using-jutsu-unreal-mcp
description: Text formats of the Jutsu Unreal MCP server's read_asset / write_asset / edit_asset sections (Blueprint and anim graphs, variables, components, widget trees, materials, sound cues, Niagara systems, emitters, scripts and scratch pads, Control Rig hierarchies and graphs, StateTrees, Smart Objects). Use when editing Unreal assets through Jutsu as text, or scripting the Editor or PIE through its run_python.
---

# Using Jutsu Unreal MCP

The tools describe themselves; this page only adds the asset-text formats, so writes are right the
first time.

Reach first for the plugin's own tools and asset text: they validate the input, compile, save and
report what changed. Take `run_python` for what they do not cover (check the tool list and the
asset's `read_asset` sections first) and for bulk work a script does more simply, such as a loop
over many assets or actors.

Editor-state calls (`start_pie`, `stop_pie`, `live_coding_compile`, `open_level`) go one per
message, each after the previous one answered.

## Assets as text

`read_asset(path)` lists an asset's sections; `read_asset(path, section)` returns one. Change a part
with `edit_asset(path, section, old_text, new_text)` (exact, unique match, like a file edit), or
replace a section with `write_asset`. The written text is the whole resulting section: what it leaves
out is removed (in a `Document` section, listed items are created or updated and the rest stay).
Writes are all or nothing, compile a Blueprint whose structure or graphs change, report the
compiler's messages and save. The plugin lays out every graph it changes; node positions are not
part of the text, so never try to place nodes.

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
  `Get Var`, `Set Var` (another object's variable: `Get Class.Var` with `self` linked to it), `Branch`, `Sequence`, `Cast Class`, `PureCast Class`, `Self`, `Reroute`,
  `Macro ForEachLoop`, `MakeStruct S`, `BreakStruct S`, `FunctionEntry(P: type)` (append
  ` [Pure]` for a pure function),
  `FunctionResult(P: type)` (in a `Macro:` graph these are its tunnels; exec pins are type `exec`),
  `Comment "text"`, or a node class with JSON: `SpawnActorFromClass`,
  `SwitchEnum {"Enum":"/Script/Engine.ECollisionChannel"}`.
- Binding an event to another object's dispatcher: `bind AddDelegate {"DelegateReference":
  {"MemberParent":"/Script/Game.Door","MemberName":"OnOpened"}}` with `self = <target>` and
  `Delegate = <event>.OutputDelegate`, where `<event>` is a `CustomEvent` named unlike any parent
  function.
- Literals: as read prints them; vectors and rotators also `1,2,3` or `(Pitch=0,Yaw=90,Roll=0)`,
  enums by display name, keys by name (`B = "Escape"`); string, name and text literals are quoted
  (an unquoted word is a link).
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
Transient SaveGame Config Category= Tooltip=`, and `was="OldName"` renames. Writing back what was
read replies `No change.` and saves nothing.

Components / WidgetTree: indented `Name: Class {"Prop":value}`; widget slots `@{"LayoutData":...}`;
`[socket="hand_r"]` attaches a component to its parent's socket or bone; inherited components are
marked `[inherited]` and keep their line, whose `{json}` overrides their properties. A changed default reaches placed instances that kept the
old value.

One line per item: `Dispatchers` `OnHit(Damage: float)`; `Interfaces` an interface path; user
struct `Fields` `Count: int = 3`; user enum `Entries` a name; String Table `Entries`
`Key = "Text"`.

Anim Blueprint graphs, Montage `Sections`, `Notifies` and `Sockets`: read [animation.md](animation.md)
before writing one.

Widget `Animations`: `FadeIn [0-0.5]` (range in seconds, `[was="Old"]` renames), then per keyed
channel `  Panel.RenderOpacity: 0=0 linear, 0.5=1` or `  Title.RenderTransform.Translation.X: 0=-200, 0.5=0`
(`Translation.X/Y`, `Angle`, `Scale.X/Y`, `Shear.X/Y`; keys `seconds=value`, `constant`/`linear`,
cubic when omitted). Left-out keys, channels and animations are removed; other tracks are kept.

Gameplay tags (path `GameplayTags`) and a GameplayEffect's tags: read [gameplay-tags.md](gameplay-tags.md) before writing one.

Material `Graph`, material instance `Parameters`, `Defaults` and `Properties`, and `Name = <json>`
properties holding instanced subobjects: read [material.md](material.md) before writing one.

Sound Cue `Graph`: read [sound-cue.md](sound-cue.md) before writing one.

Niagara System, Emitter and Script assets (`Parameters`, `Emitters`, `System`, `Emitter`,
`ScratchPad:` and `Graph` sections, and their compile reply): read [niagara.md](niagara.md) before
writing one.

`Document` (StateTree, Behavior Tree, PCG, MetaSound, Level Sequence, Control Rig, Anim
Blueprint state machines, maps): the JSON read returns. Copy a clause's shape to add an item
(most domains write `"create": {...}`); a clause with an existing item's `authoringId`, the key the
read printed for it (StateTree `state_19`, valid until the next write), or its name and type updates
it; items left out stay. Remove with `{"remove": {"authoringId": "..."}, "destructive": true}`; a
remove that matches nothing fails and lists what is there. Leading `// ` lines of a read are notes (what it leaves out); writes skip them.

StateTree `Tree` text and StateTree components with parameter overrides: read
[state-tree.md](state-tree.md) before writing one.

Smart Object `Definition` text (slots, behaviors, annotations, parameters) and Smart Object
components: read [smart-object.md](smart-object.md) before writing one.

MetaSound presets and inputs with defaults: read [metasound.md](metasound.md) before writing one.

Control Rig `Hierarchy` (controls, nulls, their settings), `Rig` and `Function:` graphs,
Sequencer Control Rig tracks, loading an animation onto them and baking: read
[control-rig.md](control-rig.md) before building a rig.

Anything without a text section (sequencer keys, animation edits, editor utilities) is reachable
through `call_function` on Unreal's scripting libraries, and past that through `run_python`.
Curve assets (`CurveFloat`, `CurveVector`, `CurveLinearColor`) have a `Keys` section: one key per line,
`0.5: 1 linear`, `1: 2 cubic user arrive=0.5 leave=0.5` (`constant`/`linear`/`cubic`; cubic may add
`smart_auto`, or `user`/`break` with `arrive=` `leave=`, and `arrive_weight=` `leave_weight=`). Vector and
colour curves put keys under `X:` / `R:` channel headers; a channel left out is cleared. Check values
with `get_float_value(t)`.
`create_asset` `options` set factory properties: a BlendSpace needs `{"TargetSkeleton": path}`; a
Blueprint interface is `class Blueprint`, `parent Interface`, `{"BlueprintType": "BPTYPE_Interface"}`.

`run_python` crash gotchas (globals that outlive a call, deleting assets, switching levels, GeometryScript
UVs, duplicated primary data assets), frame and PIE rules, and navigation rebuilds: read
[run-python.md](run-python.md) before scripting the Editor or PIE.
