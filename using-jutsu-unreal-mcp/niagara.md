# Niagara as text

Open this page only for Niagara work. The general rules of `SKILL.md` apply.

## Sections of a system

| Section | Holds |
|---|---|
| `Parameters` | `User.*` parameters, one per line; `System.*` ones the parameter panel declares |
| `Emitters` | one line per emitter, in order |
| `System` | the `SystemSpawn` and `SystemUpdate` stacks |
| `Emitter:<Name>` | the emitter's `Properties`, `Parameters` (`Emitter.*`), four stacks, `Renderers`; a lightweight one's `Properties`, `Modules`, `Renderers` |
| `ScratchPad:<Name>`, `ScratchPad:<Emitter>/<Name>` | one scratch-pad graph (below) |
| `Properties` | the system's own settings, as for any asset |

Each write makes the section match the text: what it leaves out is removed or reset. Build a system
in this order: `Parameters`, `Emitters`, scratch pads, then `System` and `Emitter:` stacks.

```
User.TracerColor: LinearColor = (R=6,G=3,B=0.8,A=1)
User.TracerWidth: float = 3
```

- Parameter lines are `Namespace.Name: type = value`; a data interface is its class without
  `NiagaraDataInterface` and its changed properties as JSON. Types are those of scratch pads.
  `System.*` and `Emitter.*` lines declare a parameter without a value (modules write it).
- `Emitters` lines are `Name [flags]`. A new name takes one origin: `[from=<emitter asset>]` (a
  template under `/Niagara/DefaultAssets/Templates/Emitters/`), `[empty]` (Niagara's Minimal emitter)
  or `[lightweight]`; on an existing name these are ignored. `[disabled]`
  disables, leaving it out enables; `[was="Old"]` renames; a left-out line removes the emitter; the
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
- Under a module, only overridden inputs, by the name Niagara shows (spaces included). A value is a
  literal (`2.5`, `true`, `(R=1,G=0,B=0,A=1)`, an enum entry's name), a linked parameter
  (`User.TracerColor`, `Particles.Gravity`), `Call <dynamic input script or ScratchPad section>` with
  its own inputs indented under it, a data interface's changed properties as `{json}` (`{}` for its
  defaults), or `Hlsl "<expression>"`. An input left out returns to the module default.
- A Data Channel read takes its channel as the module input's `{json}` value: linked to a `User.*`
  data interface it never spawns (engine behaviour). Read the spawned particle's entry by
  `Op Util::ExecIndex`, not `GetNDCSpawnData`, which only the spawning module's interface answers.
- `Properties` are `Name = <json>` lines of the emitter's settings (`SimTarget`, `bLocalSpace`,
  `CalculateBoundsMode`, `FixedBounds`, ...). `Renderers` are `Class {json}` lines (`Sprite`,
  `Ribbon`, `Mesh`, `Light`, ...); a renderer is known by its position. Its attribute bindings are
  not text yet and stay as they are.

```
Properties
  EmitterState = {"LoopBehavior": "Once"}
  SpawnInfos = [{"Type": "Burst", "Amount": {"Min": 12, "Max": 12}}]

Modules
  InitializeParticle {"LifetimeDistribution": {"Mode": "UniformRange", "ChannelConstantsAndRanges": [0.1, 0.25]}}
  GravityForce {}
  SolveVelocitiesAndForces {}

Renderers
  Sprite {"Material": "/Niagara/DefaultAssets/DefaultSpriteMaterial.DefaultSpriteMaterial"}
```

- A lightweight emitter has `Properties` (its settings: `EmitterState`, `SpawnInfos`, `FixedBounds`,
  ...), `Modules` and `Renderers`. Its modules are fixed: a listed one is on, with its changed
  properties as `{json}` (class without `NiagaraStatelessModule_`); one left out is off, its settings
  kept. `InitializeParticle` and `SolveVelocitiesAndForces` are always on.
- A distribution is its `Mode` with `ChannelConstantsAndRanges` (`UniformRange` one range for all
  channels, `NonUniformRange` per channel); its `Min`, `Max` and `Values` follow from them (engine).

## Scratch pads

A Niagara system's scratch-pad scripts are sections: `ScratchPad:<Name>` for the system's own,
`ScratchPad:<Emitter>/<Name>` for one emitter's. Writing a name that does not exist creates a scratch
pad of the kind its `Output` names; writing an existing one replaces its whole graph. Write a scratch
pad before the stack or graph that uses it.

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
  name, `get.Module.MaxRange`. On `MapSet`, `= <id>.Pin` or `= literal` is the value written.
  On the stack a module input drops `Module.`: `MaxRange`.
- `Output Module [Usage=EmitterUpdate|ParticleSpawn]`: the module's end, input `Output`, and the
  stack groups it may run in (`SystemSpawn`, `SystemUpdate`, `EmitterSpawn`, `EmitterUpdate`,
  `ParticleSpawn`, `ParticleUpdate`, `ParticleEvent`, `SimulationStage`).
- `Output DynamicInput` (one result) and `Output Function` declare results like map pins:
  `Result: float = sum.Result`. A dynamic input reads its inputs as a module does (`Module.Base` on a
  `MapGet`) and is used on the stack as `Input = Call ScratchPad:<Name>`; a function is called from a
  graph. The kind is fixed when the scratch pad is first written.
- `Call <script path>` calls a Niagara function script (or `Call ScratchPad:<Name>`).
- `CallDI <DataInterface>.<Function>`: a data interface function. Its interface pin is `Target`; a
  function that takes the parameter map has `Map` in and out. In parentheses, the outputs you add
  to a function that takes them (Data Channel `Read`, `Consume`): `Read(Origin: Position, ...)`.
- `Op Category::Name` with Niagara's internal names: `Numeric::Add`, `Numeric::Subtract`,
  `Numeric::Mul`, `Numeric::Div`, `Numeric::Length`, `Numeric::Normalize`, `Numeric::Lerp`,
  `Numeric::Clamp`, `Util::ExecIndex`; pins `A`, `B` (`C` the alpha of Lerp) to `Result`.
- `CustomHlsl(<inputs> -> <outputs>)` with its code as `Hlsl = """ ... """`.
- Any other node: its class without `NiagaraNode`, with `{json}` properties.
- Types: `bool int float Vector Vector2D Vector4 Position LinearColor Quat Matrix ID`, a data
  interface without `NiagaraDataInterface` (`DataChannelRead`), a Niagara struct without `Niagara`
  (`EmitterID`), an enum by path.
- Literals are Niagara's pin values as the read prints them (`20000`, `true`, `1,0,0`).
- A Vector linked into a Position pin gets the Convert node Niagara puts there; the text keeps the
  direct link.
- Pin names match with or without spaces (`EmitterID` finds `Emitter ID`); reads print them as
  Niagara names them.

## Write reply

A write of any of these sections waits for the whole compile, CPU and GPU, then replies like a Blueprint write:
`compile: ok`, `compile: ok with warnings` or `compile: N error(s)`, then `  error <where>: message`
lines. `<where>` is the scratch pad and node id (`ScratchPad:ReadTracer read`), the section and stack
module (`Emitter:Tracers SpawnRate`), or the section alone. Each renderer adds its missing particle
attributes and feedback (`Emitter:Tracers renderer 0 (Sprite)`). The asset is saved even when the
compile fails. A scratch pad no stack uses is not compiled, so its errors show once a stack runs it.

## Verify

1. Read the `compile:` lines of the last write; fix every error before going on.
2. `spawn_actor` a `NiagaraActor` in view and set its component's asset to the system.
3. Feed what it reads: write Data Channel entries with `set_properties` or `run_python`, or set
   `User.*` parameters on the component.
4. `take_screenshot` (in PIE with `start_pie` when the effect needs game time) and look.
