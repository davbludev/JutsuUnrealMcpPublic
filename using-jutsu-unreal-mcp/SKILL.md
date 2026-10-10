---
name: using-jutsu-unreal-mcp
description: Text formats of the Jutsu Unreal MCP server's read_asset / write_asset / edit_asset sections (Blueprint and anim graphs, variables, components, widget trees, materials, sound cues, Niagara systems, emitters, scripts and scratch pads) and how to report trouble. Use when editing Unreal assets through Jutsu as text, or when a Jutsu tool gave you trouble worth reporting.
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
  `Get Var`, `Set Var`, `Branch`, `Sequence`, `Cast Class`, `PureCast Class`, `Self`, `Reroute`,
  `Macro ForEachLoop`, `MakeStruct S`, `BreakStruct S`, `FunctionEntry(P: type)` (append
  ` [Pure]` for a pure function),
  `FunctionResult(P: type)` (in a `Macro:` graph these are its tunnels; exec pins are type `exec`),
  `Comment "text"`, or a node class with JSON: `SpawnActorFromClass`,
  `SwitchEnum {"Enum":"/Script/Engine.ECollisionChannel"}`.
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

Anim Blueprint graphs use the same text: `Function:AnimGraph`, a state's pose graph
`State:Locomotion/Idle`, a transition rule `Transition:Locomotion/Idle->Run`. Anim nodes are their
class without `AnimGraphNode_` (`SequencePlayer {"Node":{"Sequence":"/Game/A_Run.A_Run"}}`,
`BlendListByBool`, `LocalRefPose`); poses link like values; `StateMachine Locomotion` is a machine
(another name renames it). The result node (`Root`, `StateResult`, `TransitionResult`) stays:

```
sm StateMachine Locomotion
out Root
  Result = sm.Pose
```
```
speed Get Speed
fast Call KismetMathLibrary.Greater_DoubleDouble
  A = speed
  B = 10
out TransitionResult
  bCanEnterTransition = fast.ReturnValue
```

States, the entry and transitions are added in `Document`; their graphs then appear as sections.
Naming an optional property in a pin line (`PlayRate = 2`) exposes it as a pin.

Variables: `Health: float = 100 [EditAnywhere, Category="Stats"]`; types `bool int int64 float
double string name text Vector Actor /Game/Path/BP_Door class<Actor> soft<Texture2D> T[] set<T>
map<K, V>` (Blueprint classes, user structs and enums by asset path); flags `EditAnywhere BlueprintReadOnly ExposeOnSpawn Private Replicated RepNotify=Fn
Transient SaveGame Config Category= Tooltip=`, and `was="OldName"` renames. Writing back what was
read replies `No change.` and saves nothing.

Components / WidgetTree: indented `Name: Class {"Prop":value}`; widget slots `@{"LayoutData":...}`;
`[socket="hand_r"]` attaches a component to its parent's socket or bone; inherited components are
marked `[inherited]` and keep their line. A changed default reaches placed instances that kept the
old value.

One line per item: `Dispatchers` `OnHit(Damage: float)`; `Interfaces` an interface path; user
struct `Fields` `Count: int = 3`; user enum `Entries` a name; String Table `Entries`
`Key = "Text"`.

Widget `Animations`: `FadeIn [0-0.5]` (range in seconds, `[was="Old"]` renames), then per keyed
channel `  Panel.RenderOpacity: 0=0 linear, 0.5=1` or `  Title.RenderTransform.Translation.X: 0=-200, 0.5=0`
(`Translation.X/Y`, `Angle`, `Scale.X/Y`, `Shear.X/Y`; keys `seconds=value`, `constant`/`linear`,
cubic when omitted). Left-out keys, channels and animations are removed; other tracks are kept.

Montage `Sections`: `Loop @ 0.5 -> Loop` (seconds, optional next section). Montage and sequence
`Notifies`: `Track: Name` lines, each followed by `  0.25 AnimNotify_PlaySound {"Sound":"..."}`,
`  0.25-0.75 AnimNotifyState_Trail {...}` (a state's start-end) or `  0.5 "Footstep"` (skeleton
notify); one notify per start time on a track; a notify matches by track, time and class. `Sockets`: skeleton `Grip: hand_r {"RelativeLocation":{"X":10}}`,
Static Mesh `Grip {"Tag":"grip"}`. `[was="Old"]` renames a section or socket.

Gameplay tags: path `GameplayTags` (no asset). `Tags` (DefaultGameplayTags.ini) or
`Tags:<File>.ini`: `Tag.Name [comment="..."]`, `[was="Old.Tag"]` renames with a redirect;
`Redirects`: `Old.Tag -> New.Tag` (DefaultGameplayTags.ini only; redirects inside Config/Tags files
are not shown). A write is usable at once, no restart; never edit the ini by hand.

Material `Graph`: `<id> Multiply` with `A = <id>.RGB` inputs, then an `Output` block of
`BaseColor = <id>` lines. Material instance `Parameters`, `Defaults`, `Properties`: `Name = <json>`;
an instanced subobject (input trigger, Blackboard key type) is `{"class": "InputTriggerPressed", ...}`;
struct array elements list only changed members (`{}`: all default).

Sound Cue `Graph`: `<id> WavePlayer {"SoundWaveAssetPtr":"/Game/S_Step.S_Step"}`, `<id> Random`,
`Mixer`, `Attenuation`... (the SoundNode class without its prefix), inputs as `0 = <id>` (by index, or
the input's name such as `True` on a Branch), then `Output = <id>`. ` [inputs=N]` keeps unlinked
inputs; a Random node's `Weights` take one value per input (left out, each is 1). Writes keep the Sound Cue Editor's graph in step.

Niagara System, Emitter and Script assets (`Parameters`, `Emitters`, `System`, `Emitter`,
`ScratchPad:` and `Graph` sections, and their compile reply): read [niagara.md](niagara.md) before
writing one.

`Document` (StateTree, Behavior Tree, PCG, MetaSound, Level Sequence, Control Rig, Anim
Blueprint state machines, maps): the JSON read returns. Copy a clause's shape to add an item
(most domains write `"create": {...}`); a clause with an existing item's `authoringId` (or its name
and type) updates it; items left out stay. Remove with `{"remove": {"authoringId": "..."},
"destructive": true}`. Leading `// ` lines of a read are notes (what it leaves out); writes skip them.
A MetaSound preset: create the asset, then write `"preset": {"parent": "<same-kind MetaSound>"}` with
input overrides as `{"find": {"kind": "input", "name": "Gain"}, "default": 0.25}` nodes.

Anything without a text section (sequencer keys, animation edits, editor utilities) is reachable
through `call_function` on Unreal's scripting libraries or `run_python` with the full `unreal` API.
`run_python` globals outlive the call: set every UObject they hold to `None` before deleting or
moving its asset (or delete with `delete_assets`), or `EditorAssetLibrary.delete_asset` can crash
the Editor.
Right after a level opens, the editor world's navigation build stays locked until loading settles
(at least 2 s, no assets still compiling): a `RebuildNavigation` then logs `navigation build is
locked (flags: 0x20)`. `wait` a few seconds and run it again, or query paths in PIE.
A headless `UnrealEditor-Cmd` run of the same project serves the MCP port too; `get_editor_state`
`pid` tells which process answered.
`create_asset` `options` set factory properties: a BlendSpace needs `{"TargetSkeleton": path}`; a
Blueprint interface is `class Blueprint`, `parent Interface`, `{"BlueprintType": "BPTYPE_Interface"}`.

A duplicated primary data asset shares its source's Primary Asset Id and the Asset Manager hands the
id to the copy (engine behaviour): change the copy's id property at once; restart the editor if the
source has dropped out of `get_primary_asset_id_list`.
Pass `uv0` with one entry per vertex on every GeometryScript `append_buffers_to_mesh` call; a
mesh saved without UVs by `create_new_static_mesh_asset_from_mesh` crashes the Editor.

## Reporting trouble

If the server refused something that looked valid, gave an error that did not say what to do next,
or forced hand work in the Editor, report it: exact call, exact response, no paraphrase, and say
when you guessed, in a [GitHub Issue](https://github.com/davbludev/JutsuUnrealMcpPublic/issues).
If nothing gave you trouble, write nothing.
