# Blueprints

`write_asset`'s `text` description already covers the basic graph text (`<id> <type>` lines, `Pin = value|<id>.Pin`,
`ExecPin -> <id>[.Pin]`, the common node types) and the `Variables`, `Components` and `Defaults` line forms. This file adds the rest.

Blueprint graph (`EventGraph`, `Function:Name`, `Macro:Name`) node types beyond the ones `write_asset` lists; existing ids are GUID prefixes:

- `CustomEvent Name(P: type)` takes an RPC suffix: `[Server]`, `[Client]` or `[Multicast]`, plus
  `[Reliable]`, or `[Server, Reliable]`; no flags clears it; a `{...}` on a node kind that takes none is
  refused. A parameter passed by reference is `Name: ref Type` or `ref const Type`; `T&` and `const T&` also work.
- `ComponentEvent Comp.Delegate`, `Message Interface.Function`, `CallParent Function`, `PureCast Class`,
  `Self`, `Reroute`; another object's variable: `Get Class.Var` with `self` linked to it.
- `FunctionEntry(P: type)` takes ` [Pure]`, `[Const] [ThreadSafe] [Category "x"] [Keywords "y"]`; `[Exec]` makes
  it a console command, reached on the PlayerController, its Pawn, HUD, CheatManager or PlayerCameraManager,
  the GameMode, GameState or GameInstance. `FunctionResult(P: type)`; in a `Macro:` graph these are its
  tunnels, and exec pins are type `exec`.
- A function's local variables are `Local Name: type [= value]` lines at the top of its `Function:` text (type and
  default as in Variables, no flags); `Get Name`/`Set Name` use them, a local without its line is removed, and
  `Local New: int [was="Old"]` renames one, its `Get`/`Set` nodes and links kept (write them as `Get New`).
- An exec output, a data input and an anim graph pose output take one link (an exec input, a value output and a
  multi-target call's `self` take many); of two lines linking one such pin the later is not applied, naming both.
- Graph sections (these, anim graphs, a Level Sequence's `Director`) write partially: a node line that fails keeps the
  existing node of its id as it was, with its links and values, and its own lines and every line linking or naming it
  are not applied; so is a line setting a pin that such a kept node's link holds, or whose split or recombine would
  unlink one (the kept link wins). A pin line that fails keeps that pin's value and links (a far pin another applied line
  links stays with that line), and a pin it grew, showed, split or recombined goes back; a grown pin below one an applied line grew (`then_2` under `then_3`, `[2]` under `[3]`) stays, unlinked. A body line that does not parse keeps the links and values of every pin of
  its node that no other line names. A failed `Local` line keeps its local (a rename, retype or new local whose default
  does not take goes back, and the nodes naming the new name are not applied). The compile runs on what was applied;
  its errors do not undo the write. Whole: a new `Function:`/`Macro:` whose `FunctionEntry` or `FunctionResult` line
  fails is not created; in Lite, a line placing or rewiring a node that runs Python refuses the whole write.
- Node classes with JSON: `SpawnActorFromClass`, `SwitchEnum {"Enum":"/Script/Engine.ECollisionChannel"}`.
- Switch cases: `SwitchInteger` (optionally `{"StartIndex":1}`) takes `0 -> a`, `2 -> c`; naming
  a case adds it and any before it, and unnamed cases stay. `SwitchString`/`SwitchName` take
  their cases from `{"PinNames":["A","B"]}`, then `A -> a`. `SwitchGameplayTag` takes
  `{"PinTags":["A.B"]}`, then `A.B -> a`. A Gameplay Tag multi-compare
  (`MultiCompareGameplayTagContainer`) adds `TagCase_<n>` and `Case_<n> True` when named. Tags in
  node JSON and pin values need to be registered ([gameplay-tags.md](gameplay-tags.md)).
- Nodes with an **Add pin** button (`Sequence`, `K2Node_MakeArray`, `K2Node_DoOnceMultiInput`, ...)
  add the pins a line names, up to the node's limit; write the pin name bare: `-> d.C In`. A name
  the node cannot grow to fails its line, lists its pins, and the pins grown for it are taken back.
- `FormatText`: a literal `Format = "{a} {b}"` makes the argument pins `a` and `b` in the same write
  (link them: `a = count`; a literal text comes from a linked `MakeLiteralText`); a changed format
  drops the pins it no longer names. A linked Format keeps its arguments in `{"PinNames":["a"]}`.
- Binding an event to another object's dispatcher: the node `b1 AddDelegate {"DelegateReference":
  {"MemberParent":"/Script/Game.Door","MemberName":"OnOpened"}}` (id `b1`, type `AddDelegate`) with `self = <target>` and
  `Delegate = <event>.OutputDelegate`, where `<event>` is a `CustomEvent` named unlike any parent
  function; the Blueprint's own dispatcher is `{"MemberName":"OnOpened"}` alone. Calling a dispatcher is the node `CallDelegate {"DelegateReference":{"MemberName":"OnOpened"}}` (another object's: `MemberParent` too and `self` linked to it), its parameters as pins. The event takes the delegate's parameters, so write them as the delegate has them, by
  reference included: `ev CustomEvent OnDone(Context: ref const UpdateContext)`.
- Literals: vectors and rotators also `1,2,3` or `(Pitch=0,Yaw=90,Roll=0)`, enums by display name, keys by
  name (`B = "Escape"`); an unquoted word is a link, except a name of the pin's enum.
- Split struct pins read as `Position_X = ...`; naming a member splits the pin, naming it whole
  (`Position = v.ReturnValue`) recombines it.
- `Function:OnKeyDown` (a parent function) creates the override, while an event-style parent
  function is `Event Name` in the event graph.

Variables: types `bool int int64 float double string name text Vector Actor /Game/Path/BP_Door
class<Actor> soft<Texture2D> T[] set<T> map<K, V>` (Blueprint classes, user structs and enums by asset path); flags
`EditAnywhere BlueprintReadOnly ExposeOnSpawn Private Replicated RepNotify=Fn Transient SaveGame Config
Category= Tooltip=`; a name that is not an identifier reads quoted (`"My Speed": float`).

The write reply's `removed:` lists at most 20 names, then `+N`; `stored differently:` lists at most 10 ids, then `+N`;
`read_asset` with `match` on the ids shows the stored blocks. A `find_in_blueprints` hit without `line`: its
section's `match` search finds it.

Components / WidgetTree: a Components name that is not an identifier reads quoted, as in Variables
(`"My Mesh": StaticMeshComponent`); `[socket="hand_r"]` attaches a
component to its parent's socket or bone; inherited components are marked `[inherited]` and keep
their line, whose `{json}` overrides their properties.

A Blueprint's `Defaults` `Parent: Pawn` alone is a whole write; a text without the line keeps the
parent, and a refusal names the line.

One line per item: `Dispatchers` `OnHit(Damage: float)`; `Interfaces` an interface path.

`Variables`, `Components`, `Defaults`, `Interfaces` and `Dispatchers` write partially: a bad line (form, type, class, flag,
value, a `was` that names nothing, a name twice, one Unreal refuses) is skipped and named under `not applied:`, and the
item it names stays as it was (a failed `[was="Old"]` keeps `Old`); the other lines are written. Under a skipped
`Components` line the indented lines are skipped too, and its component keeps its children. Only items no line names are
removed: a line whose name cannot be read keeps them all. A `Defaults` text whose `Parent:` changes the parent is
whole: any problem refuses it, changing nothing. One undo takes a `Variables` write back; when it also added, removed,
renamed, retyped or reflagged a variable, the class shows the old defaults again only after the Blueprint's next compile.

`create_asset` `class` `Interface` makes a Blueprint Interface, `AnimLayerInterface` an Anim Layer Interface, `BlueprintFunctionLibrary` a function library, `EditorUtilityWidget` an Editor Utility Widget. A class `Blueprint` `parent` that is an interface or that no Blueprint derives from (`BlueprintFunctionLibrary`, `EditorFunctionLibrary`) is refused.
