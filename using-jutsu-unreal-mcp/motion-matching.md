# Motion Matching: Pose Search schemas and databases

Needs the PoseSearch plugin enabled in the project; without it the sections below do not exist.

Build the assets in this order, all through `create_asset`:

```
create_asset(path="/Game/MM/PSS_Locomotion", class="PoseSearchSchema", parent="/Game/Characters/SK_Hero")
create_asset(path="/Game/MM/PSD_Locomotion", class="PoseSearchDatabase", parent="/Game/MM/PSS_Locomotion")
```

- A schema's `parent` is its skeleton; the factory adds the default channels. A database's `parent` is
  its schema (`options` {"TargetSchema": path} does the same). Without them the factory makes nothing
  and the refusal names the setting that is unset.
- A schema is plain properties. `read_asset(schema, "Properties")` shows `Channels` as instanced
  objects (`{"class": "...", members}`), `SampleRate`, the mirror table and the rest; `write_asset`
  with that text changes them, and Pose Search recomputes the schema. Remove or reorder a channel by
  editing the `Channels` array; writing back what was read is `No change.`

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
- Unknown setting names are refused with the valid ones listed.

## Indexing

A database builds its search index in the background. A changing write requests a build; read
`Details` to see `Index building` turn into `Index idle`:

```
Schema /Game/MM/PSS_Locomotion.PSS_Locomotion
Schema cardinality 36
Assets 3
Index idle: no build is running (the last one finished; get_log names a failure)
```

`idle` means no build runs; Pose Search does not say whether a finished build worked, so a database
that never searches well after `idle` has its failure in `get_log`. `Details` is read-only. `Schema not finalized` (and `Index none`) means the schema could not be set up,
usually because the skeleton lacks a bone a channel names; fix the schema first, there is nothing to index.

## Chooser tables: `Table`

Needs the Chooser plugin. A Chooser Table picks an animation (or any asset) from rows by testing the
columns. `create_asset(path, class="ChooserTable")` makes an empty one; `read_asset(table, "Table")` and
`write_asset` do the rest. Its results, fallback and disabled flags are not editable properties, so
`Properties` (and `get_properties` without names) never show them; use `Table`:

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
- The text is the whole table: write back what you read to change nothing (`No change.`); remove a row by
  leaving its line out; every column is resized with the rows. Rows are told apart by position.
- Do not write `ColumnsStructs` through `Properties`: it leaves the rows out of step. `Properties` stays
  for the result type, result class and parameters (context objects). On UE 5.8 the write validates the table
  (compiling input bindings) and lists what it finds as `validation:` lines.

## Proxy tables: `Entries`

A Proxy Asset is a name an animation graph looks up; a Proxy Table maps it to a result. Make
`ProxyAsset`s and a `ProxyTable` with `create_asset`, then:

```
Entry /Game/Anim/PA_Locomotion.PA_Locomotion evaluate /Game/Anim/CT_Run.CT_Run
Entry /Game/Anim/PA_Idle.PA_Idle /Game/Anim/A_Idle.A_Idle
```

One entry per proxy asset; results are written as in a row (no `nested`); options `{"key":...,"outputs":[...]}`
follow the result. The write rebuilds the table's runtime lookup.

## Not covered here

The Motion Matching anim nodes of an Anim Blueprint are not described here. The
trajectory functions differ by engine: UE 5.5 `PoseSearchGenerateTrajectory` / `GetTrajectorySampleAtTime`; UE 5.8
`PoseSearchGenerateTransformTrajectory` / `GetTransformTrajectorySampleAtTime` (UE 5.7 has both).
