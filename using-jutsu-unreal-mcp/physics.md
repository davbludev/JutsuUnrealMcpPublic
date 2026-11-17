# Physics

## Destruction

Make a Geometry Collection with `unreal.JutsuDestructionLibrary` (also `call_function`):

- `create_geometry_collection(path, sources, transforms, split_islands=False)`: from Static Meshes or other Geometry
  Collections (Skeletal Meshes are refused: the engine makes them pieces that never simulate); `transforms` is `[]` (all at the origin) or one `unreal.Transform` per source;
  `split_islands` makes each connected part of a Static Mesh a piece. Returns the saved asset.
- `create_from_actors(actors, path, replace_in_level=True)`: from placed actors' Static Mesh and Geometry Collection
  components, relative to the first actor; `replace_in_level` places a Geometry Collection actor (labelled as the asset) where
  the first actor stood and deletes the actors. Save the level with `save_assets`.

The new collection is unfractured: one `Rigid` piece per Static Mesh, a `ClusterBone` root over several.

`read_asset` section `Collection`:

```
Source /Engine/BasicShapes/Cube
Source /Engine/BasicShapes/Sphere [location=(0,0,100), rotation=(0,45,0)]
Levels 2: 1, 2
ClusterBone: Cluster
  ClusterBone_1: Rigid
  ClusterBone_2: Rigid
```

- `Source` lines are writable until the collection is fractured: change, add or leave out a line and the pieces are rebuilt
  (the reply says `rebuilt: N bones in L levels`). Flags: `location=(x,y,z)`, `rotation=(pitch,yaw,roll)`, `scale=(x,y,z)`,
  `materials=[...]` (one per slot), and for Static Meshes `split`, `internal`.
- The `Levels` line and the bone tree are read-only: write them back exactly as read (edit_asset does).
- `Collection` writes partially: a bad `Source` line keeps the source in its place as it was (a new one adds nothing), a
  changed tree line is ignored, both named under `not applied:`; the other lines rebuild. A fractured collection, or a
  source whose mesh's material slots changed, refuses the write whole.
- Sources match by place: a line inserted before others makes each later line change the next source. Add new
  sources at the end and keep the order when editing.
- A bone is named by its spelling in the tree; a name two bones share reads `Name#<index>`. A rebuild, cluster or fracture
  renames bones: read the tree again before naming bones.
- After a fracture, or while a source asset does not load, a source change is refused; `JutsuFractureLibrary.reset`
  rebuilds from the sources (then they are writable again), or make a new collection with `create_geometry_collection`.
- A big tree reads its first levels; a bone ending `[children=N]` has more: read `Collection@<bone>` for that branch.
- Damage thresholds, clustering, removal and Nanite are `Properties` (`DamageThreshold`, `EnableClustering`, ...); the sources
  are only the `Source` lines.

### Fracture

`unreal.JutsuFractureLibrary` (also `call_function`), where the engine has the Fracture and PlanarCut plugins (stock
engines do; on one without them the `Collection` read opens with a note saying so). `bones` are spellings from the `Collection` tree; every call renames bones,
so read the tree again before the next call that names bones. Each call is one undo step; save with `save_assets`.

```python
import unreal
L = unreal.JutsuFractureLibrary
gc = unreal.load_asset("/Game/Destruction/GC_Wall")
s = unreal.JutsuFractureSettings()
s.uniform.min_sites, s.uniform.max_sites = 15, 25
made = L.fracture(gc, [], unreal.JutsuFracturePattern.UNIFORM, s, 7)   # [] = every piece; returns new pieces
L.auto_cluster(gc, [], 4)                       # group the root's pieces into about 4 clusters
```

Then `read_asset` the `Collection` section and name a piece from that tree:

```python
s = unreal.JutsuFractureSettings(); s.planar.planes = 2
L.fracture(gc, ["<piece as the tree spells it>"], unreal.JutsuFracturePattern.PLANAR, s, 1)   # cut one piece again
```

- Patterns and their settings member: `VORONOI` (`voronoi.sites`, points in the collection's space), `UNIFORM`
  (`uniform.min_sites`/`max_sites`, default 20), `CLUSTERED` (`clustered.min_clusters`, `max_clusters`,
  `min_sites_per_cluster`, `max_sites_per_cluster`, radii), `PLANAR` (`planar.planes`), `SLICE` (`slice.x`, `y`, `z`,
  `angle_variation`, `offset_variation`), `BRICK` (`brick.bond`, `length`, `height`, `depth`).
- Shared: `group_fracture` (default on: one cut over all selected pieces; off: each piece in its own bounds),
  `chance_to_fracture`, `split_islands`, `grout`, `noise_amplitude` (0 = flat cuts) and the other `noise_*`.
- The same seed and settings give the same tree. A cut that makes no piece is refused.
- `auto_cluster(gc, bones, count)` takes `count` 2-5000. `cluster_bones(gc, bones)` (two or more) puts them under a new
  cluster; `merge_bones(gc, bones)` joins pieces into one; `delete_bones(gc, bones)` removes them and what is under them
  (roots, and a delete that would leave a root without pieces, are refused); `reset(gc)` rebuilds from the sources.
- Placed Geometry Collection actors of the asset follow at once. Every call, and a `Collection` write, is refused while PIE
  runs.

## Static Mesh collision

A Static Mesh's simple collision is its `Collision` section: one `Complexity` line, then one line per shape.

```
Complexity UseSimpleAsComplex
Sphere [center=(0,0,120), radius=30, name="Head"]
Box [center=(0,0,50), rotation=(0,0,45), size=(100,100,100)]
Capsule [rotation=(0,90,0), radius=12, length=40, collision=QueryOnly]
TaperedCapsule [radius0=8, radius1=4, length=30, contributeToMass=false]
Convex [center=(0,0,25), verts=32]
```

- `Complexity`: `UseDefault` (project setting), `UseSimpleAndComplex`, `UseSimpleAsComplex`,
  `UseComplexAsSimple`. Left out: `UseDefault`.
- Flags print only where a shape differs from a new one of its kind. `center`, `size` (full extent per
  axis) and `rotation` (Pitch, Yaw, Roll) are number groups. Every kind takes `name`, `collision`
  (`QueryAndPhysics`, `QueryOnly`, `PhysicsOnly`, `NoCollision`, `ProbeOnly`, `QueryAndProbe`),
  `contributeToMass` and `restOffset`.
- `Sphere`, `Box`, `Capsule`, `TaperedCapsule` are written whole: add, change, or leave a line out to
  remove the shape. They match by place within their kind: a line inserted before others of its kind
  makes each later line change the next shape. Add new ones at the end and keep the order when editing. A `TaperedCapsule` collides as a capsule of the mean radius (the taper serves cloth).
- `Convex`, `LevelSet` and the skinned and ML kinds are generated geometry. A line keeps the shape with
  its `name`, else the first one whose `verts` it repeats: repeat a line to keep a shape, leave it out to
  remove that shape. `Convex` and `LevelSet` also take `center`/`rotation` (a hull's is an offset from
  where generation put it, a level set's is its grid centre); the skinned and ML kinds take only `name`,
  `collision`, `contributeToMass`, `restOffset`. `verts` is read-only; a line that keeps no shape is
  not applied. Name hulls (`name="Left"`) before reordering or pruning many of the same `verts`.
- The write marks the collision customized (kept on reimport), recooks it and refreshes placed
  components and navigation: traces see the new shapes at once.
- `Collision` writes partially: a bad line is named under `not applied:` and keeps what it stood for: a bad
  `Complexity` the trace flag; a bad `Sphere`/`Box`/`Capsule`/`TaperedCapsule` line the shape in its place; a bad
  generated-kind line every shape of its kind the text leaves out, a line of unknown kind every shape left out (which
  one it meant cannot be known).

Generate shapes in `run_python`, then read `Collision` to see and adjust them:

```python
import unreal
mesh = unreal.load_asset("/Game/Props/SM_Crate")
sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
sub.add_simple_collisions(mesh, unreal.ScriptCollisionShapeType.BOX)    # also SPHERE, CAPSULE, NDOP10_X ... NDOP26 (one hull)
sub.set_convex_decomposition_collisions(mesh, 4, 16, 100000)             # hull count, max verts per hull, precision
sub.remove_collisions(mesh)
```

`add_simple_collisions` adds to what is there; `set_convex_decomposition_collisions` replaces all simple
collision and can make fewer hulls than asked: count the `Convex` lines.

## Physics Asset

A Physics Asset is its `Physics` section: the preview mesh, solver values, profile names, one `Body` per bone with its
shapes indented under it, one `Constraint` per joint, and the pairs that do not collide.

```
Preview /Game/Characters/SK_Hero
Solver {"PositionIterations":8}
Profile Animation Ragdoll
Profile Constraint Loose
Body pelvis [physics=Kinematic, mass=12, material=/Game/Physics/PM_Flesh] {"LinearDamping":0.5}
  Capsule [center=(0,0,5), rotation=(0,90,0), radius=14, length=18]
  Animation Ragdoll {"OrientationStrength":200}
Body spine_01
  Sphere [radius=12]
Constraint spine_01 -> pelvis [swing1=Limited 45, swing2=Limited 45, twist=Limited 20]
  Profile Loose [swing1=Free]
NoCollision pelvis spine_01
```

- `Body <bone>`: the bone must exist in the `Preview` mesh (a wrong name is refused with the closest ones). Flags:
  `physics` (`Default`, `Kinematic`, `Simulated`), `mass` (kg override), `massScale`, `material` (a Physical
  Material), `trace` (`UseDefault`, `UseSimpleAndComplex`, `UseSimpleAsComplex`, `UseComplexAsSimple`). Other
  body-instance values (damping, collision profile, ...) go in the trailing `{json}`. Shapes use the Static Mesh
  shape lines above, indented. `[was="old_bone"]` moves a body to another bone.
- `Constraint <child> -> <parent>`: `linear` (`Locked`, `Limited 5`, or three motions for X Y Z: `Free Locked Limited
  5`), `swing1`, `swing2`, `twist` (`Free`, `Locked`, `Limited <degrees>`), `name`. A new constraint's frames are
  snapped to the bones, as the editor does; other values go in `{json}` (`ProfileInstance`, frames `Pos2`, ...).
- `Profile Animation|Constraint <name>` lists the profiles; `[was="Old"]` renames one and carries every body's
  `Animation` and every constraint's `Profile` entry along. An entry names a listed profile.
- `NoCollision a b` lines are the complete set of disabled pairs: a new body collides with everything until you add
  its pairs. Constrained bodies usually get a `NoCollision` line too.
- Leaving a line out removes that body, constraint, profile or pair. Writes are refused while PIE runs.
- `Physics` writes partially: a bad line skips its item (a body or constraint with its indented lines) and keeps it as
  it was; a constraint, pair or entry that needs a body or profile whose line was skipped is skipped too (`depends on
  line M`), and one naming a body the text removes is skipped and named. A bad `Preview` line keeps the current preview,
  and new or moved bodies and new constraints wait for it. A line of no known kind keeps everything no other line names;
  a shape line without its indent skips the body above it. A body a kept constraint joins stays (on its bone: a move
  off it is skipped), and a profile a kept body or constraint has an entry for stays. The other lines are written.
- A new constraint needs a `Preview` line; existing constraints keep their frames (unless their JSON gives `Pos2`, ...), also when `Preview` changes. Removing a frame key does not snap back: leave the constraint line out in one write and add it back in the next. Constraints
  are keyed by their bones, so after moving a body its constraint lines name the new bone and get fresh frames.
- New bodies go last; reordering lines changes nothing. Profile names are written here, not in `Properties`.
- To see a ragdoll fall: a Skeletal Mesh actor with the mesh, the asset as its physics asset override, and
  `simulate_physics` on in PIE.

Make a ragdoll and fit shapes with `unreal.JutsuPhysicsLibrary` (also `call_function`), then edit it as text:

```python
import unreal
lib = unreal.JutsuPhysicsLibrary
mesh = unreal.load_asset("/Game/Characters/SK_Hero")
opts = unreal.JutsuPhysicsAssetOptions(geom_type=unreal.JutsuPhysicsGeomType.CAPSULE, min_bone_size=20.0)
pa = lib.create_physics_asset(mesh, "/Game/Characters/PA_Hero", opts, assign_to_mesh=True)
lib.fit_bodies(pa, ["spine_01", "head"], unreal.JutsuPhysicsAssetOptions(geom_type=unreal.JutsuPhysicsGeomType.BOX))
```

- `create_physics_asset(mesh, path, options, assign_to_mesh=False)`: the editor's Create Physics Asset: a body per bone
  long enough (`min_bone_size`, `body_for_all`), shapes fitted to the skinned vertices, constraints between bodies
  (`create_constraints`, `angular_constraint_mode` `FREE`/`LIMITED`/`LOCKED`), overlapping bodies not colliding. Nothing
  may exist at `path`. `assign_to_mesh` makes it the mesh's physics asset (save the mesh with `save_assets`). Returns the
  saved asset. A `min_bone_size` no bone exceeds is refused, naming the largest. The engine's
  `SkeletalMeshEditorSubsystem.create_physics_asset` takes no shape or size options and writes next to the mesh.
- `fit_bodies(asset, bones, options)`: replaces each bone's shapes with new ones of `geom_type` fitted to its vertices,
  named `<bone>_<shape>` (`spine_01_box`); a bone without a body gets one, constrained to the nearest parent body, and a
  body below it that was constrained past it (an arm joined to the spine when the clavicle gets a body) is constrained to
  it, even with `create_constraints=False`; with `create_constraints` a body below it without a constraint is joined to
  it. One undo step; the asset is left unsaved (`save_assets`). A bone that cannot be fitted fails the call and changes
  nothing. `SKINNED_LEVEL_SET`, and refitting a body that holds one, are refused: make those with `create_physics_asset`.
- `geom_type`: `BOX`, `CAPSULE`, `SPHERE`, `SINGLE_CONVEX_HULL`, `MULTI_CONVEX_HULL` (`hull_count`, `max_hull_verts`);
  cloth only: `TAPERED_CAPSULE`, `LEVEL_SET`, `SKINNED_LEVEL_SET` (all bones become one body; `level_set_resolution`,
  `lattice_resolution`). `lod_index` (UE 5.7+) is refused on engines without it unless 0. `always_use_vertices` and
  `include_child_bones` (UE 5.8) are ignored on earlier engines, which fit boxes, spheres and capsules to the bone's
  weighted vertex positions and never include child bones' vertices (5.8 with both `False`).

## Physical materials and constraint actors

- A Physical Material is `Properties` / `set_properties`; a write updates the engine's live copy of the material at
  once, no restart. `SurfaceType` reads and writes by the surface's project name. Name surface types in the `Surfaces`
  section of path `Physics` (below); materials take a new name at once. A name two entries answer to (`Default`, a
  repeated name) reads as the entry, `SurfaceType3`.
- A Physical Material Mask takes `MaskTexture` through `set_properties`: a texture imported as 8-bit or 16-bit RGBA
  (not grayscale, not HDR) with a width that is a multiple of 8; another texture is refused. A mask already holding
  such a texture (set by Python or reimported grayscale) refuses its other properties until `MaskTexture` is replaced
  in a write of its own.
- A Physics Constraint Actor (component `MyConstraintComp`) joins what `ConstraintActor1`/`ConstraintActor2` name (an
  actor label), on the component `ComponentName1`/`ComponentName2` names (`{"ComponentName":"Offset"}`; none: the
  actor's root). Place the constraint where the joint is; its frames (`ConstraintInstance` `Pos1`/`Pos2` and axes)
  follow from the joined bodies and that place on every write, so leave them as read.

## Project collision settings

Path `Physics` (no asset) holds the project's collision channels, profiles and surface types, saved to
`DefaultEngine.ini` and live in the running editor (components on a profile take its new values at once). Never edit
the ini by hand.

```
Channels:  Weapon: Object [default=Ignore, slot=1]
           Interact: Trace [slot=2]
Profiles:  Projectile: Weapon QueryOnly [Pawn=Overlap, Visibility=Ignore] [description="Fast shots"]
Redirects: Profile OldShot -> Projectile
Surfaces:  Flesh: SurfaceType1
```

- `Channels`: `Object` or `Trace`; `default=` is every profile's response to it unless the profile says otherwise
  (left out: `Block`); `static` marks an object channel of static things. `slot=N` is its `ECC_GameTraceChannelN` in
  C++; leave it out on a new channel to take the first free slot. A channel keeps its slot and its kind. UE 5.5-5.7
  have 18 slots, 5.8 has 50.
- `Profiles`: `Name: <object channel> <collision> [Channel=Response, ...] [description="..."]`, collision one of
  `NoCollision`, `QueryOnly`, `PhysicsOnly`, `QueryAndPhysics`, `ProbeOnly`, `QueryAndProbe`; responses `Block`,
  `Overlap`, `Ignore`, listed only where they differ from the channel's default. `[engine]` profiles cannot change:
  keep their lines as read. Then name the profile on a component (below).
- `[was="Old"]` renames a channel or profile and adds the redirect that keeps assets resolving. `Redirects`:
  `Profile Old -> New`, `Channel Old -> New`.
- `Surfaces`: `Name: SurfaceTypeN`; leave the type out on a new name to take the first free one.
- Every section is the whole list: a line left out is removed. An object channel a profile uses, and an `[engine]`
  profile, stay when left out (the reply names them); change the profile first. `Channels`, `Profiles` and `Surfaces`
  write partially: a bad line (a kind or slot change, a taken or missing slot, an unknown channel or type, a name twice)
  is skipped and named under `not applied:`, its item kept as it was; the other lines are written. Other Physics settings (gravity, solver, combine modes) are
  `set_properties(object="PhysicsSettings", ...)`.

Component collision (`set_properties`, a `Components` or `Actors` line): `BodyInstance.CollisionProfileName` takes a
registered profile, whose `CollisionEnabled`, `ObjectType` and responses replace the component's (also values written
beside it), or `"Custom"`; writing those values without naming a profile makes it `Custom`.
`CollisionResponses.ResponseArray` lists only the channels whose response differs from the channel's default; a channel
not listed has its default.
