# Materials

Sections: Material and Material Function `Graph` and `Properties`; Material Instance `Parameters` and
`Properties`.

## Graph

```
rough ScalarParameter {"ParameterName":"Roughness","DefaultValue":0.4}
tint VectorParameter {"ParameterName":"Tint","DefaultValue":{"R":0.8,"G":0.2,"B":0.1,"A":1}}
mix LinearInterpolate
  A = tint.RGB
  B = 0.5
  Alpha = rough
Output
  BaseColor = mix
  Roughness = rough
```

- **Node types** are expression class names (`LinearInterpolate`, `ShadowReplace`); a palette caption
  or one-word keyword (`Lerp`, `ShadowPassSwitch`) also resolves where it is unique, and reads print
  the class. `Kinds:Graph@<kind or node id>` gives one kind's inputs, values and outputs.
- **Constants vs links.** `Input = <id>` links; `B = 0.5` sets the value an unlinked input takes
  (Multiply's `ConstB`), only where `Kinds:Graph@<kind>` shows a value. Everywhere else, and in the
  `Output` block, link a `Constant` or `Constant3Vector` node.
- **Outputs.** `<id>` is the node's first output; name another as `<id>.R`, `<id>.RGB`, `<id>.Result`.
  A texture sample's pins are `RGB`, `R`, `G`, `B`, `A`, `RGBA`.
- **Input names** are the editor label or the property name (Noise `Position`), whichever you read.
- **Graph writes partially.** A line with a problem (an unknown kind, property, flag, input or output) is skipped and
  named under `not applied:`, with the lines under its node and every line linking to it; the rest is written. The node
  of a skipped line's id stays as it was, links and values included, and so do an input or `Output` slot whose line was
  skipped. The material compiles on what was written; compile errors do not undo it. Still refused whole: removing or
  changing the kind of an expression loaded at Editor startup, and a texture sampler type problem on a node the text does
  not change.

### Function

A function has no `Output` block: its outputs are `FunctionOutput` nodes, its inputs `FunctionInput`.
A material calls it with a `MaterialFunctionCall` that takes inputs by name and links `call.<Output>`.

```
in FunctionInput {"InputName":"Value","InputType":"FunctionInput_Scalar"}
twice Multiply
  A = in
  B = 2
out FunctionOutput {"OutputName":"Result"}
  Input = twice
```

```
call MaterialFunctionCall {"MaterialFunction":"/Game/MF_Twice.MF_Twice"}
  Value = rough
Output
  Roughness = call.Result
```

A function write recompiles the loaded materials that use it and lists their errors (when many fail, the first 3, then the others' paths: `compile_assets` lists theirs). Material Layer and Material Layer Blend are functions: a layer's output takes
`MakeMaterialAttributes`, a blend's inputs are `FunctionInput_MaterialAttributes` (`Top`, `Bottom`).

### Other nodes

`SetMaterialAttributes` and `GetMaterialAttributes` get the attribute pins you name, as the editor's "+" does:
`BaseColor = tint` on a Set links (and adds) its input, `get.Roughness` adds the Get's output. An unknown name is
refused with the valid ones; pins stay once added, and their GUID arrays are not JSON.

```
set SetMaterialAttributes
  MaterialAttributes = make
  BaseColor = tint
get GetMaterialAttributes
  MaterialAttributes = set
Output
  Roughness = get.Roughness
```

Named Reroute usages link `Declaration = <declaration id>`; `CustomPrimitiveData` is a `ScalarParameter` or
`VectorParameter` with `"bUseCustomPrimitiveData":true`.

## Properties

Settings live in `Properties` (`BlendMode`, `ShadingModel`, `MaterialDomain`, `TwoSided`,
`bUseMaterialAttributes`, usage flags). The section is whole: a setting you leave out returns to its
default, engine-set `bUsedWith...` flags included, so read, change the lines, write all of them back. The settings are applied
together and compiled once, so a text with a bad line is refused whole, naming every problem. A Material Instance's
`Properties` write partially, as the generic `Properties` do (SKILL.md).
An open Material Editor shows the change on 5.8; on 5.5-5.7 the editor window is
closed (it declines when it has unsaved edits). `set_properties` on the live material recompiles once per call; its reply's `followUps` carries the compile line.

## Instance `Parameters`

```
Roughness = 0.75
Tint = {"R":1,"G":0.5,"B":0.25,"A":1}
Base = "/Game/T_Rock.T_Rock"
Fancy = true
AOChannel = {"R":false,"G":true,"B":false,"A":false}
Layer[0].LayerRough = 0.9
Blend[0].BlendAlpha = 0.25
# Tint2 = {"R":1,"G":1,"B":1,"A":1} (inherited)
```

Scalar (a number), vector (`{"R":..}` or `[r,g,b,a]`), texture (asset path or `None`), static switch
(`true`/`false`) and static component mask (`{"R":true,"G":false,..}`, channels left out off, or
`[r,g,b,a]` booleans; at least one channel on, and only channels the masked input has). Only
overridden parameters are lines; `# ... (inherited)` lines show what the others hold and may be kept
or dropped. A parameter the text leaves out loses its override. `Parameters` writes partially: a line with a
wrong value is skipped and its parameter keeps its override; a misspelled name is skipped too, and the parameter you meant counts
as left out and loses its override. A material layer
stack's parameters are `Layer[i].Name` and `Blend[i].Name` (the layer or blend index in the stack, as
the read prints them); a stack comes from the parent material's `MaterialAttributeLayers` node.

A `Parameters` write that changes a static switch or static mask compiles the instance's rebuilt permutation,
waiting for its shaders as a material write does, and lists its errors under a reply that stays ok (an editor
without a renderer compiles no shaders, so lists none). Other `Parameters` writes compile nothing, and a parent
instance's write does not compile its children's permutations. `compile_assets` on the instance compiles its own
permutation (when it overrides a static switch, static mask or base property), lists its errors and fails on
them; an instance without one renders with another asset's shaders (the nearest parent instance with its own
permutation, else the root material), and the reply names that asset to compile.
