# Landscapes

The route: create -> sculpt -> edit layers -> target layers and paint -> dressing ([landscape-dressing.md](landscape-dressing.md): roads,
water, PCG scatter, builds) -> save.
The plugin's `unreal.JutsuLandscapeLibrary` does what the engine's script surface cannot (same calls in `call_function`, object
`JutsuLandscapeLibrary`; `tools/list` does not show it). A function that cannot do what its name says raises a `RuntimeError` naming
the reason and the working form. Works on UE 5.5-5.8. Every write is final when the call returns (merged, marked for saving, one
undo step: `TRANSACTION UNDO`); the builds are the exception ([landscape-dressing.md](landscape-dressing.md#4-builds)).

```python
lib = unreal.JutsuLandscapeLibrary
```

## 1. Create

Work in a saved map: a fresh editor opens the throwaway `/Temp/Untitled_1`, which cannot be saved in place. Make one first with
`unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).new_level('/Game/Maps/Terrain')` (classic; [world.md](world.md) for World Partition).

```python
p = unreal.JutsuLandscapeCreateParams()      # every field has a default: 8 x 8 components, 63 quads, 1 m per quad, flat
p.location = unreal.Vector(0, 0, 0)          # the CENTER of the landscape
p.components_x = 8; p.components_y = 8       # 1..256 per side; or p.size_x_meters = 500; p.size_y_meters = 500 (both; rounded to whole components)
p.scale = unreal.Vector(100, 100, 100)       # cm per quad in X/Y; Z 100 stores heights within +-256 m of the origin
p.material = unreal.load_asset('/Game/Landscape/M_Terrain')      # optional; later: set_properties LandscapeMaterial
p.label = 'Terrain'                          # optional
land = lib.create_landscape(p)               # returns the Landscape actor; one undo step (TRANSACTION UNDO removes it) except in a World Partition map (split into streaming proxies: no single undo step)
info = lib.get_landscape_info(land)          # any landscape actor or streaming proxy
```

- `p.heightmap_file = 'C:/maps/ridge.r16'` starts from a file (`.png` 16-bit grayscale, `.r16`, `.raw`; absolute path). The file
  decides the layout, so `components_*`, `sections_per_component` and `quads_per_section` are ignored; a size that fits no layout
  is expanded to the next one.
- Sections are 1 or 2 per component side, quads per section 7, 15, 31, 63, 127 or 255 (default 1 x 63). At most 8191 vertices a side.
- In a World Partition map the landscape splits into streaming proxies of `p.grid_size_in_components` (1..16, default 2) components
  per side. A partitioned landscape of more than 1024 components is refused.

`info` (`unreal.JutsuLandscapeInfo`) holds: `label`, `path`, `location` (the origin: the corner at vertex 0, 0), `scale`,
`world_bounds`, the vertex grid `min_vertex_x .. max_vertex_x` and `min_vertex_y .. max_vertex_y` (both ends inclusive; vertices a
side = components x quads per component + 1), `sections_per_component`, `quads_per_section`, `quads_per_component`,
`components_x/y` (the loaded part), `min_height_cm` / `max_height_cm` (final merged heights, world Z), `height_limit_min_cm` /
`height_limit_max_cm` (the world Z range heights can encode: `set_heights` raises outside it, mask, noise and brush operations clamp to it), `edit_layers` (`name`, `visible`, `locked`,
`heightmap_alpha`, `weightmap_alpha`; a new landscape has one, `Layer`), `target_layers` (`name`, `layer_info` asset path),
`partitioned`, `grid_size_in_components`, `loaded_proxies`, `unloaded_proxies`.

A vertex (x, y) sits at world `origin + rotation * (x * scale.x, y * scale.y)`; a stored height h (0..65535) is world Z
`origin.z + (h - 32768) / 128 * scale.z`. Probe the terrain height at (x, y) with a line trace right after any change:

```python
hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 100000), unreal.Vector(x, y, -100000),
    unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, True)
z = hit.to_tuple()[5].z                      # impact point; [8] is the hit's physical material
```

### World Partition landscapes

Edits reach loaded streaming proxies only. A landscape far from the origin reopens with its proxies unloaded
(`info.unloaded_proxies > 0`, grid fields 0); load them with the World Partition library ([world.md](world.md)); the proxies appear
on the next call:

```python
wp = unreal.WorldPartitionBlueprintLibrary
wp.load_actors([d.guid for d in wp.get_actor_descs() if d.native_class.get_name() == 'LandscapeStreamingProxy'])   # needs a saved map
```

A region over unloaded components raises, naming the region.

## 2. Sculpt

Heights are world Z in **cm** (`raw=True`: stored 0..65535, 32768 = the origin height). A height steps in `scale.z / 128` cm
(0.78 cm at scale 100): a value set reads back rounded to that step, and a change smaller than one step does not show.

### Regions, arrays and files

```python
r = lib.make_vertex_region(10, 20, 19, 24)                    # vertices, both ends inclusive; or lib.make_world_box_region(min_x, min_y, max_x, max_y) in cm
# unreal.JutsuLandscapeRegion() = the whole loaded landscape. A world box takes the vertex rectangle bounding its footprint in
# landscape space (edges included, clamped): on a rotated landscape that is the rectangle around the rotated box.
h = lib.get_heights(land, r, False, '')                       # (landscape, region, raw, edit_layer); '' = the final merged result, a name = that layer's own data
h.min_vertex_x, h.min_vertex_y, h.width, h.height, list(h.values)          # row-major: x fastest
lib.set_heights(land, r, [1500.0] * (h.width * h.height), False, '')       # exactly one value per vertex, else it raises naming both counts; '' = the first standard edit layer (the bottom-most; locked, Splines and procedural layers are refused, naming ListEditLayers / list_edit_layers)
```

After `TRANSACTION UNDO` the next read is already the restored heights.

- `set_heights` raises on a height the landscape cannot store (outside `info.height_limit_min_cm .. height_limit_max_cm`,
  or not a number; raw: whole numbers 0..65535) and writes nothing. Vertices where the landscape has no component (holes in
  its layout) read as 32768 (the origin height) and are not written. An array call (heights, masks, noise, and an import with scale or offset) takes a region of at most 16 777 216 vertices (4096 x 4096); bigger regions raise pointing to heightmap and weightmap files, which have no such limit.
- Move big data through `run_python`: a 4M-element list crosses into a library call in 0.3-0.6 s (adds about 110 MB), so a whole
  2048 x 2048 landscape is one call. `call_function` carries JSON in one request capped at 4 MB: about 500 000 numbers (a 700 x 700
  region).
- `lib.import_heightmap(land, 'C:/maps/hill.png', offset_x, offset_y, scale, offset_cm, '')` writes a heightmap file with
  its first pixel at that vertex; it must fit inside the loaded landscape (else it raises with the spans). `scale` 1 and
  `offset_cm` 0 store the file's values unchanged; otherwise each height becomes `origin + (file height - origin) * scale +
  offset_cm`, and a result the landscape cannot store raises. `lib.export_heightmap(land, 'C:/out/hill.png', region)` writes
  the final heights of a region (an existing file is replaced only when the export succeeds). Formats: use **`.png`**
  (16-bit grayscale; carries its size, any rectangle). `.r16` has no size inside, so it imports only when square; `.raw`
  needs the `.json` beside it that export writes; a `.json` of the same name beside an `.r16` is read as its sidecar too,
  so give exports of different formats different names. A `.png` export then import elsewhere restores the stored heights exactly
  (the png keeps 16 bits). Use files for whole landscapes; arrays for regions.
- **Masks** (`unreal.JutsuLandscapeMask()`): `texture` (a grayscale texture asset stretched over the region; red channel of
  a color one) or `values` (one 0..1 value per region vertex), `strength` (0..1), `invert`, `edge_falloff_vertices` (fades
  to nothing toward the region's edge). None given = 1 everywhere.
  `lib.apply_height_mask(land, region, mask, unreal.JutsuLandscapeHeightOp.ADD, 1000.0, '')` moves each height toward
  `op(height, value_cm)` by its mask weight. Ops: `SET` (plateau; `strength` 0.5 blends halfway toward it), `ADD`, `SUBTRACT`,
  `MULTIPLY` (height above the origin times value), `MIN`, `MAX`. A crater is `SUBTRACT` with a round mask; a stamp is `MAX` or
  `ADD` with a texture. Vertices with weight 0 keep their stored value exactly.
- **Noise:** `n = unreal.JutsuLandscapeNoise()` with `kind` (`unreal.JutsuLandscapeNoiseKind.FBM`: rolling, +-amplitude; `.RIDGED`: 0 to amplitude, sharp ridges),
  `seed`, `feature_size_meters` (0.1..1 000 000), `octaves` (1..12), `lacunarity` (1..8), `gain` (0..4), `amplitude_cm`, `replace`
  (False adds to the heights; True sets `base_height_cm` + noise). `lib.fill_noise(land, region, n, mask, '')`. The pattern follows
  the vertex grid and the seed, so neighbouring regions and later calls tile.
- Mask, noise and brush results beyond what the landscape stores clamp to its limits. Like the brush strokes below, `apply_height_mask` and `fill_noise` work in world Z of the layers up to `edit_layer`: they read those layers' merged heights and write the difference into `edit_layer`.

### Brush strokes

One call per stroke, each over a **brush** (or a ramp's footprint) and its falloff: nothing outside changes, one undo step,
the reply is the vertex rectangle worked on (a `JutsuLandscapeHeights` with empty `values`; read the result with `get_heights`). Heights and lengths are cm and **world Z of the layers up to `edit_layer`** (the layers above it are left out, as in the editor's tools: a road on the Splines layer is not baked into the base): the difference to the layers below goes into that layer, so `sculpt_flatten(.., 1000, 'Hill')` gives world Z 1000 cm for the layers up to `Hill` (layers above still add on top) and the layers below are untouched (a hidden layer, or heightmap alpha below 0.05, is refused: it would not show). `edit_layer` '' = the first standard edit layer.

```python
b = unreal.JutsuLandscapeBrush()
b.shape = unreal.JutsuLandscapeBrushShape.CIRCLE         # or BOX (radius = half the side; axes along world X/Y)
b.center = unreal.Vector(x, y, 0)                        # world X/Y of the middle (Z ignored)
b.radius_cm = 2000.0                                     # outer edge
b.falloff = 0.5                                          # 0..1 of the radius, inward from the edge (0 = hard edge)
b.falloff_kind = unreal.JutsuLandscapeBrushFalloff.SMOOTH    # LINEAR, SMOOTH, SPHERICAL (dome), TIP (peak)
b.strength = 1.0                                         # 0..1; under 1 each tool blends toward its result
lib.sculpt_raise(land, b, 500.0, '')                     # +500 cm at full weight (negative digs)
```

- `sculpt_raise(land, brush, strength_cm, layer)`: height added = `strength_cm * brush.strength * falloff weight`. A mound is a round brush with `TIP` or `SPHERICAL`.
- `sculpt_smooth(land, brush, radius_vertices=3, iterations=1, kind=GAUSSIAN, layer)`: radius 1..64, iterations 1..100; `kind` is `unreal.JutsuLandscapeSmoothKind.BOX` or `GAUSSIAN`.
- `sculpt_flatten(land, brush, height_cm, direction=BOTH, layer)`: level to a world Z; `direction` (`unreal.JutsuLandscapeFlattenDirection`) `ONLY_RAISE` / `ONLY_LOWER` leave the other side alone.
- `sculpt_flatten_to_plane(land, brush, point, normal, direction=BOTH, layer)`: the plane through `point` (world cm) with `normal` (mostly up).
- `sculpt_ramp(land, start, end, width_cm, side_falloff_cm=500, strength=1, layer)`: no brush; `start`/`end` are world `Vector`s whose **Z is the ground height at that end**; a straight slope fading out over `side_falloff_cm` at the sides and ends.
- `sculpt_noise(land, brush, noise, layer)`: the `JutsuLandscapeNoise` of `fill_noise` under the brush.
- `sculpt_erode_thermal(land, brush, iterations=30, talus_angle_degrees=35, layer)`: ground steeper than the angle slides down (iterations 1..1000).
- `sculpt_erode_hydraulic(land, brush, iterations=50, rain_cm=1, solubility=0.05, evaporation=0.3, capacity=0.2, layer)`: water cuts channels and fills hollows (iterations 1..1000).
- `sculpt_terrace(land, brush, step_height_cm, smoothness=0.25, offset_cm=0, layer)`: snaps heights to levels `offset + k * step`; smoothness 0 = sheer steps, 1 = rolling slopes.
- Erosions move material and treat ground outside the brush as a wall, so a hard-edged (falloff 0, strength 1) brush keeps its volume; a falloff or strength under 1 keeps only part of what moved. Smooth reads up to 128 vertices beyond the brush.
- Keep `iterations x vertices` modest (a brush of a few hundred vertices a side with a few hundred iterations is fine); a call that would take too long raises and names the brush size to use.
- A brush that covers none of the landscape raises; one half outside works on the part inside. Trailing arguments with a default (shown with `=`) can be left out in `run_python`; `call_function` takes `Brush` as a JSON object (`Shape`, `Center`, `RadiusCm`, ...).

## 3. Edit layers

A landscape is a stack of edit layers added up bottom to top: a stamp on its own layer comes off without touching the base. A new
landscape has one layer, `Layer`. Layers are addressed by name; each change merges at once. Height and weight writes (`set_heights`,
sculpt, paint, imports) go into a standard, unlocked layer: the Splines layer (rebuilt at every apply) and procedural patch layers
(computed) are refused, and an empty `edit_layer` means the bottom-most standard layer.

```python
K = unreal.JutsuLandscapeEditLayerKind
rows = lib.list_edit_layers(land)    # name, guid, kind, procedural_class, index (0 = bottom), visible, locked, heightmap_alpha, weightmap_alpha, brushes
hill = lib.add_edit_layer(land, 'Hill', K.STANDARD, None)    # on top; returns the name (made unique); '' = Layer1, Layer2...
lib.set_edit_layer_visible(land, hill, False)                # hidden: its heights leave the final result
lib.set_edit_layer_alpha(land, hill, 0.5, 1.0)               # heights x 0.5 (-1..1, negative inverts), paint x 1 (0..1)
lib.set_edit_layer_locked(land, hill, True)
lib.move_edit_layer(land, hill, 0)                           # to the bottom (positions 0..count-1)
lib.clear_edit_layer(land, hill, unreal.JutsuLandscapeClearTarget.HEIGHTS)   # ALL, HEIGHTS or WEIGHTS; the layer stays
lib.collapse_edit_layer(land, hill)                          # merges into the layer below and removes it
lib.delete_edit_layer(land, hill)                            # the layer and its data; add another layer before deleting the last one
# a listed layer rebuilds from its row: lib.add_edit_layer(land, 'Copy', row.kind, row.procedural_class)
```

- Kinds: `STANDARD` (sculpt and paint data, holds Blueprint brushes), `SPLINES` (the layer landscape splines draw into; one per
  landscape; no alpha), `PROCEDURAL` (drawn by code; needs its class as the fourth argument, for example
  `unreal.load_class(None, '/Script/LandscapePatch.LandscapePatchEditLayer')`; `row.procedural_class` holds it). Procedural and
  Splines layers hold no painted data: clear and collapse refuse them.
- The editor allows at most `Max Number of Layers` layers (Project Settings > Landscape, default 8); `add_edit_layer` refuses past it.
- `collapse_edit_layer` needs both layers standard, visible, unlocked and without brushes; final heights stay the same while both
  had alpha 1. On a World Partition landscape `collapse_edit_layer`, `clear_edit_layer` and `delete_edit_layer` need every streaming
  proxy loaded (see section 1).
- Blueprint brushes sit on a standard layer. `lib.add_brush_to_edit_layer(land, layer, brush)` puts a brush actor on top of the
  layer's brushes (one layer of one landscape at a time), `lib.remove_brush_from_edit_layer(land, brush)` takes it off (the actor
  stays in the level), `lib.move_edit_layer_brush(land, brush, index)` reorders. A Landmass brush is an actor of the Landmass plugin
  (`/Script/LandmassEditor.LandmassManagerBase` or a Blueprint of it; `unreal.find_object(None, that path)` is None when the plugin is off).
- Brush and patch layers draw on the editor's next ticks, not inside the call that changed them: after placing a patch or a water
  body, or adding or removing a brush, read the final heights on later `run_python` calls until a height inside the stamp changes
  (usually the next call). Standard layer changes are final at once. `get_heights`, `get_weights` and `get_landscape_info` leave
  the map unmodified.

### Landscape Patch: a stamp on its own layer

A patch (`LandscapeCircleHeightPatch`, `LandscapeTexturePatch`; plugin `LandscapePatch`, on when
`unreal.find_object(None, '/Script/LandscapePatch.LandscapePatchEditLayer')` is not None) is a component: put it on a Blueprint actor
with the Jutsu components text (`Patch: LandscapeCircleHeightPatch`, parent `/Script/Engine.Actor`) and place that Blueprint. A circle
patch raises the terrain to its own Z inside `radius`, easing out over `falloff`. Placing it opens no dialog.

```python
cls = unreal.load_class(None, '/Script/LandscapePatch.LandscapePatchEditLayer')
lib.add_edit_layer(land, 'Stamp', unreal.JutsuLandscapeEditLayerKind.PROCEDURAL, cls)
actor = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_object(bp, unreal.Vector(0, 0, 500))
def patch(): return actor.get_component_by_class(unreal.LandscapeCircleHeightPatch)   # fetch it again after setting a property
patch().set_editor_property('radius', 1000); patch().set_editor_property('falloff', 500)
lib.bind_patch_to_edit_layer(patch(), land, 'Stamp')     # the same call on 5.5-5.8; raises when the patch did not end up on that layer
```

`bind_patch_to_edit_layer` is the one way to name the layer (the engine's own routes differ per lane) and reads the binding back.
The layer must be a patch layer (`PROCEDURAL` with the class above). A patch placed on a landscape with a patch layer may join the
first one on its own; bind to pick the layer. Hide, move or delete the layer and the stamp leaves without touching `Layer`.

A texture patch takes a height texture and weight patches (bind the layer before reading heights):

```python
Mode = unreal.LandscapeTexturePatchSourceMode
patch().set_height_source_mode(Mode.TEXTURE_ASSET); patch().set_height_texture_asset(texture)
patch().set_height_encoding_mode(unreal.LandscapeTextureHeightPatchEncoding.WORLD_UNITS)
settings = unreal.LandscapeTexturePatchEncodingSettings(); settings.world_space_encoding_scale = 400.0   # white = 400 cm
patch().set_height_encoding_settings(settings)
patch().set_zero_height_meaning(unreal.LandscapeTextureHeightPatchZeroHeightMeaning.WORLD_ZERO)
patch().set_unscaled_coverage(unreal.Vector2D(2000, 2000))                    # world size the texture covers
if hasattr(patch(), 'create_weight_patch'): patch().create_weight_patch('Grass', Mode.TEXTURE_ASSET, unreal.LandscapeTexturePatchAlphaSourceMode.NONE)   # 5.8
else: patch().add_weight_patch('Grass', Mode.TEXTURE_ASSET, False)           # 5.5 - 5.7
patch().set_weight_patch_texture_asset('Grass', weight_texture)
lib.bind_patch_to_edit_layer(patch(), land, 'Stamp')
```

## 4. Target layers and paint

Order: a landscape **material** with one layer node per layer -> **`ensure_target_layers`** (creates the Layer Info assets and binds them)
-> paint. A layer cannot be painted until it has a bound Layer Info; every paint call names the layer (`'Grass'`) and says
`ensure_target_layers` when it is missing. Weights are 0..1 floats (`raw=True`: 0..255 as stored).

The material, with the `create_asset` tool (class `Material`) then `write_asset` section `Graph` ([material.md](material.md)): one
`LandscapeLayerWeight` per layer, each chained `Base = <previous>` and `Layer = <colour>`; the `ParameterName` is the layer name.

```
sand Constant3Vector {"Constant":{"R":0.76,"G":0.7,"B":0.5,"A":1}}
green Constant3Vector {"Constant":{"R":0.1,"G":0.4,"B":0.1,"A":1}}
gray Constant3Vector {"Constant":{"R":0.45,"G":0.45,"B":0.45,"A":1}}
grass LandscapeLayerWeight {"ParameterName":"Grass"}
  Base = sand
  Layer = green
rock LandscapeLayerWeight {"ParameterName":"Rock"}
  Base = grass
  Layer = gray
Output
  BaseColor = rock
```

Set it with `p.material` at creation, or later with `set_properties` on the landscape actor: `{"LandscapeMaterial": "/Game/Landscape/M_Terrain.M_Terrain"}`. [landscape-dressing.md](landscape-dressing.md#4-builds) adds the grass and
physical material outputs to the same graph.

```python
o = unreal.JutsuLandscapeLayerOptions()      # blend: WEIGHT_BLEND (default), NO_BLEND, PREMULTIPLIED_ALPHA (UE 5.7+; raises on 5.5/5.6); physical_material
rows = lib.ensure_target_layers(land, [], '/Game/Landscape/Layers', o)    # [] = every layer the landscape material declares; or ['Grass', 'Rock']
for r in rows: r.name, r.layer_info                                        # target layers after the call, with the asset path bound to each
```

- `ensure_target_layers` leaves a layer that already has an info alone, reuses a Layer Info of that layer name found in the folder,
  and creates the rest there (options apply to created ones). The new assets are dirty until `save_assets`. `lib.bind_target_layer(land,
  'Grass', info_asset)` binds an existing asset whose own layer name is `Grass`; `lib.remove_target_layer(land, 'Grass')` removes the
  layer (weights already painted stay in the weightmaps). `get_landscape_info` and `ensure_target_layers` list paint layers only
  (the hole layer of a material with a visibility mask stays out).
- **Share 100 %:** a `WEIGHT_BLEND` write lowers the other `WEIGHT_BLEND` layers of that edit layer so a vertex adds up to 255
  (the same result on every lane). A layer lowered where no other layer has weight hands the rest to the layer with the most weight
  in that area; a lone layer raised on an empty vertex takes all of it. So give the terrain a base first
  (`fill_layer(land, 'Grass', 1.0, '')`), then paint the others over it. `NO_BLEND` (an independent mask layer: roads, snow cover)
  and `PREMULTIPLIED_ALPHA` layers neither lower nor are lowered.
- Reads with `edit_layer` '' give the merged final weights (what the material shows); a layer's own weights in an edit layer read
  with `edit_layer` set to that layer's name (`'Layer'` on a new landscape).
- UE 5.6 only: a merge the editor runs on its own (after an undo, or an edit in the Landscape mode) may blend stale data (a lone
  layer reads 128 instead of 255). Library writes and `export_*` flush correctly; after undo or Landscape-mode edits, call a library
  read or write once (`get_weights`, or any paint call) before trusting merged weights.
- **Weights over a region** (regions as in section 2; `edit_layer` '' = the final merged result when reading, the first edit layer
  when writing): `lib.get_weights(land, region, 'Grass', raw, '')`, `lib.set_weights(land, region, 'Grass', values, raw, '')` (one
  value per vertex, row-major, x fastest), `lib.fill_layer(land, 'Grass', 1.0, '')` (whole landscape, any size; 0.0 clears),
  `lib.get_weights_at_point(land, unreal.Vector(x, y, 0))` -> `.dominant` and `.layers` (`layer`, `weight`; strongest first, zero
  weights left out) at the nearest vertex of a world point.
- **Brush:** `lib.paint_brush(land, 'Grass', b, erase, '')` moves the weights toward 1 (`erase`: toward 0) by the brush weight of the
  sculpt brush `b`; one call is one stroke.
- **Rules** (terrain-aware, computed natively from the final merged heights: no arrays through Python):
  ```python
  r = unreal.JutsuLandscapePaintRule(); r.layer = 'Rock'; r.min_slope = 35.0       # degrees; max_slope default 90
  s = unreal.JutsuLandscapePaintRule(); s.layer = 'Snow'; s.min_height_cm = 3000.0   # world Z; max_height_cm default huge
  g = unreal.JutsuLandscapePaintRule(); g.layer = 'Grass'                            # no limits = everywhere ("grass elsewhere" goes first)
  lib.paint_by_rules(land, unreal.JutsuLandscapeRegion(), [g, r, s], unreal.JutsuLandscapeMask(), '')   # applied in order: a later rule paints over an earlier one
  ```
  Per rule: `slope_falloff` (degrees) and `height_falloff_cm` fade the rule out beyond its range (0 = hard edge), `strength` (0..1),
  `breakup` (0..1) with `breakup_feature_size_meters` and `breakup_seed` breaks the coverage into noise patches. The mask (section 2)
  limits where all rules act. Slopes use the vertex spacing (`scale.x`, `scale.y`).
- **Weightmap files:** `lib.export_weightmap(land, 'Rock', 'C:/out/rock.png', region)` writes a layer's final weights of a region
  (8-bit grayscale `.png`; `.r8` square raw bytes; `.raw` with a `.json` sidecar holding `width`/`height`/`bpp`, written next to it);
  `lib.import_weightmap(land, 'Rock', 'C:/out/rock.png', offset_x, offset_y, '')` writes a file with its first pixel at that vertex.
  Export, change, import keeps the 8-bit weights.

## 5. Save

`save_assets` saves the landscape with its map and the new Layer Info assets; reopening keeps heights,
paint, edit layers, splines and builds.
