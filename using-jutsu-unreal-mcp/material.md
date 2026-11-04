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

A function write recompiles the loaded materials that use it and lists their errors. Material Layer and Material Layer Blend are functions: a layer's output takes
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
default, engine-set `bUsedWith...` flags included, so read, change the lines, write all of them back.
An open Material Editor shows the change on 5.8; on 5.5-5.7 the editor window is
closed (it declines when it has unsaved edits). `set_properties` on the live material recompiles once per call; its reply's `followUps` carries the compile line.

## Instance `Parameters`

```
Roughness = 0.75
Tint = {"R":1,"G":0.5,"B":0.25,"A":1}
Base = "/Game/T_Rock.T_Rock"
Fancy = true
Layer[0].LayerRough = 0.9
Blend[0].BlendAlpha = 0.25
# Tint2 = {"R":1,"G":1,"B":1,"A":1} (inherited)
```

Scalar (a number), vector (`{"R":..}` or `[r,g,b,a]`), texture (asset path or `None`) and static switch
(`true`/`false`). Only overridden parameters are lines; `# ... (inherited)` lines show what the others
hold and may be kept or dropped. A parameter the text leaves out loses its override. A material layer
stack's parameters are `Layer[i].Name` and `Blend[i].Name` (the layer or blend index in the stack, as
the read prints them); a stack comes from the parent material's `MaterialAttributeLayers` node.
