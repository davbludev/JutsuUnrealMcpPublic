# Niagara as text

## Sections of a system

| Section | Holds |
|---|---|
| `Parameters` | `User.*` parameters, one per line; `System.*` ones the parameter panel declares |
| `Emitters` | one line per emitter, in order |
| `System` | the `SystemSpawn` and `SystemUpdate` stacks |
| `Emitter:<Name>` | the emitter's `Properties`, `Parameters` (`Emitter.*`), four stacks, event handlers, simulation stages, `Renderers`; a lightweight one's `Properties`, `Modules`, `Renderers` |
| `ScratchPad:<Name>`, `ScratchPad:<Emitter>/<Name>` | one scratch-pad graph (below) |
| `Inputs@<module>` | read-only: a module's inputs, their types, values and what hides them (below) |
| `Properties` | the system's own settings, as for any asset (warmup below) |

An emitter asset (`create_asset` class `NiagaraEmitter`) has `Emitter`, the same text as
`Emitter:<Name>` (`User.*` links are not checked there: the system using it declares them), and its
own `ScratchPad:<Name>` sections. `[from=<that asset>]` adds it to a system as a child: its modules
and scratch pads come from the parent (Niagara renames the pads, e.g. `ScratchPad:<Emitter>/<Name>_0`)
and are edited in the emitter asset. A script asset (`create_asset` class `NiagaraScript`) has
`Graph`, scratch-pad text (below); its `Output` line sets the kind. Stack lines name it by path;
Niagara names the module after the asset. Epic's library scripts read as `Graph` too.

A Cascade `ParticleSystem` has read-only `Emitter:<Name>` sections: the emitter's `<class> <object>` and
settings, then each `LOD <k>` with its modules as `<class> <object>` and their changed properties
(`(same as LOD 0)` for a shared one). Adding or removing emitters, modules and LODs needs the Cascade
editor; their properties take `set_properties` with `object="<asset object path>:<object>"`. The
system's own settings (bounds, warmup, LOD distances) are `Properties`.

Build a system in this order: `Parameters`, `Emitters`, scratch pads, then `System` and `Emitter:` stacks.

Warmup in the system's `Properties`: write `WarmupTime` (or `WarmupTickCount`) with `WarmupTickDelta`;
the other follows; listing both keeps the one that changed (the count when both did), and a write
that changes neither keeps the warmup as held.
Niagara floors the time to whole ticks (engine): `WarmupTime = 1` on the default delta 1/15 stores
14 ticks, 0.933 s. Pick a delta that divides the time (`0.05`, `0.25`).

```
User.TracerColor: LinearColor = (R=6,G=3,B=0.8,A=1)
User.TracerWidth: float = 3
```

- Parameter lines are `Namespace.Name: type = value`; a data interface is its class without
  `NiagaraDataInterface` and its changed properties as JSON. Types are those of scratch pads.
  `System.*` and `Emitter.*` lines declare a parameter without a value (modules write it).
- Vector, colour and Quat values of inputs and user parameters also take their numbers in order: vector X,Y,Z(,W),
  Position X,Y,Z, colour R,G,B,A, Quat X,Y,Z,W; a left-out number is 0, but a colour's A and a Quat's W are 1.
- `Emitters` lines are `Name [flags]`. A new name takes one origin: `[from=<emitter asset>]` (a
  template under `/Niagara/DefaultAssets/Templates/Emitters/` or any emitter asset), `[empty]` (Niagara's Minimal emitter)
  or `[lightweight]`; on an existing name these are ignored. `[disabled]`
  disables, leaving it out enables; `[was="Old"]` renames (a quote left open skips the line, and the emitter
  it names stays); a left-out line removes the emitter; the
  order of lines is the emitter order. Reads add `[lightweight]` and `[parent=<asset>]`.

```
EmitterUpdate
  EmitterState: /Niagara/Modules/Emitter/EmitterState
    Life Cycle Mode = Self
  SpawnFromChannel: ScratchPad:Tracers/SpawnFromChannel
    DataChannel = {"Channel": "/Game/VFX/NDC_Tracers.NDC_Tracers"}

ParticleSpawn
  InitializeParticle: /Niagara/Modules/Spawn/Initialization/V2/InitializeParticle
    Lifetime = Call /Niagara/DynamicInputs/UniformRange/UniformRangedFloat
      Minimum = 0.03
      Maximum = 0.06
    Color = User.TracerColor

Renderers
  Sprite {"Alignment": "VelocityAligned"}
```

- A stack is its header (`SystemSpawn`, `SystemUpdate`, `EmitterSpawn`, `EmitterUpdate`,
  `ParticleSpawn`, `ParticleUpdate`), then its modules in order: `<Name>: <module script path or
  ScratchPad section> [disabled]`. A module keeps its name; a new one is named after its script.
- `EventHandler <Emitter>/<Event> [ExecutionMode=SpawnedParticles, SpawnNumber=3]` stacks take events
  (`DeathEvent`, `LocationEvent`, `Collision`) the source writes with its `Generate…Event` module (CPU
  only; death events need `bRequiresPersistentIDs = true`); receive with `/Niagara/Modules/Events/Receive{Death,Location,Collision}Event`.
- `SimulationStage <Name> [NumIterations=2, IterationSource=DataInterface, DataInterface=Emitter.Grid, disabled]`
  stacks run on GPU emitters only (`SimTarget = "GPUComputeSim"`); a scratch pad there has `[Usage=SimulationStage]`.
- Under a module, only overridden inputs, by the name `Inputs@` prints (spaces included; a near name is
  refused with the names that exist). A value is a
  literal (`2.5`, `true`, `(R=1,G=0,B=0,A=1)` or numbers in order `(0,0,-300)` (SKILL.md), an enum entry's name), a linked parameter
  (`User.TracerColor`, `Particles.Gravity`), `Call <dynamic input script or ScratchPad section>` with
  its own inputs indented under it, a data interface's changed properties as `{json}` (`{}` for its
  defaults), or `Hlsl "<expression>"`. An input left out returns to the module default.
- Input lines are stored in the module's own order, and an input equal to its default is not listed.
- `read_asset` `Inputs@<module>` lists a module's inputs, one `Name - type, ...` line each: a static
  switch with the values it takes (`switch, one of Uniform Curve, Non-Uniform`), an enum's entries, the
  module's `default` or the `value` set, and for an input that is off `inactive: shows when <Switch> = <value>
  (now <current>)`. Name the module by where it is, `Inputs@Emitter:Smoke/ParticleUpdate/GravityForce`
  (`System/SystemUpdate/<Module>` for a system stack; `Inputs@Emitter/<Stack>/<Module>` on an
  emitter asset), or by script before you add it, `Inputs@/Niagara/Modules/Update/Forces/GravityForce`
  (a `ScratchPad:` section too). Read it instead of provoking an error to get the list.
- An input the switches hide takes a value once its switch shows it: set the switch in the same
  lines (any order) or first.
- A checkbox is an input line of its own (`Use Spawn Probability = true`, true or false); `Inputs@`
  lists it as `Use Spawn Probability - bool, ..., the checkbox of Spawn Probability` and marks the
  guarded input `off until Use Spawn Probability = true` while it is false; read shows it only when it
  differs from its default; a left-out line returns it to the default; while any overridden input's
  checkbox is off, every write reply says `stack warning <Section> <Module>: <Input> is off until <Toggle> = true.`
- A `SetParameters` module sets stack parameters. Its inputs are its targets: `Particles.CameraOffset =
  55`. A target the engine knows takes its type; another is typed once, `Particles.Gain: float = 2`
  (later reads list `Particles.Gain = 2`). A target left out is removed, the module stays.

```
ParticleUpdate
  CamOffset: SetParameters
    Particles.CameraOffset = 55
    Particles.Gain: float = 2
```
- A Data Channel read takes its channel as the module input's `{json}` value: linked to a `User.*`
  data interface it never spawns (engine behaviour). Read the spawned particle's entry by
  `Op Util::ExecIndex`, not `GetNDCSpawnData`, which only the spawning module's interface answers.
- `Properties` are `Name = <json>` lines of the emitter's settings (`SimTarget`, `bLocalSpace`,
  `CalculateBoundsMode`, `FixedBounds`, ...). `Renderers` are `Class {json}` lines (`Sprite`,
  `Ribbon`, `Mesh`, `Light`, ...); a renderer is known by its position. Its attribute and User
  parameter bindings are names in the same json: `Ribbon {"RibbonWidthBinding": "Particles.Mass",
  "MaterialUserParamBinding": "User.Mat"}`. A binding that is the renderer's own is not listed, and
  one left out goes back to it. A `User.` name must be declared in `Parameters` first, with the type the
  binding takes (a material binding takes `/Script/Engine.MaterialInterface`, written there as
  `User.Mat: /Script/Engine.MaterialInterface` or with the asset as a quoted path).

```
Properties
  EmitterState = {"LoopBehavior": "Once"}
  SpawnInfos =
    Amount.Min=12 Amount.Max=12

Modules
  InitializeParticle {"LifetimeDistribution": {"Mode": "UniformRange", "ChannelConstantsAndRanges": [0.1, 0.25]}}
  GravityForce {}
  SolveVelocitiesAndForces {}

Renderers
  Sprite {"Material": "/Niagara/DefaultAssets/DefaultSpriteMaterial.DefaultSpriteMaterial"}
```

- A lightweight emitter has `Properties` (its settings: `EmitterState`, `SpawnInfos`, `FixedBounds`,
  ...; `SpawnInfos` and other arrays of records are blocks: `SpawnInfos =` and one record line per
  element, indented under it), `Modules` and `Renderers`. Its modules are fixed: a listed one is on, with its changed
  properties as `{json}` (class without `NiagaraStatelessModule_`); one left out is off, its settings
  kept. `InitializeParticle` and `SolveVelocitiesAndForces` are always on.
- A distribution is its `Mode` with `ChannelConstantsAndRanges` (`UniformRange` one range for all
  channels, `NonUniformRange` per channel); its `Min`, `Max` and `Values` follow from them (engine).

## Scratch pads

A Niagara system's scratch-pad scripts are sections: `ScratchPad:<Name>` for the system's own,
`ScratchPad:<Emitter>/<Name>` for one emitter's. Writing a name that does not exist creates a scratch
pad of the kind its `Output` names; writing an existing one replaces its whole graph. Write a scratch
pad before the stack or graph that uses it. A scratch pad (and a script asset's `Graph`) is written whole for now: a
text with a bad line is refused naming every problem, and nothing changes.

```
in InputMap
get MapGet
  Source = in.Map
  Module.DataChannel: DataChannelRead [Tooltip="Channel to read."]
  Module.MaxRange: float = 20000
exec Op Util::ExecIndex
read CallDI DataChannelRead.Read(Origin: Position, Velocity: Vector)
  Target = get.Module.DataChannel
  Index = exec.Result
life CustomHlsl(Velocity: Vector, Range: float -> Lifetime: float)
  Velocity = read.Velocity
  Range = get.Module.MaxRange
  Hlsl = """
    Lifetime = min(2.0, Range / max(length(Velocity), 1.0));
  """
set MapSet
  Source = in.Map
  Particles.Position: Position = read.Origin
  Particles.Lifetime: float = life.Lifetime
out Output Module [Usage=ParticleSpawn]
  Output = set.Dest
```

- `<id> <type>` lines, pins indented: `Pin = <id>.<OutPin>` links, `Pin = literal` sets a value.
  The ids you write are kept; nodes made in the Niagara editor read as `n` plus a GUID prefix.
- `InputMap`: the parameter map coming in, output `Map`. `MapGet` reads parameters, `MapSet`
  writes them; both take the map on `Source`, and `MapSet` passes it on as `Dest`.
- Map pins are `Namespace.Name: type` lines. On `MapGet`, `= literal` is a module input's default
  and `[Tooltip="...", Default=User.X]` its tooltip and default binding; link from it by its full
  name, `get.Module.MaxRange`; a `MapGet` pin holds a default, never a link. On `MapSet`,
  `= <id>.Pin` or `= literal` is the value written.
  On the stack a module input drops `Module.`: `MaxRange`.
- `Output Module [Usage=EmitterUpdate|ParticleSpawn]`: the module's end, input `Output`, and the
  stack groups it may run in (`SystemSpawn`, `SystemUpdate`, `EmitterSpawn`, `EmitterUpdate`,
  `ParticleSpawn`, `ParticleUpdate`, `ParticleEvent`, `SimulationStage`).
- `Output DynamicInput` (one result) and `Output Function` declare results like map pins:
  `Result: float = sum.Result`. A dynamic input reads its inputs as a module does (`Module.Base` on a
  `MapGet`) and is used on the stack as `Input = Call ScratchPad:<Name>`; a function is called from a
  graph.
- `Call <script path>` calls a Niagara function script (or `Call ScratchPad:<Name>`).
- `CallDI <DataInterface>.<Function>`: a data interface function. Its interface pin is `Target`; a
  function that takes the parameter map has `Map` in and out. In parentheses, the outputs you add
  to a function that takes them (Data Channel `Read`, `Consume`): `Read(Origin: Position, ...)`.
- `Op Category::Name` with Niagara's internal names: `Numeric::Add`, `Numeric::Subtract`,
  `Numeric::Mul`, `Numeric::Div`, `Numeric::Length`, `Numeric::Normalize`, `Numeric::Lerp`,
  `Numeric::Clamp`, `Util::ExecIndex`; pins `A`, `B` (`C` the alpha of Lerp) to `Result`.
- `CustomHlsl(<inputs> -> <outputs>)` with its code as `Hlsl = """ ... """`.
- Any other node: its class without `NiagaraNode`, with `{json}` properties.
- `Kinds:<section>` (read-only: `Kinds:ScratchPad:<Name>`, `Kinds:Graph` on a script asset) lists
  these node types; `@CustomHlsl` shows one, `@<id>` a node's type and pins.
- Types: `bool int float Vector Vector2D Vector4 Position LinearColor Quat Matrix ID`, a data
  interface without `NiagaraDataInterface` (`DataChannelRead`), a Niagara struct without `Niagara`
  (`EmitterID`), an enum by path.
- Literals are Niagara's pin values as the read prints them (`20000`, `true`, `1,0,0`).
- A Vector linked into a Position pin gets the Convert node Niagara puts there; the text keeps the
  direct link.
- Pin names are written as reads print them (Niagara's names, spaces included; case aside); a near
  name (`EmitterID` for `Emitter ID`) is refused naming the pin. A bare `<id>` links a node's only
  output; with several, name one.

## Write reply

`Parameters` and `Emitters` write partially: a line with a problem (a type, a value, a data interface
property, a flag, an origin that does not load) is skipped and named under `not applied:`, and the other
lines are written. A skipped line keeps what it names as it is: the parameter or emitter of its name, and
the emitter its `was=` names, read even off a line that does not read otherwise; a kept emitter stays
where the line stands. These lines are skipped too:
- a line whose name an earlier line already has, also when that earlier line was skipped;
- a rename of an emitter a skipped line names, or onto its name;
- two lines with one `was=`, a line keeping a name another line renames away, a rename onto a name
  another line renames away: every line of the conflict;
- a new or renamed emitter under the name of an emitter that stays.

A text none of whose lines applies is refused and changes nothing.

The stack sections (`System`, `Emitter:<Name>`, an emitter asset's `Emitter`) write partially too: a
property, parameter, module, input, stage or renderer line with a problem (it does not read, an unknown
script, input, property or class, a value or flag that does not take, an inactive input, a module, input,
simulation stage or event handler named twice) is skipped and named, and its item stays as it is: the
module or stage it names (with all its inputs), the input it names, the renderer at its position. A
`SetParameters` target line whose value does not take adds or retypes no target. The lines under a skipped
module or stage header are skipped with it; a block of unknown or repeated header keeps every block it may
mean, and a line no name can be read from keeps everything of its kind no line names. A module, simulation
stage or event handler the emitter inherits that the text leaves out stays, named in the block. Kept items
keep their order among themselves; the written lines' items are placed around them in the text's order, and
a module Niagara will not move there (or that ends up out of the text's order) is skipped where it is. A text none of whose lines applies is refused
and removes nothing. When Niagara itself fails partway through a line, the whole write is undone and
refused. A stack or lightweight text with a line indented before any header is refused whole (no block to place
it in). A lightweight emitter's `Emitter:<Name>` writes partially the same way: a bad `Properties` line keeps
its property, a bad `Modules` line (one that does not read, a value that does not take, a module listed
twice) keeps its module as it is, on or off, a misspelt module name (or more text than the name before
its `{json}`) keeps every module no line names, a bad `Renderers` line keeps the renderer at its position.
Properties no line names go back to their defaults, and a misspelt property name names nothing, so the
property it meant goes back to its default too. A scratch pad or script `Graph` is written whole: Niagara imports the graph in one piece.

A write of any of these sections waits for the whole compile, CPU and GPU, and replies with
`compile:` when it has errors or warnings (a clean compile prints nothing), then `renderer` and `stack` lines (the issues the Niagara editor shows, with the fix it
offers); those two are not counted in the `compile:` verdict. The asset is saved even when the
compile fails. A scratch pad no stack uses is not compiled, so its errors show once a stack runs it.
A system open in the Niagara editor stays open: a write rebuilds that editor's view, as its own undo does
(the preview restarts, the stack's selection may reset).

## Verify

1. Read the `compile:`, `renderer` and `stack` lines of the last write (none of them: it compiled clean); fix every error before going on.
2. `spawn_actor` a `NiagaraActor` in view and set its component's asset to the system.
3. Feed what it reads: write Data Channel entries with `set_properties` or `run_python`, or set
   `User.*` parameters on the component.
4. `take_screenshot` (in PIE with `start_pie` when the effect needs game time) and look.
