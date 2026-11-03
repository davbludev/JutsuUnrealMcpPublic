# Motion Matching: Pose Search schemas and databases

Needs the PoseSearch plugin enabled in the project; without it the sections below do not exist.

Build the assets in this order, all through `create_asset`:

```
create_asset(path="/Game/MM/PSS_Locomotion", class="PoseSearchSchema", parent="/Game/Characters/SK_Hero")
create_asset(path="/Game/MM/PSD_Locomotion", class="PoseSearchDatabase", parent="/Game/MM/PSS_Locomotion")
```

- A schema's `parent` is its skeleton; the factory adds the default channels. A database's `parent` is
  its schema (`options` {"TargetSchema": path} does the same).
- A schema is plain properties. `read_asset(schema, "Properties")` shows `Channels` as instanced
  objects (`{"class": "...", members}`), `SampleRate`, the mirror table and the rest; `write_asset`
  with that text changes them, and Pose Search recomputes the schema. Remove or reorder a channel by
  editing the `Channels` array.

## Database animation list: `Assets`

The list of animations is a private property: `Properties` and `get_properties` do not show it. Read and
write it as section `Assets`, one line per entry:

```
/Game/Anim/A_Idle.A_Idle
/Game/Anim/A_Run.A_Run {"bDisableReselection":true,"MirrorOption":"MirroredOnly","SamplingRange":{"Min":0.1,"Max":0.5}}
/Game/Anim/BS_Walk.BS_Walk {"bUseSingleSample":true,"BlendParamX":1}
```

- The asset's object path, then (when anything differs from a new entry) a JSON object of the settings:
  `bEnabled`, `bDisableReselection`, `MirrorOption` (`UnmirroredOnly`, `MirroredOnly`,
  `UnmirroredAndMirrored`; mirrored needs a mirror table in the schema), `SamplingRange` (`{"Min":0,
  "Max":0}` is the whole animation), and for a Blend Space `bUseSingleSample`, `bUseGridForSampling`,
  `NumberOfHorizontalSamples`, `NumberOfVerticalSamples`, `BlendParamX`, `BlendParamY`.
- The text is the whole list: lines left out are removed, and a line with no settings puts that entry's
  back to the defaults. Animation sequences, blend spaces, composites, montages and multi anim assets
  all take the same line; the plugin picks the entry kind from the asset's class on every engine.
- `edit_asset(db, "Assets", old_text, new_text)` changes one line's settings.

## Chooser tables: `Table`

Needs the Chooser plugin. A Chooser Table picks an animation (or any asset) from rows by testing the
columns. `create_asset(path, class="ChooserTable")` makes an empty one; `read_asset(table, "Table")` and
`write_asset` do the rest:

```
Column /Script/Chooser.FloatRangeColumn {"InputValue":{"struct":"/Script/Chooser.FloatContextProperty","Binding":{"PropertyBindingChain":["Speed"]}}}
Column /Script/Chooser.BoolColumn
Row /Game/Anim/A_Idle.A_Idle {"cells":[{"Min":0,"Max":1},null]}
Row /Game/Anim/A_Walk.A_Walk {"disabled":true,"cells":[{"Min":1,"Max":5},null]}
Row evaluate /Game/Anim/CT_Run.CT_Run {"cells":[{"Min":5,"bNoMax":true},null]}
Fallback /Game/Anim/A_Idle.A_Idle
```

- A column is its struct plus the settings that differ (the input binding is `InputValue`; read a table you
  built in the editor to see the binding shape). Its cells are not on the column line: each row's `cells`
  holds one value per column, `null` for the column's default.
- A row's result is an asset path, `soft <path>`, `evaluate <chooser path>`, `nested <name>` or `None`.
  `nested Branch` makes a chooser inside the table; its own columns and rows are section `Table:Branch`.
- Remove a row by leaving its line out; every column is resized with the rows. Rows are told apart by
  position.
- `Properties` holds the result type, result class and parameters (context objects).

## Proxy tables: `Entries`

A Proxy Asset is a name an animation graph looks up; a Proxy Table maps it to a result. Make
`ProxyAsset`s and a `ProxyTable` with `create_asset`, then:

```
Entry /Game/Anim/PA_Locomotion.PA_Locomotion evaluate /Game/Anim/CT_Run.CT_Run
Entry /Game/Anim/PA_Idle.PA_Idle /Game/Anim/A_Idle.A_Idle
```

Results are written as in a row, except `nested`; options `{"key":...,"outputs":[...]}` follow the result.

## Anim Blueprint nodes

The nodes are ordinary anim graph text ([animation.md](animation.md)): `MotionMatching`,
`PoseSearchHistoryCollector` (Pose History), `ChooserPlayer`; `MotionMatchingInteraction` exists on UE 5.5-5.7 only. A pose chain with a thread-safe function and a
property access pin, compiling clean:

```
mm MotionMatching {"Node":{"OnMotionMatchingStateUpdated":{"FunctionName":"UpdateMatching"}}}
  Database = /Game/MM/PSD_Locomotion.PSD_Locomotion
  BlendTime = @Speed
hist PoseSearchHistoryCollector
  Source = mm.Pose
out Root
  Result = hist.Pose
```

- `Function:UpdateMatching` is `e FunctionEntry() [ThreadSafe]` (node functions run on worker
  threads).
- `Speed: float` is an Anim Blueprint variable (`Variables` section); `BlendTime = @Speed` binds the pin to it.
- The history collector generates the trajectory itself; a trajectory you supply comes from engine functions
  that differ by lane: UE 5.5 `PoseSearchGenerateTrajectory` / `GetTrajectorySampleAtTime`; UE 5.8
  `PoseSearchGenerateTransformTrajectory` / `GetTransformTrajectorySampleAtTime` (UE 5.7 has both).
