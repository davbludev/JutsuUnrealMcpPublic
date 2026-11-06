# PCG graphs

## Graph

Build and rewire a PCG graph (`create_asset` class `PCGGraph`) in its `Graph` section. Read it first: a new graph
reads `Input Input` and `Output Output`, the graph's own nodes, which every text keeps.

1. Find kinds: `read_asset section=Kinds:Graph@sampler` lists matching kinds, then `Kinds:Graph@SurfaceSampler`
   one kind with its pins (`in`/`out`) and settings (type, default, enum entries).
2. Write the whole graph. A landscape scatter:

```
Input Input
landscape GetLandscape
sampler SurfaceSampler
  Surface = landscape
  PointsPerSquaredMeter = 0.5
filter DensityFilter [title="Keep dense"]
  In = sampler
  LowerBound = 0.2
spawner StaticMeshSpawner
  In = filter
Output Output
  Out = spawner
```

- A kind is the settings class without `PCG` and `Settings` (`SurfaceSampler`); the class name and the palette
  title without spaces work too.
- `<pin> = <id>` links the node's only output, `<id>.<output>` names one; quote a pin name with spaces only where
  the line needs it (`Primary Source = a` reads as written).
- `<setting> = <value>`: JSON numbers, bools, quoted strings and object paths, a struct as an object of the members
  to change, an enum by its entry's name (`CoordinateSpace = World`). A setting with an override pin also takes a
  link (`PointsPerSquaredMeter = attrs`).
- The text is the resulting graph: a node, link or setting left out is removed or reset, so rewiring an input is
  writing its new source. `[title="..."]` sets a node's title.
- Ids you choose (`sampler`) are kept, also on a copy made with `duplicate_asset`; a node made elsewhere reads as
  `n` plus hex.
- Dynamic inputs: a link to the next one adds it (Merge, Gather, Union, Merge Attributes from UE 5.6 `In2`, `In3`;
  Outer Intersection `Source2` on every lane); a later one adds those between. Pins are never removed.
- Instanced settings (a spawner's mesh selector) are setting lines too (next section).

### Instanced settings

A setting holding a subobject (Static Mesh Spawner `MeshSelectorParameters` and `InstanceDataPackerParameters`,
Match And Set's `MatchAndSetInstance`) is one line: a JSON object of the subobject's members that differ from a new
one (`{}` for none). Struct array entries list their changed members too. Two weighted meshes:

```
spawner StaticMeshSpawner
  In = filter
  MeshSelectorParameters = {"MeshEntries":[{"Descriptor":{"StaticMesh":"/Game/Rock.Rock"},"Weight":3},{"Descriptor":{"StaticMesh":"/Game/Bush.Bush"}}]}
```

- Its class follows the node's type setting (`MeshSelectorType`, `InstanceDataPackerType`): change both in one text,
  `MeshSelectorType = "/Script/PCG.PCGMeshSelectorByAttribute"` with `MeshSelectorParameters = {"AttributeName":"Mesh"}`.
  A subobject without a type setting names its class with `"class"`.
- `Kinds:Graph@StaticMeshSpawner` lists the subobject's class and members; an unknown member is refused with them.
- Left out, the subobject is a new one of its type setting's class (`{}`; none while the type is None); without a
  type setting, a new node's.

### Subgraph and Loop nodes

`Subgraph = "<graph path>"` names the graph (or graph instance) a `Subgraph` or `Loop` node runs; the node gets
that graph's Input and Output pins in the same write, so the write can link them:

```
sub Subgraph
  Points = grid
  Subgraph = "/Game/PCG/PCG_Rows.PCG_Rows"
loop Loop
  Points = sub
  Subgraph = "/Game/PCG/PCG_Rows.PCG_Rows"
```

- A link from a new subgraph node names its output when the subgraph's output is not `Out` (`sub.Points`).
- Leaving the line out clears the subgraph; the node is back to `In` and `Out`.
- Every write of the graph brings its Subgraph and Loop nodes up to their subgraphs: after changing a pin or its
  Usage in the subgraph, write the referencing graph (its read text as it is is enough). `Kinds:Graph@<node id>`
  shows a pin's Usage (`in Points: Any (loop)`).
- Each user parameter of the subgraph is an input named after it: `Density = 0.5` overrides it on this node (the
  value spelled as on a `Parameter` line), `Density = attrs` links its override pin. Leaving the line out uses the
  subgraph's value. `Kinds:Graph@<node id>` lists them (`in Density: float (subgraph parameter ...)`).

### Parameters

The graph's user parameters are `Parameter <name>: <type> [= <default>]` lines above the nodes; a Get Parameter
node names one, and its output carries it:

```
Parameter Density: float = 0.5
Parameter Rows: int
Input Input
density UserParameterGet Density
sampler SurfaceSampler
  PointsPerSquaredMeter = density
...
```

- Types are the Variables spellings (`float`, `double`, `int`, `name`, `Vector`, `StaticMesh`, `soft<StaticMesh>`,
  `class<Actor>`, `T[]`, `set<T>`; no `text`, no `map`). A default left out is the type's zero value.
- The lines are the resulting set: a parameter left out is removed, so remove its Get Parameter nodes with it.
  `[was="Old"]` at the end of a line renames a parameter; its Get Parameter nodes, written with the new name, stay
  with their links. Name a parameter exactly as declared (letter case too).

A PCG graph has no `Document` section: asking for it is refused and names `Graph`.
