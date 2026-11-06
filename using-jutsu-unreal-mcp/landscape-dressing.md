# Landscape dressing

Roads, water, PCG scatter and builds over a landscape made and painted per [landscape.md](landscape.md), with the same
`lib = unreal.JutsuLandscapeLibrary`. Save at the end ([landscape.md](landscape.md#5-save)).

## 1. Splines (roads)

A landscape spline is a road: control points joined by segments. It flattens the ground along its path (raises where the road is
above the ground, lowers where below), paints a target layer along it and lays meshes along it. One call makes a whole road from a
polyline.

```python
lib.ensure_target_layers(land, ['Grass', 'Dirt'], '/Game/Landscape/Layers', unreal.JutsuLandscapeLayerOptions())   # a paint layer needs its Layer Info first
def point(x, y):
    p = unreal.JutsuLandscapeSplinePoint()
    p.location = unreal.Vector(x, y, 0)         # world cm; Z is ignored while snap_to_terrain is on
    p.width_cm = 600.0                          # the road's FULL width at this point (the engine stores half)
    p.side_falloff_cm = 400.0                   # how far the ground blends out sideways from the road's edge
    p.end_falloff_cm = 400.0                    # past the road's first / last end
    return p
o = unreal.JutsuLandscapeSplineOptions()
o.paint_layer = 'Dirt'                          # painted along the whole road (a point's own paint_layer wins); '' = none
o.snap_to_terrain = True                        # each point's Z = the ground under it (+ height_offset_cm); False: your Z is the road height
                                                # only the points snap: between them the road is a curve that cuts or fills, so on rough ground put a point every 10-20 m
m = unreal.JutsuLandscapeSplineMesh(); m.mesh = unreal.load_asset('/Game/Roads/SM_RoadSlab')   # optional: meshes bent along every segment
o.meshes = [m]
o.tangent_scale = 1.0                           # smoothing of the curves: 1 = natural bend, lower = tighter to the straight line
road = lib.create_landscape_spline(land, [point(0, 0), point(3000, 500), point(6000, 4000)], o)   # applied at once
```

- The reply (and `lib.get_landscape_splines(land)`, one entry per spline) holds `owner`, `points` and `segments`. The `owner` is the
  actor that holds the spline: the landscape itself, or in a World Partition map a `LandscapeSplineActor` (made at the road's start;
  the proxies under the road must be loaded).
- A point: `location`, `width_cm`, `side_falloff_cm`, `end_falloff_cm`, `paint_layer`, `raise_terrain` / `lower_terrain` (default both
  on), `rotation` + `auto_rotation` (True: the rotation follows the neighbors; a read returns False with the rotation in use). A
  segment: `start_point` / `end_point` (indices into `points`), `paint_layer`, `raise_terrain` / `lower_terrain`, `meshes`,
  `auto_tangent` + `tangent_scale` + `start_tangent_cm` / `end_tangent_cm` (a read returns `auto_tangent` False with the lengths in
  use), and the read-only `mesh_count`. `create_landscape_spline` joins consecutive points; a segment's paint layer and raise/lower
  are its start point's. After moving points, set `auto_rotation` True on them and `auto_tangent` True on their segments, or the old
  rotation and tangent lengths stay.
- Outside World Partition the landscape holds ONE spline: a second `create_landscape_spline` adds its points after the existing
  ones (earlier roads and their indices stay; the reply is the whole spline). In a World Partition map every create makes its own
  `LandscapeSplineActor`; to branch off a road, `add_spline_point` on that road's `owner` with `connect_to` (a segment cannot join
  points of two actors).
- **Edit by index.** Read, change, write back; a point or segment is its index in the list:
  ```python
  road = lib.get_landscape_splines(land)[0]
  pts = list(road.points); p = pts[2]; p.width_cm = 1200.0; pts[2] = p; road.points = pts   # a struct read from a list is a copy: assign it back
  road = lib.set_landscape_spline(land, road, True)     # point i = control point i (changed in place, or added; points past the end are deleted with their segments); segments likewise; applies
  ```
  `lib.add_spline_point(land, road.owner, point_struct, connect_to, True)` returns the new index (`connect_to` = a point to join it to,
  -1 = none); `lib.connect_spline_points(land, owner, a, b, True)` joins two points (a junction when one already has a segment) and
  returns the segment index; `lib.delete_spline_point(land, owner, i, True)` removes a point and its segments (later indices move
  down by one); `lib.delete_landscape_spline(land, owner, True)` removes the whole spline. The last argument is `apply`: pass False
  to batch edits, then `lib.apply_landscape_splines(land)` once.
- **Apply.** The deformation and paint live on the landscape's Splines edit layer (kind `SPLINES`), added on first use at the top of
  the stack. Each apply clears that layer and rebuilds it from every spline, so widening a point and applying again moves the whole
  footprint, and deleting a spline gives the ground back. Sculpting or painting on the layers below stays; the road is drawn over it.
  The road's paint is added to the weights below it before they share 100 %: over ground that is wholly one other layer a road
  layer reads about half and half (128 / 128), like any paint on an upper edit layer.
- A paint layer a point, segment or the options name must be a target layer with a Layer Info asset: the call names the missing
  one. A point off the landscape (with `snap_to_terrain`), two consecutive points at one place, a width of 0 or less, more than 512
  points, an empty mesh entry and a footprint over unloaded components are refused with the reason.
- `call_function`: `CreateLandscapeSpline` takes `Points` as a JSON array of point objects (`Location`, `WidthCm`, ...) and
  `Options` as an object; the reply `ReturnValue` is the spline. `Owner` is an object path.

## 2. Water

Water bodies (plugin `Water`) and Landscape Patches ([landscape.md](landscape.md#landscape-patch-a-stamp-on-its-own-layer)) may be placed by any tool call (`spawn_actor`, `run_python`) on a landscape that lacks their
edit layer: the plugin holds the editor's modal "new edit layer" dialog off while any call runs, so the layer is created at once and
the editor does not freeze.

Read the ground height at the lake's origin (`lib.get_heights` over a small `make_world_box_region` there): that is the water
surface. Then `spawn_actor` `class` `WaterBodyLake`, `location` `[x, y, z]`.

- The actor's Z is the water surface; the bed is cut `channel_depth` (default 500 cm) below it. The lake's origin sits on the ground you read `z` from, so level or raise that spot to the wanted surface first.
- An editor world without a Water Zone gets `WaterZone_0` when the first body is spawned (`unreal.WaterZone` actors list it).
- The Water body adds a standard layer `Water` holding a Water brush manager actor, and the cut draws on the editor's next ticks:
  read the heights again on a later call ([landscape.md](landscape.md#3-edit-layers)). The bed shows as a run of vertices at `z - 500`.
- The brush is in `list_edit_layers(land)[-1].brushes`: `remove_brush_from_edit_layer` fills the riverbed back,
  `add_brush_to_edit_layer(land, 'Water', brush)` cuts it again. The depth is
  `lake.get_editor_property('water_body_component').get_editor_property('curve_settings').get_editor_property('channel_depth')`.

## 3. PCG dress

Scatter (trees, rocks, flowers) is a PCG graph on a volume over the landscape. This graph samples the landscape surface, keeps the
points where the `Grass` layer weighs at least 0.5 and spawns a mesh on them.

1. `create_asset` path `/Game/Landscape/PCG_Meadow`, class `PCGGraph`.
2. `write_asset` section `Graph` ([pcg.md](pcg.md)): the nodes, their settings and the links. The landscape's layer weights are
   point attributes named after the layers; a range filter sets both ends. The spawner's meshes are one setting line.

```
Input Input
land GetLandscape
sample SurfaceSampler
  Surface = land
  PointsPerSquaredMeter = 0.05
filter AttributeFilteringRange
  In = sample
  TargetAttribute = {"Selection":"Attribute","AttributeName":"Grass"}
  MinThreshold = {"bUseConstantThreshold":true,"AttributeTypes":{"Type":"Double","DoubleValue":0.5}}
  MaxThreshold = {"bUseConstantThreshold":true,"AttributeTypes":{"Type":"Double","DoubleValue":1.0}}
spawn StaticMeshSpawner
  In = filter.InsideFilter
  MeshSelectorParameters = {"MeshEntries":[{"Descriptor":{"StaticMesh":"/Engine/BasicShapes/Cone.Cone"}}]}
Output Output
```

3. The volume, in `run_python`:

```python
pg = unreal.load_asset('/Game/Landscape/PCG_Meadow')
# scale it over the landscape (the cube is 2 m: scale 30 covers 60 m; scale Z over the terrain's height range), assign the graph, generate
volume = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(unreal.PCGVolume, unreal.Vector(0, 0, 0))
volume.set_actor_scale3d(unreal.Vector(30, 30, 20))
pcg = volume.get_component_by_class(unreal.PCGComponent)
pcg.set_graph(pg)
pcg.set_editor_property('is_component_partitioned', True)      # generate per grid cell; use it in a World Partition map
pcg.generate(True)
```

Generation finishes on later ticks: read the instances on a later call. With `is_component_partitioned` the `InstancedStaticMeshComponent`s
(`ISM_<mesh>_N`) belong to PCG partition actors, not to the volume, so scan every actor:
`[c.get_instance_count() for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor) for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent)]`.
Repaint the layer and call `pcg.generate(True)` again to scatter on the new paint. Other PCG nodes and their settings: [pcg.md](pcg.md).

## 4. Builds

The editor's Build menu as calls. Each works on the landscape and its loaded streaming proxies, blocks until the engine is done, and
returns a `unreal.JutsuLandscapeBuildResult`: `build`, `complete`, `proxies`, `outdated_before`, `outdated_after` (components for
grass maps and physical material, landscape actors for Nanite) and `message`. When `complete` is False, `message` says what remains
and the call that finishes it (a physical material build waits up to 5 minutes for the GPU; streaming proxies not loaded are named).
Builds are not undo steps; they mark the landscape for saving.

```python
r = lib.build_grass_maps(land)                  # the data grass types scatter from, per component
r = lib.build_physical_material(land, False)    # the material's physical material output rendered per component; True rebuilds up-to-date components too
lib.set_landscape_nanite(land, True)            # one undo step; False turns it off
r = lib.build_nanite(land, False)               # the Nanite mesh; nothing to do while Nanite is off; True rebuilds all
for r in lib.build_landscape(land): r.build, r.complete, r.message     # grass maps, physical material and, when Nanite is on, Nanite
```

**Grass.** Create the grass type with the `create_asset` tool (class `LandscapeGrassType`), fill its varieties, and add a grass output
to the landscape material graph ([landscape.md](landscape.md#4-target-layers-and-paint)) that reads the layer's weight:

```
density LandscapeLayerSample {"ParameterName":"Grass"}
cover LandscapeGrassOutput {"GrassTypes":[{"Name":"Meadow","GrassType":"/Game/Landscape/GT_Meadow"}]}
  Meadow = density
```

Fill the varieties with `set_properties` on the grass type, the whole array at once (`GrassDensity` is instances per 10 square
meters): `{"GrassVarieties":[{"GrassMesh":"/Engine/BasicShapes/Cone.Cone","GrassDensity":{"Default":400}}]}`. Then
`r = lib.build_grass_maps(land)`; `outdated_before` counts the components that had no map yet.

`outdated_after` 0 proves every component holds its grass map. The instances are placed around the editor camera by the engine; an
unattended editor without a viewport shows none, so judge the scatter in the viewport.

**Physical material.** Add a `LandscapePhysicalMaterialOutput` node to the landscape material graph: its `Inputs` list the physical
materials and each input pin is named after its asset; the input with the highest value at a vertex wins.

```
phys LandscapePhysicalMaterialOutput {"Inputs":[{"PhysicalMaterial":"/Game/Landscape/PM_Grass"},{"PhysicalMaterial":"/Game/Landscape/PM_Rock"}]}
  PM_Grass = grass
  PM_Rock = rock
```

`build_physical_material` and the line trace ([landscape.md](landscape.md#1-create); `hit.to_tuple()[8]` is the hit's physical material) use the material's
`LandscapePhysicalMaterialOutput`; the Layer Info `physical_material` is the fallback that collision uses for a layer when the material has no
such node. Delete the Layer Infos, or clear their `physical_material`, before deleting a physical material asset: a referenced one
crashes the editor on deletion. On UE 5.5 and 5.6 the trace read None in an unattended editor; check the material on 5.7+.

Save through `save_assets` (or `open_level`, which saves the previous level first): they finish the pending physical material tasks first.
A save from `run_python` must call `build_physical_material` first (UE 5.6 asserts when a map is saved while a task runs).

Run the builds after the last sculpt, paint and spline edit, then save. Nanite needs a Nanite-capable renderer (`r.Nanite 1`).
