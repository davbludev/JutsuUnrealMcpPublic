# Maps (actors as text, World Partition, Data Layers, sublevels, Level Instances)

The open map reads and writes as text in these sections (`read_asset(<map>)` lists them; all but `Actors@` refuse
another map: `open_level` it first; with `revision` any map reads as a commit holds it, below):

| Section | Holds |
| --- | --- |
| `Actors`, `Actors:<Folder>` | one line per loaded actor of an Outliner folder: class, place, attachment, sublevel, Data Layers |
| `Actor:<label>` | one actor's properties and components |
| `Actors@<query>` | the placeable classes; one class's components and properties (read-only, any map) |
| `World` | the overview (read-only): partitioned or not, Outliner folders (`Props/Small: 2 actors, 1 not loaded`), sublevels, Data Layers, Level Instances, actors loaded and not loaded |

`list_actors` rows add `level`, `dataLayers` and `levelInstance` where they apply, and a partitioned map's reply
counts `unloadedActors`; unloaded actors are listed through the World Partition calls below. `list_actors` `folder`
lists one Outliner folder and its subfolders, any name. `spawn_actor`, `delete_actors`
and `set_actor_transform` act on single actors.

## Actors as text (folder sections)

`read_asset(<open map>, "Actors")` holds the actors outside any folder, `"Actors:Props/Small"` one folder (not its
subfolders); the outline lists the folders with their counts (in a very big map they are one `Actors:<name>` entry that names every folder; `section="Actors:Props/*"` lists them with counts). `spawn_actor` takes `folder` (`Props/Small`): the new
actor lands in that folder and reads in `Actors:Props/Small` (refused while a Level Instance is being edited, whose
level the folder sections leave out). Classes hidden from the Outliner never show in folder sections.

```text
Lamp PointLight at 100,0,50 [rot=0,90,0]
"Prop One" /Game/Props/BP_Prop at 0,200,0 [scale=2]
# note: 3 actors in this folder not loaded
```

- Line: `<Label> <Class> at x,y,z`, then only what differs from the default: `[rot=pitch,yaw,roll]`,
  `[scale=s]` or `[scale=x,y,z]`, `[attach=Parent]` or `[attach=Parent.Socket]`, `[layers=A,B]`,
  `[level=Sub_A]`, and for a Level Instance `[map=/Game/Maps/L_Room]`. Quote a label with spaces. The class is a
  native class name or a Blueprint path.
- `attach` names the parent by label (a line of the same write or an actor of any folder; by its `[name=]` value when
  two actors share the label, as reads print it), `.Socket` a socket of the parent's attach component (its root,
  usually). `at`/`rot`/`scale` are then relative to the parent; leave `attach` out to detach. A parent and its
  children share a level: move them together.
- `layers` sets exactly those Data Layers (create layers with `run_python`). `level` moves the actor to a loaded
  sublevel (its map's name or path; the actor becomes a new object with a new object name); leave it out for the
  persistent level. A Level Instance is one line (`LevelInstance` class plus `map`); its inner actors are not
  listed. An unknown socket, layer or sublevel is refused listing the choices.
- Folder sections write partially: a line with a problem (unknown class, bad place, unknown socket, layer or sublevel,
  ambiguous label...) is skipped and named under `not applied:` with its reason, and the other lines are written. The
  actor a skipped line names (by label, `[was=]` or `[name=]`) stays as it was and is not removed; another line that
  renames or takes that actor is skipped too; a line attached to a skipped line's actor is skipped, naming that line; a
  line whose label or markers cannot all be read removes nothing. An actor Unreal will not delete stays and is named
  under `not applied:`; the others left out are still removed (an empty text clears the rest of the folder). A text
  that changes nothing is `No change.`; one with skipped lines none of which applies, or whose applied lines and
  removals change nothing, is refused, changing nothing. A step Unreal itself refuses (`see get_log`) rolls the whole
  write back.
- A write is the folder's whole state: a new label places an actor in that folder (in the persistent level unless
  `level` says otherwise), a changed place moves it, a label left out is removed. A changed class recreates the
  actor, keeping its tags, regular Data Layers and parent (its children keep their offset; mobility is kept only
  when it is attached or has children; editor Layers are not kept).
- Writing a new folder creates it; empty text removes its loaded actors, and the folder too when no unloaded actor,
  subfolder or unlisted actor is left in it. Actors not loaded (World Partition), actors the Outliner hides (the
  level Blueprint's) and system actors (World Settings, navigation data, HLOD, landscapes, foliage and PCG
  partition actors...) are never listed and never removed; a folder holding one stays. Edit landscapes with the
  landscape tools ([landscape.md](landscape.md)). Folder names hold no `@`; a folder made by hand with one has no
  section: a `# note:` line of the outline and of `match` searches names it with its counts (searches skip its actors).
  List them with `list_actors folder=<folder>`, move one to a folder with a section by `run_python`:
  `actor.set_folder_path("Other")`.
- Removing a parent detaches its children in other folders where they stand; the reply names them in a `warning:`.
- Stop PIE before writing. The map stays unsaved until `save_assets`.
- The label is the actor's identity. Writing a label of another folder's actor moves that actor into this
  folder. `[was="Old"]` renames (`Light PointLight at 0,0,50 [was=Lamp]`). `[new]` places another actor with a
  label already in use. A label two actors share reads with `[name=<ObjectName>]` (`[name=<Level>:<ObjectName>]`
  when sublevels repeat the object name): keep it when writing, since a line two actors could match is skipped
  listing their names. A write that makes a label shared, or a `level` move (a new object), names the new `[name=]`
  in its reply (`ids:`). To swap two labels, put `[name=]` on both lines or rename in two writes.

## Which classes (`Actors@<query>`)

`read_asset(<map>, "Actors@Light")` (read-only) lists the placeable actor classes and the addable component classes
whose name, short name or description holds the query, native and Blueprint, one `Name (also ShortName) - detail`
line each; `"Actors@"` alone lists them all (the project's Blueprints come first). A
Blueprint is named by its asset path.

```text
/Game/Props/BP_Door (also BP_Door) - Blueprint, parent Actor
PointLight - native, parent Light
PointLightComponent - native component, parent LocalLightComponent
```

A query that names one class (`Actors@PointLight`, `Actors@BP_Door`, `Actors@/Game/Props/BP_Door`), or matches only
one, lists that class's components and editable properties instead: the `Component` lines `Actor:<label>` shows for
it, the properties `Actor:<label>` takes (`Name - Type`, an enum's values after its type), and each kind of
component's, written `<Component>.<Name> = value`. A component class (`Actors@PointLightComponent`) lists its
properties. A name that is exact lists its class even when it cannot be placed (abstract, deprecated), with a note
saying why; two Blueprints sharing a name list both, pass the path. The refusals for an unknown class, property or
component in the folder and `Actor:` sections name this section.

## One actor as text (`Actor:<label>`)

`read_asset(<open map>, "Actor:Lamp")` holds one actor's details: its properties that differ from its class
defaults, its components, and their properties that differ from theirs. Values are spelled as in `Properties`.

```text
Tags = ["Lit"]
Component LightComponent0: PointLightComponent [inherited]
LightComponent0.Intensity = 1234
Component Fill: PointLightComponent [attach=Holder]
Fill.Intensity = 50
Component Holder: SceneComponent
```

- `Component <Name>: <Class>`: `[inherited]` marks a component of the actor's class, which stays (left out, it
  stays as it is and is named under `not applied:`; its class and attachment cannot change). A new line adds an instance component; one left out is
  removed. `[attach=Parent]` or `[attach=Parent.Socket]` hangs it on another component; without it, on the root.
  A name with a space is quoted on its line (`Component "Static Mesh": ...`) and bare before a property
  (`Static Mesh.CastShadow = false`); one with `:` or `=` is quoted in both places. The root keeps its class and hangs on nothing.
- `<Name>.<Prop> = value` sets a component's property, `<Prop> = value` the actor's. A property left out goes back
  to its default. The place (the root's location, rotation, scale) is the folder line's, not here.
- The actor is named as folder lines name it: its label (another letter case works), its object name
  (`Actor:PointLight_3`), `<Level>:<ObjectName>` when sublevels repeat the object name, or the label with the
  `[name=]` a folder read prints (`Actor:Post [name=PointLight_3]`). Labels are looked up first. A label or object
  name two actors share is refused, listing the `Actor:` form of each. An actor no folder section lists is refused,
  and so is a write that changes an actor of a locked level. The section writes partially: an unknown property or
  component, a value that does not fit (or a collision profile the project lacks), skips its line (named under
  `not applied:` with the choices; `Actors@<class>` lists them all) and the rest is written. A skipped property keeps
  its value (it is not reset like one left out), a skipped component line keeps that component as it is (and its
  parent, and its place on it), and the lines of its properties and components attached to it are skipped too; another
  line naming the same component or property is skipped as well, and so is a line writing the edit-condition toggle
  of a skipped property, or recreating a kept component's parent as a class that cannot hold it. A parent left out
  stays while a kept component hangs on it (a `note:` line says so). A line whose name cannot be read (a quote that
  does not end) keeps everything: nothing is removed or reset. A text that changes nothing is `No change.`; one none of whose
  lines changes anything while some are skipped is refused, changing nothing. `save_assets` saves the map; in a partitioned map it also
  writes the dirty actor files (`/Game/__ExternalActors__/...`) and counts them in `Also saved with them:` (`list: true` names them). An actor
  file's path saves that file alone (an unsaved deleted actor's file is deleted, counted in `Deleted the files of`); one
  that is not loaded, or holds no actor and is not among the unsaved, is refused.
- World Settings is not text: read and change it with `get_properties` / `set_properties` on its actor,
  `object: "WorldSettings"` (`set_properties(object="WorldSettings", values={"KillZ": -5000})`).

## A map at a git revision or as saved (`revision`, `diff`)

Not in UE 5.7 (refused there: read the map in a checkout of that commit). `read_asset(<map>, revision="HEAD~2")` reads the
map as that commit holds it, with that commit's actor and folder files
(never the work tree), also a map that is not open or was deleted since: the folder sections and `Actor:<label>`, as
the open map reads. Every actor of the commit is there (no "not loaded"), but only the section you ask for loads its
actors: read one folder or one actor rather than searching the whole map. Not `World` (refused), not the actors of
sublevels, External Data Layers or Content Bundles: a `# note:` line says so; landscape proxies are not read (a note counts them).

`read_asset(<map>, diff="HEAD")` compares that commit with the open map (open it first; for a closed map add
`revision=` to compare two commits). The summary lists the changed folder sections with `+added -removed` lines and
`Actor:<label>  added` / `removed` / `+a -r` for actors placed, deleted or with other properties; `section="Actors:Props"`
shows the changed lines. An actor moved to another folder shows as `-` in the old folder and `+` in the new one; a
relabelled one as `Actor:<old>` removed and `Actor:<new>` added. Actors the open map has not loaded (World Partition) are
left out of the old side too, so they never show as removed; a change inside one does not show (a `# note:` line counts
them: load them to compare). The open map is compared as the commit is read: its sublevels', External Data Layers' and
Content Bundles' actors are left out (a `# note:` line counts them), so they never show as added; nor do folders the
commit cannot hold (an empty folder of a map without folder files, a folder of sublevel actors only).
`section="Actors:Props*"` compares the folders the pattern fits. An actor or folder file of the commit saved by a newer
engine or plugin refuses the whole read or diff, naming the file. A read or diff has 30 s: a section
not loaded whole in time is never compared but listed under `Not compared` with the call that compares it alone (use it); a
map whose files git cannot give within that time is refused (read it in a checkout). Every call reads all the map's actor
files first (about 7.5 s per side for 10 000 actors): from some thousands of actors on, a summary is partial, so diff one
folder or one actor (`section=`) instead. A label an unloaded actor shares now
reads with `[name=]` in every read. Conflict sides are refused for maps.

**Unsaved level edits**: `read_asset(<open map>, diff="saved")` compares the open level with its files on disk (the `.umap`
and its actor and folder files; no git needed), in the same summary and `section=` forms: an actor moved shows in its
folder's lines, one placed and not saved as `Actor:<label>  added`, one deleted and not saved as `removed`. A level with no
unsaved changes answers `No difference` at once; otherwise the `.umap` and only the unsaved actor and folder files are read,
so it stays fast on an open world. A folder renamed and not saved shows as its old name removed and its new name added. The
map must be open; `revision="saved"` reads the map as saved. Unsaved landscape proxies and External Data Layer packages are
not compared (a `# note:` line counts them). UE 5.7 refuses it while anything is unsaved, and `revision="saved"` always:
`get_editor_state` lists the unsaved packages by name there.

The rest is `run_python` recipes for UE 5.5-5.8 (a line names its lane where they differ). Use the subsystems below
(`EditorLevelLibrary` is deprecated). Each call finishes its work before it returns: read the actors in
the same call (`eas.get_all_level_actors()`; `list_actors` shows loaded actors only).

```python
import unreal
WPL = unreal.WorldPartitionBlueprintLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ds = unreal.get_editor_subsystem(unreal.DataLayerEditorSubsystem)
ls = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
save = lambda: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
```

After a save of a partitioned map, World Partition can drop an actor saved for the first time (a new landscape) out of
the actor queries for one frame. `save_assets` answers once such actors are back (it waits 2 s at most and then names any still missing); after `save()` in a script, the next
call can still miss them for that frame.

New map: `ls.new_level("/Game/Maps/Wp", True)` partitioned (the second argument is `is_partitioned_world`),
`ls.new_level("/Game/Maps/Cl")` classic. It saves the new map and opens it in place of the current one.
Open an existing map with the `open_level` tool.

## World Partition

A partitioned map opens with only its non-spatial actors loaded; every actor stays listed.

```python
descs = WPL.get_actor_descs()   # loaded or not; None on a classic map
# d.label is a Name: str(d.label) is the actor label; d.guid.to_string(); d.native_class;
# d.is_spatially_loaded; d.bounds; d.data_layer_assets (for an asset layer, p.export_text() is its path)
box = unreal.Box(unreal.Vector(0, -5000, -5000), unreal.Vector(60000, 5000, 5000))
WPL.load_actors([d.guid for d in WPL.get_intersecting_actor_descs(box)])   # load a region
WPL.unload_actors(guids)            # undoes load_actors; a pinned actor stays
WPL.pin_actors(guids)               # loads and holds
WPL.unpin_actors(guids)             # unloads an actor only the pin held
WPL.get_editor_world_bounds(); WPL.get_runtime_world_bounds()   # unreal.Box, is_valid
```

## Data Layers

```python
p = unreal.DataLayerCreationParameters(); p.is_private = True
priv = ds.create_data_layer_instance(p)        # lives in the map
asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset("DL_A", "/Game/Maps", unreal.DataLayerAsset, unreal.DataLayerFactory())
p = unreal.DataLayerCreationParameters(); p.data_layer_asset = asset
inst = ds.create_data_layer_instance(p)        # the map's instance of the asset
ds.add_actors_to_data_layer(actors, inst); ds.remove_actors_from_data_layer(actors, inst)
ds.get_actors_from_data_layer(inst)
{d.get_data_layer_short_name(): d for d in ds.get_all_data_layers()}
ds.set_data_layer_visibility(inst, False)      # d.is_visible() reads it back
ds.set_data_layer_is_loaded_in_editor(inst, False, False)   # (layer, is_loaded, is_from_user_change): False unloads the layer's actors, True loads them
ds.delete_data_layer(inst)
```

While a layer is off, `load_actors` skips its actors. A layer's unloaded actors list it in
`d.data_layer_assets`. The loaded toggle acts on actors the session does not hold: an actor created or
changed in this session stays loaded even after `save()`. To toggle by layer, `save()`, reopen the map
(`open_level` another map, then this one), then toggle.
`set_data_layer_is_loaded_in_editor` always returns `True`; read the flag with
`unreal.JutsuLevelLibrary.is_data_layer_loaded_in_editor(inst)`.

## HLOD

Give the actors a mesh with `comp.set_editor_property("static_mesh", mesh)` (it marks them dirty;
`set_static_mesh` does not, so `save()` would skip them), leave their HLOD Layer unset (a new partitioned
map has a default one), and `save()` so no actor in the set is dirty: 5.8 answers `False` and builds
nothing while one is.

- UE 5.8: `unreal.WorldPartitionHLODBlueprintLibrary.build_hlod_for_actors(actors)` or
  `.build_hlod_for_volume(box)` blocks (seconds), returns `True` and leaves `WorldPartitionHLOD` actors
  in the map unsaved: `save()` again.
- UE 5.5-5.7 have no Python build: use the commandlet below.

## Sublevels (classic map)

```python
unreal.EditorLevelUtils.create_new_streaming_level(unreal.LevelStreamingAlwaysLoaded, "/Game/Maps/Sub_A", False)  # (class, path, move_selected_actors_into_it); becomes current
unreal.EditorLevelUtils.add_level_to_world(world, "/Game/Maps/Sub_A", unreal.LevelStreamingDynamic)   # an existing map
ls.set_current_level_by_name("Sub_A")           # the map's own name returns to the persistent level
stream = unreal.GameplayStatics.get_streaming_level(world, "Sub_A"); stream.is_level_visible()
level = [l for l in unreal.EditorLevelUtils.get_levels(world) if l.get_outer().get_name() == "Sub_A"][0]
unreal.EditorLevelUtils.set_level_visibility(level, False, False)   # (level, should_be_visible, force_layers_visible)
unreal.EditorLevelUtils.move_actors_to_level(actors, stream)    # returns the moved count; actor.get_level().get_outer().get_name() names a level
unreal.EditorLevelUtils.remove_level_from_world(level)   # also clears the selection and resets the undo history
```

`spawn_actor` and `eas.spawn_actor_from_class` place into the current level. `save()` saves the sublevel with the map.

## Level Instances and Packed Level Actors

The engine's script surface cannot create, edit or pack them; the plugin's `unreal.JutsuLevelLibrary` does
(same calls in `call_function`, object `JutsuLevelLibrary`). A function that cannot do what its name says
raises a `RuntimeError` naming the reason, so a script stops at the failed step.

```python
lib = unreal.JutsuLevelLibrary
all_actors = lambda: unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)   # includes actors inside instances
find = lambda label: next(a for a in all_actors() if a.get_actor_label() == label)
inst = lib.create_level_instance([a, b], "/Game/Maps/LI_Room")       # new map (must not exist), saved; the actors move into it
inst = lib.create_level_instance([a, b], "/Game/Maps/LI_Room", True)  # a Packed Level Actor + BPP_LI_Room beside the map
lib.edit_level_instance(inst)         # its level becomes current: spawn_actor and eas.spawn_actor_from_class land inside it
inst = lib.commit_level_instance(inst)   # saves the edit and returns the actor (keep the result: a packed one is replaced); (inst, True) discards it
moved = lib.break_level_instance(inst)    # the actors return to the parent level and are returned
lib.set_level_instance_loaded(inst, False)   # (inst, True) loads: both return with the actors in place (or gone); break loads an unloaded one itself
st = lib.get_level_instance_status(inst)     # st.asset, st.loaded, st.loading, st.editing, st.dirty
bp = lib.pack_level_blueprint("/Game/Maps/LI_Room")   # create or update /Game/Maps/BPP_LI_Room, saved; no prompt
```

- The actors are re-created inside the new map: `a` and `b` are stale after `create_level_instance`; find them again
  by label with `all_actors()`. `eas.get_all_level_actors()` leaves out what is inside an instance; `list_actors`
  includes it.
- The instance sits at the pivot (the optional 4th argument `unreal.JutsuLevelInstancePivot`: `CENTER_MIN_Z`
  default, `CENTER`, `WORLD_ORIGIN`, `FIRST_ACTOR`); the actors keep their world positions.
- One script can enter, place and leave: `edit_level_instance(inst)`, spawn, `inst = commit_level_instance(inst)`.
  One edit at a time: editing another instance raises until the first is committed or discarded. `open_level` while an edit is open saves it and ends it.
- `create_level_instance` saves the new map but leaves the parent map unsaved (`save()` it); `edit`, `break` and `pack` reset the undo history.
- A reopened map fills its instances over the next ticks, and a committed Packed Level Actor leaves its level unloaded (it shows
  its packed meshes): `lib.set_level_instance_loaded(inst, True)` waits for the actors.
- Place the packed Blueprint with `spawn_actor` (`class` `/Game/Maps/BPP_LI_Room.BPP_LI_Room_C`); after the map
  changed, `pack_level_blueprint` again updates it.

## Commandlets (separate process)

Converting a map to World Partition, building the minimap and (UE 5.5-5.7) building HLODs have no Python
route. Save the map, then run `Engine/Binaries/Win64/UnrealEditor-Cmd.exe <Project>.uproject <args>
-unattended -nosplash` from a shell. A `-run=` commandlet loads no Jutsu module (`EditorNoCommandlet`), so
it takes no MCP port and does not clash with an open editor. Success is `finished execution (result 0)` in the log; a cold start takes minutes.

- Convert: `-run=WorldPartitionConvertCommandlet /Game/Maps/Cl -ConversionSuffix -AllowCommandletRendering`
  writes `/Game/Maps/Cl_WP` and merges always-loaded sublevels into it; the source stays.
- Minimap: `/Game/Maps/Wp -run=WorldPartitionBuilderCommandlet -Builder=WorldPartitionMiniMapBuilder -AllowCommandletRendering`
  fills the map's `WorldPartitionMiniMap` actor.
- HLOD (5.5-5.7): `/Game/Maps/Wp -run=WorldPartitionBuilderCommandlet -Builder=WorldPartitionHLODsBuilder -SetupHLODs -BuildHLODs -AllowCommandletRendering`.
