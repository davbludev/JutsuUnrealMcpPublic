# Niagara as text

Open this page only for Niagara work. The general rules of `SKILL.md` apply.

## Scratch pads

A Niagara system's scratch-pad scripts are sections: `ScratchPad:<Name>` for the system's own,
`ScratchPad:<Emitter>/<Name>` for one emitter's. Writing a name that does not exist creates a module
scratch pad; writing an existing one replaces its whole graph. Write a scratch pad before the stack
that uses it.

```
in InputMap
get MapGet
  Source = in.Map
  Module.DataChannel: DataChannelRead [Tooltip="Channel to read; link it to User.TracerChannel."]
  Module.MaxRange: float = 20000
  Engine.Emitter.ID: EmitterID
exec Op Util::ExecIndex
slot CallDI DataChannelRead.GetNDCSpawnData
  Target = get.Module.DataChannel
  Emitter ID = get.Engine.Emitter.ID
  Spawned Particle Exec Index = exec.Result
read CallDI DataChannelRead.Read(Origin: Position, Velocity: Vector)
  Target = get.Module.DataChannel
  Index = slot.NDC Index
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
  `ParticleSpawn`, `ParticleUpdate`, `ParticleEvent`, `SimulationStage`). A new scratch pad is a
  module; one made in the editor as a dynamic input or function keeps its kind.
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

Until stacks are text, a system scratch pad goes on a stack through `Document` with
`"create": {"script": "/Game/VFX/NS_Tracers.NS_Tracers:ReadTracer"}`.

## Write reply

A scratch-pad write waits for the whole compile, CPU and GPU, then replies like a Blueprint write:
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
