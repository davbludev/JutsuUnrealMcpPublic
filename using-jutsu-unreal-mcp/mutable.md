# Mutable (Customizable Objects)

With the Mutable plugin enabled, a Customizable Object has a `Graph` section: its node graph as
text. Read it first; write back what you read with your changes. Works on UE 5.5-5.8; node types
and pin names are that engine's own, so the examples (UE 5.8) differ on 5.5-5.7
([earlier engines](#ue-55-57)). `create_asset` with class `CustomizableObject` makes an empty
object: its graph is the base `Object` node alone.

```
mesh SkeletalMesh {"SkeletalMesh":"/Engine/EngineMeshes/SkeletalCube.SkeletalCube"}
section SkeletalMeshSection {"Material":"/Game/M_Body.M_Body"}
  Mesh_Input_Pin = mesh
  Base {"UVLayoutMode":"Ignore"}
make SkeletalMeshMake_V2
  "LOD 0" = section
object SkeletalMeshObjectMake
  "Skeletal Mesh" = make
component ComponentSkeletalMesh {"ReferenceSkeletalMesh":"/Engine/EngineMeshes/SkeletalCube.SkeletalCube"}
  "Passthrough Skeletal Mesh" = object
n90974d Object
  Components = component
size EnumParameter {"Values":[{"Name":"Small"},{"Name":"Big"}],"ParameterName":"Size"}
small FloatConstant {"Value":0.5}
big FloatConstant {"Value":2}
pick Switch {"PinType":"float"}
  "Switch Parameter" = size
  Small = small
  Big = big
```

- `<id> <Type> {json}`. Existing ids are what read printed; a new node takes any unused name that
  is not `n` plus hex digits (those name existing nodes), and the reply's `ids:` line says which id it got.
- Types are the node class without `CustomizableObjectNode` / `CONode`; a class outside the palette
  (kept for older assets) reads under its full class name. `Kinds:Graph` (read-only) lists the
  palette's types, keyed ones with the values they take; `Kinds:Graph@Switch` one type with its pins,
  `Kinds:Graph@<id>` a node's. A keyed type's key is in its JSON (`Switch {"PinType":"float"}`, the
  type it switches: `float`, `mesh`, ...).
- JSON holds the node's editable properties that differ from a new node of its type, and the names
  the Mutable editor renames on the node itself: `ObjectName`, `ComponentName`, a `StaticString`'s
  `Value`.
- Inputs: `Pin = <id>`, or `<id>.<Output>` when the source has several outputs; a multi-link input
  (`Components`) lists its sources in order: `Components = a, b`. Pin names are Mutable's internal
  names (`Mesh_Input_Pin`, `"LOD 0"`); quote names with spaces.
- Pins that follow other links come by themselves: link `"Switch Parameter"` to an enum, and the
  switch gets one input per enum value (`Small`, `Big`) in the same write.
- Per-pin data: `Pin {json}` under the node (`Pin [out] {json}` for an output), for pins such as a
  section's material texture parameters (`Base` above, from the material's `Base` parameter).
- A node of another asset is `"<package>:<node id>"`, the id that asset's read prints.
- `Comment {"NodeComment":"..."}` and `Reroute` round-trip. The plugin lays out the graph; never place
  nodes.
- **Add pin** button pins are made by naming them (UE 5.8). Such a node's pins share one name, so the
  text names the first `Slot` and the next `"Slot #2"`, `"Slot #3"` ..., by a link or a data line; the
  write makes the pins up to the highest one named, before it links. Per-pin data goes on the
  pin's data line (`Pin {json}`, `Pin [out] {json}` for an output). Nodes: `ComponentSkeletalMesh`
  `"Overlay-or-Override"` inputs (`TargetMaterialSlotName`, Override slots), `SkeletalMeshBreak_V2`
  and `SkeletalMeshObjectBreak` `"Material Slot"` outputs (`TargetMaterialSlotName`),
  `SkeletalMeshModify` `Slot` inputs (`SlotName`), `MaterialBreak` `Parameter` outputs and
  `MaterialModify` `Parameter` inputs (`ParameterName`, `LayerIndex`), `MeshMorphStackDefinition`
  `Target` inputs (`TargetMorphName`). A Break or Modify pin takes the type of the pin it links
  (float, color, image, passthrough image), a pin with no link is a float.
  A name is needed for the compile: Mutable reports a slot or parameter pin without one. A write keeps
  pins the text does not name (their data goes back to defaults); remove a pin in the Mutable editor.
  A Break with one output is referenced bare (`brk`), with more `brk."Parameter #2"`.
  UE 5.8.4: a `SkeletalMeshBreak_V2` with a linked `"Material Slot"` output crashed the editor
  compiling (into a component slot); while the graph holds one, a write is saved but the reply says
  `compile: skipped` with a warning naming it. Unlink its outputs to compile.

A Modify feeding a component's override slot:

```
component ComponentSkeletalMesh {"ReferenceSkeletalMesh":"/Engine/EngineMeshes/SkeletalCube.SkeletalCube"}
  "Passthrough Skeletal Mesh" = object
  "Overlay-or-Override" = mod
  "Overlay-or-Override" {"TargetMaterialSlotName":"MaterialSlot"}
brk MaterialBreak
  Material = matc
  Parameter [out] {"ParameterName":"Gloss"}
mod MaterialModify
  Material = matc
  Parameter = brk
  Parameter {"ParameterName":"Gloss"}
  "Parameter #2" = tint
  "Parameter #2" {"ParameterName":"Tint"}
```

A mesh reaches the object through SkeletalMesh -> SkeletalMeshSection -> SkeletalMeshMake_V2 ->
SkeletalMeshObjectMake -> ComponentSkeletalMesh -> `Object.Components`. Give the section a
`Material` to compile without warnings.

More LODs: `"LODs":N` on the Make node (1-8, its `"LOD <n>"` inputs) and `NumLODs` on the object
node; the object gets the smaller of the two. Link the section into `"LOD 0"` alone: Mutable takes
each LOD of the section's mesh by itself, and LOD n also gets every section linked into
`"LOD 0"`-`"LOD n"`, so a link into `"LOD n"` adds sections from that LOD on.

```
make SkeletalMeshMake_V2 {"LODs":3}
  "LOD 0" = section
object SkeletalMeshObjectMake {"NumLODs":3}
  "Skeletal Mesh" = make
```

Without `LODs`, the node gets the inputs up to the highest one the text links.

### UE 5.5-5.7

- A mesh reaches the object through SkeletalMesh -> `Material` (the section, same pins and
  `Material`) -> `ComponentMesh` (its `"LOD 0"`) -> `Object.Components`:

  ```
  mesh SkeletalMesh {"SkeletalMesh":"/Engine/EngineMeshes/SkeletalCube.SkeletalCube"}
  section Material {"Material":"/Game/M_Body.M_Body"}
    Mesh_Input_Pin = mesh
  component ComponentMesh {"ReferenceSkeletalMesh":"/Engine/EngineMeshes/SkeletalCube.SkeletalCube"}
    "LOD 0" = section
  ```

  On UE 5.5 a `ComponentMesh` compiles only with a name: add `"ComponentName":"Body"` to its JSON.
- Switches are typed (`FloatSwitch`, ...; no `PinType`), their option pins numbered with a trailing
  space: `"Float 0 " = small`.
- UE 5.5 has no `StaticString`: names are the nodes' own values (`ComponentName`,
  `ParentComponentName`). It also names an `ExposePin`'s input `Object` whatever its type, and a
  `TextureParameter`'s output `Value`.

## Child objects and imported pins

A child object is its own Customizable Object attached to a group of its parent. Its base `Object`
node names the group, and its `ObjectName` is the option's name. Write the parent's group first:
the reply's `ids: <written>=<stored>` line gives the group's id, which the children name.

Parent `/Game/CO_Body` (its group read back as `n0f7f32`):

```
group ObjectGroup {"GroupType":"COGT_ONE","GroupName":"Hat"}
nfd68f9 Object
  Components = component
  Children = group
```

Child `/Game/CO_Cap`, its whole graph:

```
n679599 Object {"ObjectName":"Cap","ParentObjectGroupId":"/Game/CO_Body:n0f7f32"}
```

- On UE 5.8 a child adds a mesh to its parent's component through a merge modifier, matched by
  the string on the parent `SkeletalMeshObjectMake`'s `Name` pin (link a `StaticString` there; left
  unlinked, the child compiles clean and adds nothing). Parent, its existing `SkeletalMeshObjectMake`
  under the id its read printed:

  ```
  name StaticString {"Value":"Body"}
  n2c41e7 SkeletalMeshObjectMake
    Name = name
    "Skeletal Mesh" = n5b0e19
  ```

  Child, after its own SkeletalMesh -> SkeletalMeshSection -> `make SkeletalMeshMake_V2` chain:

  ```
  target StaticString {"Value":"Body"}
  add ModifierMutableSkeletalMeshMerge
    "Skeletal Mesh Name" = target
    Added = make
  n679599 Object {"ObjectName":"Cap","ParentObjectGroupId":"/Game/CO_Body:n0f7f32"}
    Modifiers = add
  ```
- On UE 5.5-5.7 the child adds a component to the parent's `ComponentMesh` of that name, on its
  `Object`'s `Components` (the parent's component needs the name, or the child's compile reports
  `Can not find parent Mesh Component Body.`). UE 5.6 and 5.7, after the child's own SkeletalMesh ->
  `section Material` chain:

  ```
  target StaticString {"Value":"Body"}
  add ComponentMeshAddTo
    "LOD 0" = section
    "Component Name" = target
  n679599 Object {"ObjectName":"Cap","ParentObjectGroupId":"/Game/CO_Body:n0f7f32"}
    Components = add
  ```

  UE 5.5: `add ComponentMeshAddTo {"ParentComponentName":"Body"}` with its `"LOD 0"` link, no
  `StaticString`. On 5.6 and 5.7 the parent's `ComponentMesh` takes its name from a `StaticString`
  on its `Name` pin; on 5.5 from its `ComponentName`.
- `COGT_ONE` makes the group one enum parameter (`Hat`) whose values are its children's names;
  the default `COGT_TOGGLE` makes one bool per child, `COGT_ONE_OR_NONE` adds `None`.
- An `ExternalPin` imports what an `ExposePin` of another object of the same hierarchy exposes:
  `imported ExternalPin {"PinType":"mesh","ExternalObjectNodeId":"/Game/CO_Body:nab778d"}`. Both
  take the same `PinType`.
- A write that removes or replaces a group or `ExposePin` still succeeds and warns with the objects
  that reference it: read their `Graph` and write their references again.

## Macros

A Macro Library (UE 5.6 and later) has one `Macro:<Name>` section per macro, in the same graph
text. Its `Inputs` and `Outputs` nodes list the macro's variables as `Name: type`:

```
in Inputs(Mesh: mesh)
section SkeletalMeshSection {"Material":"/Game/M_Body.M_Body"}
  Mesh_Input_Pin = in
make SkeletalMeshMake_V2
  "LOD 0" = section
object SkeletalMeshObjectMake
  "Skeletal Mesh" = make
component ComponentSkeletalMesh {"ReferenceSkeletalMesh":"/Engine/EngineMeshes/SkeletalCube.SkeletalCube"}
  "Passthrough Skeletal Mesh" = object
out Outputs(Component: component)
  Component = component
```

- Writing a new `Macro:<Name>` makes the macro; empty text removes it. `create_asset` with class
  `CustomizableObjectMacroLibrary` makes a library holding one empty macro.
- Keep both `Inputs` and `Outputs` lines (any id). Types: `object`, `component`, `material` (a mesh
  section), `modifier`, `mesh`, `image`, `passThroughImage`, `projector`, `groupProjector`, `color`,
  `float`, `enum`, `stack`, `materialAsset`, `poseAsset`, `transform`, `string`. With several
  inputs, link one as `<inputs id>.<Name>`.
- An object runs a macro through `use MacroInstance {"ParentMacro":"/Game/ML_Parts:Body"}`; its
  pins are the macro's variable names (`Mesh = mesh`, `Components = use`).
- A library write compiles nothing and warns with the objects using it. Renaming a variable drops
  the links to it.

## Compile

Every write that changes the graph compiles the object (a child object from its root) and the reply
ends with its result when it was not clean (a clean compile prints nothing):

```
compile: 1 error(s), 1 warning(s)
  warning n4ceffd: Could not generate a mesh section because it didn't have a material selected. Please assign one and recompile.
  error n1fc235: The clip mesh with mesh node requires an input clip mesh.
```

- Each Mutable message starts with the ids of the nodes it names (`<package>:<id>` for a node of
  another asset). The write is kept and saved with compile errors too: fix the named nodes and write
  again.
- Inputs a node can do without stay unlinked without a message; a node that needs one (a clip
  modifier's clip mesh) reports an error naming it.
- `compile_assets` with a Customizable Object path compiles it again and returns the same lines.

## Add-on plugins

Enabled add-ons put their nodes in the same text:

```
factor FloatParameter {"ParameterName":"Noise"}
noise ExternalOperation {"OperationInstancedStruct":{"struct":"/Script/MutableExtensionExample.MeshNoise","Seed":7}}
  Mesh = mesh
  Factor = factor
groom GroomConstant {"GroomData":{"ComponentName":"Hair","GroomAsset":"/Game/Hair/G_Bob.G_Bob"}}
n90974d Object
  Components = component
  "/Script/HairStrandsMutable.Default__HairStrandsMutableExtension__Grooms" = groom
```

- An `ExternalOperation` or `ExternalTypeParameter` (UE 5.8 only) is chosen by its `struct`; the
  struct's other fields (`Seed`, a sphere's `W`) are that node's values, and a field left out goes
  back to its default.
- Give an external operation a parameter upstream of at least one input (as `Factor` above): Mutable
  on UE 5.8 crashes the editor compiling one whose inputs are all constants, so until each has one the
  write is saved with `compile: skipped`.
- RigLogicMutable (UE 5.5-5.7): a `DNAConstant` on the base `Object` node's
  `"/Script/RigLogicMutable.Default__RigLogicMutableExtension__DNA"` input. On 5.6 and 5.7 a
  `SkeletalMesh` without DNA crashes the editor's compile, so such a write is saved with
  `compile: skipped`. It picks its component by `ComponentName`, on 5.5 by `ComponentIndex`.
- MutablePopulation's Population and Population Class assets have no graph: write their `Properties`.

## Instances

`create_asset` with `class` `CustomizableObjectInstance` and `parent` the object's path makes an
instance. Its `Parameters` section holds the state and every parameter of the object:

```
State = "Default"
Body = "/Engine/EngineMeshes/SkeletalCube.SkeletalCube"
Gloss = 0.25
Hat = "Cap"
Tint = {"R":1,"G":0.5,"B":0,"A":1}
```

- Values by parameter type: an enum (a group's, an `EnumParameter`'s) by option name, a float or a
  bool as JSON, a colour as `{"R","G","B","A"}`, a mesh, texture or material by asset path, a
  projector or transform as a JSON object of its fields.
- A parameter left out goes back to its default; `State` left out goes back to the first state.
- A parameter named `State` is written `"State" = ...`.
- Only parameters the object's compiled data has are listed: a parameter node that feeds nothing the
  object builds is not one. Reading compiles an object never compiled.
- On UE 5.5 and 5.6 skeletal mesh and material parameters are not listed: those engines' instances
  have no functions to read or set them.
