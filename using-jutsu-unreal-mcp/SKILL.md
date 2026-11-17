---
name: using-jutsu-unreal-mcp
description: Jutsu Unreal MCP asset text formats and the facts its tools don't state. Use before changing Unreal assets, levels, landscapes or PIE through Jutsu tools.
---

# Using Jutsu Unreal MCP

The tool descriptions give each tool's parameters; this page routes to the asset-text formats and holds
the facts no single tool states. Blueprints, materials, Niagara, animation, widgets, AI, audio and the
other kinds below have a text form that `read_asset` / `write_asset` / `edit_asset` read and write.
The tools validate, compile, save and report; `run_python` does only what the script does itself
(crash cases: [run-python.md](run-python.md)).
A Lite server (`get_editor_state` has `"edition": "lite"`) writes only plain Blueprints, structs, enums and level actors: [LITE.md](LITE.md).
The rules on reply size and on calls sent while another runs come with the server's MCP instructions, not from this skill.

| Task | Read |
| --- | --- |
| Blueprints: node kinds beyond the basics, switch, Add-pin nodes, delegate binding, RPC flags, function flags, variable types and flags, components, defaults and `Parent:`, dispatchers, interfaces | [blueprint.md](blueprint.md) |
| User structs, user enums, String Tables, Curve assets | [structs-enums-curves.md](structs-enums-curves.md) |
| Widget Blueprints: `WidgetTree`, `[bind ...]` bindings, `Animations`, widget events, driving a widget in PIE | [widget.md](widget.md) |
| Anim Blueprint graphs and `Machine:` state machines; Montage, Anim Sequence, Blend Space | [animation.md](animation.md) |
| Gameplay tags (path `GameplayTags`), tags used in nodes or pins | [gameplay-tags.md](gameplay-tags.md) |
| DataTable `Rows` | [data-table.md](data-table.md) |
| Gameplay Ability System: Gameplay Effects, Abilities, Cues, attribute references | [gas.md](gas.md) |
| Material, Material Function, Material Instance | [material.md](material.md) |
| Sound Cue | [sound-cue.md](sound-cue.md) |
| Niagara System, Emitter and Script assets, `ScratchPad:`; Cascade Particle Systems | [niagara.md](niagara.md) |
| MetaSound graphs, presets | [metasound.md](metasound.md) |
| Behavior Tree, Blackboard | [behavior-tree.md](behavior-tree.md) |
| StateTree, StateTree components | [state-tree.md](state-tree.md) |
| Smart Object definitions and components | [smart-object.md](smart-object.md) |
| Customizable Object (Mutable), Macro Library, instances | [mutable.md](mutable.md) |
| Pose Search (Motion Matching) schemas and databases, Chooser Tables, Proxy Tables | [motion-matching.md](motion-matching.md) |
| Physics: component collision profiles and responses, Static Mesh simple collision (`Collision`), generating collision shapes, Physics Assets and ragdolls (`Physics` section), project collision channels, profiles and surface types (path `Physics`), Physical Materials, Physics Constraint Actors, Geometry Collections (Chaos Destruction) | [physics.md](physics.md) |
| Level Sequences: `Sequence`, `Binding:<Name>`, the `Director` and `Function:` graphs | [level-sequence.md](level-sequence.md) |
| Control Rig, Sequencer Control Rig tracks, baking; IK Rig, IK Retargeter | [control-rig.md](control-rig.md) |
| PCG graphs | [pcg.md](pcg.md) |
| Maps (classic, partitioned): `Actors`, `Actors:<Folder>`, `Actor:<label>`, `Actors@<query>`, the `World` overview, World Partition, Data Layers, HLOD, sublevels, Level Instances | [world.md](world.md) |
| Landscapes: create, sculpt, edit layers, Landscape Patch, paint | [landscape.md](landscape.md) |
| Landscape dressing: roads (splines), Water, PCG scatter, grass, physical material, Nanite builds | [landscape-dressing.md](landscape-dressing.md) |
| Multiplayer PIE, a session's log lines, navigation rebuilds, which editor answers | [pie.md](pie.md) |
| Any `run_python` script: crash gotchas, frame rules, PIE handles | [run-python.md](run-python.md) |

Landscapes, Level Instances, Geometry Collections and their fracture, and Physics Assets go through the plugin's
Python libraries (`unreal.JutsuLandscapeLibrary`, `JutsuLevelLibrary`, `JutsuDestructionLibrary`, `JutsuFractureLibrary`,
`JutsuPhysicsLibrary`; also callable with `call_function`), which `tools/list` does not show; the pages above hold their calls.

A single instanced subobject in `Properties`, `Defaults` or `Parameters` is
`{"class": "InputTriggerPressed", ...}` (`get_properties` adds its `path`, which writes ignore).
**An array of structs or instanced objects is a block, never JSON**: `Name =` and one indented line per
element, `Field=value` items split at spaces with nested members dotted, an instanced element led by its class,
only members that differ from the default, `()` for an all-default element. The lines are the whole array
(drop a line to remove its element; `Name =` alone or `Name = []` clears it):

    DefaultKeyMappings.Mappings =       (UE 5.6 and earlier: Mappings =)
      Action=/Game/Input/IA_Jump.IA_Jump Key=SpaceBar Triggers=[InputTriggerPressed ActuationThreshold=0.75] Modifiers=[InputModifierNegate]
      Action=/Game/Input/IA_Move.IA_Move Key=W Modifiers=[InputModifierDeadZone LowerThreshold=0.3, InputModifierScalar]

Items may come in any order; a read prints a struct's identity fields first (a mapping's `Action` and `Key`; a Gameplay Effect
modifier's `Attribute`, see gas.md), then the rest as the struct declares them. A list in a line is
`Field=[Class a=1, Class b=2]`. In a child Blueprint an element is written against the parent's element at
the same index (`()` keeps it). A member of a struct property is a dotted name, `Struct.Member = value`. A vector,
rotator or colour is also its numbers in order, `Pos=(1,2,3)`, `Tint=(1,0.5,0)`. In a record or flag a left-out number takes the default (child Blueprint: parent's value);
a slot or Control value needs every number; a palette colour's alpha defaults to 1.

The wait of `open_level` for running calls ends after 45 s. `write_asset`, `edit_asset` and
`compile_assets` on a Blueprint of any kind (Actor, Widget, Anim, Control Rig) are refused while PIE
runs, and while actors of it are left in the world of a map that is no longer open (the refusal names them;
a restart drops them). An object path inside a map (`/Game/Maps/L.L:PersistentLevel.Door`) resolves only
while that map is open (`open_level`). Anything without a text section (animation curves and sync markers,
editor utilities) is reachable through `call_function` on Unreal's scripting libraries or `run_python`.
`Properties` lists only what differs from the defaults; a read-only value an import or the engine computed (a Sound
Wave's `Duration`, `NumChannels`, `ImportedSampleRate`; `LUFS`, `SamplePeakDB` from UE 5.7) is read by name with `get_properties`.

Files changed on disk under a running editor (`git checkout`, `pull`, `stash`, `restore`) are not picked up by the editor:
reads show the loaded objects, and the next write saves them over the new file. `reload_assets` without paths compares
each loaded asset of the project with its file (the hash the file was loaded or saved with), so an asset whose file did not
change, or that is not loaded, is left alone; it also registers new files and drops gone ones from the Asset Registry. A
closed map whose files changed is unloaded (the next read loads it); the open level reopens without saving, also for an
actor file added or removed (the reply names the file). Assets, maps and the open level with unsaved changes are kept and named until
`discardUnsavedChanges: true`; an asset made in this session and never saved, where git put a file at its path, is
discarded then (unloaded, the file loads at the next read), never reloaded. The whole call is refused while PIE runs (`stop_pie` first). Each reload clears the undo
history. A file named on `Not compared` (held by another program, damaged, saved by a newer Unreal) or `Unreal did not
reload` still has its old asset in memory: a write would save that over the file. Not judged, so reopen the level
(`open_level`) to read them: a changed file of an unloaded World Partition actor of the open level, and an External Data
Layer or Content Bundle actor file added or deleted while its actor is not loaded.

A write (`write_asset`, `edit_asset`) applies the lines it can and names the rest. When some could not be applied, the reply ends
with a block: `not applied: N lines; the rest was applied and saved, ...`, then each skipped line as `line N: <line>` (numbered
in the whole section, also for `edit_asset`) with its reason indented under it (`depends on line M, which was not applied` for a
line that needed a skipped one). The item a skipped line names stays as it was, name included: a line renaming another item onto that name (`[was=]`) is skipped
too, in every section of `Name: ...` lines (`'X' is the name of another <item>, which stays.`). The
next `edit_asset` matches the stored text. One undo reverts the whole write, skipped lines and all.
A write refuses whole when no line could be applied or a check of the whole call failed. A
section that stays whole, refusing a text with any bad line, says so on its page. The generic `Properties` section (any asset
whose page gives its `Properties` no rules of their own; a Sound Cue's, Geometry Collection's, Niagara System's, Material's and
Material Function's stay whole) writes partially: a line with a
bad value keeps its property's value, and a property with one bad line (a member line, a block element) keeps all of it. A
misspelled name names no property, so the property you meant counts as left out and goes back to its default; a line naming no
property at all (`= 3`) keeps every property the text leaves out.

Unreal sometimes changes another asset with the one a call writes: a material instance first put on a Nanite Static Mesh
gets that usage flag (before UE 5.8 its parent material does), a Blueprint follows a struct it uses.
`create_asset`, `duplicate_asset`, `import_assets`, `write_asset`, `edit_asset`, `set_properties` and `spawn_actor` save those
assets too and name them (`also saved: <paths>`, in a JSON reply `alsoSaved`; `(has compile errors)` after a Blueprint the
change broke). `also changed, not saved: ...` names one that was not saved, with the reason (engine content is never written).
A material on an actor's component or a Skeletal Mesh, or one put on a mesh while PIE runs, may get its flag only when it is
first drawn (after the call, or in `take_screenshot`) and is then left unsaved: `get_editor_state` lists it, `save_assets`
saves it.

Silent results: node positions are not part of the text, so a write that changes a graph lays it out
again; a changed Blueprint default reaches placed instances that kept the old value.

**An asset as a commit holds it**: `read_asset` with `revision` (one commit: `HEAD`, `HEAD~3`, a hash, a branch or tag; not a
range) and any other arguments as usual. The first reply line is `revision <hash>` (plus the name you gave); the tool's hints in
the reply already carry `revision=` (the asset's own text, a comment holding a hint, is shown as stored). Instead of `git show` on
a `.uasset` (binary) or reading two whole versions. It needs the asset's folder in a git work tree and `git` on the editor's PATH
(Source Control settings play no part). Nothing is ever downloaded: a Git LFS object, or a partial clone's file, you never fetched
is refused until you run the `git lfs fetch` / `git fetch` the refusal names. Files over 1 GiB and files kept through another git
filter (git-crypt) are refused. The live asset and its unsaved changes are untouched. References to other assets resolve to
their current versions. Not for `GameplayTags` or `Physics` (refused; `git show <rev>:Config/...` for the settings);
`write_asset` / `edit_asset` take no revision. A map reads with that commit's actor files: the folder sections and
`Actor:<label>` (not `World`, not sublevels' actors; see [world.md](world.md)).

**What changed since a commit**: `read_asset` with `diff=<revision>` (same rules as `revision`). Without `section`: one line per
changed section, `<section>  +<added> -<removed>`, or `added` / `removed (<N> lines)` for a section on one side only, plus a
`class:` / `parent:` line when those changed; `No difference ...` when nothing did (a pattern, `section="Function:*"`, narrows
it). With `section`: that section's unified diff (`@@ -a,b +c,d @@` hunks, lines prefixed ` `, `-`, `+`, `before` / `after`
context lines, default 2; `offset` / `limit` page the diff's lines). The text after the prefix is as a plain read prints it, so a
`+` or ` ` line pastes into `edit_asset` `old_text`. Add `revision=<newer>` to compare two commits instead of a commit and the
live asset. A section only one side has is refused with the read that shows it there; an asset the revision lacks is refused
as added since (read it plainly). Graph nodes are compared in the new side's order, so moved nodes are not changes; then a
hunk's `-a` is where its first old line stands in `read_asset revision=<rev>` and its old lines need not be consecutive
there. Past 2000 changed lines the reply says so: those lines show as all removed, then all added, not as the smallest diff. Use it before reading
two versions whole: on a 1000-line graph with one change the diff is 310 characters, the two reads 70 000. Not with `match`.

**Which assets changed**: `find_assets` with `changed=<revision>` (`HEAD`: the work tree against it, staged or not, untracked
files included) or `changed=A..B` (between two commits) lists assets, not files, with `status` (`modified`, `added`, `deleted`,
`renamed` with `from` for a file moved unchanged, `conflicted`; an Unreal rename rewrites the file, so it lists as deleted and
added); `query`, `class`, `path`, `offset`, `limit` work as usual, `path` also picks the git work
tree. A map's actor and object files (`__ExternalActors__/...` hashes) are counted on the map's row (`changedActors`). A modified
asset (not a map) carries `changes`, the lines `read_asset diff` summarises (`Variables  +1 -0`), compared from copies of its files
for 10 s per call; a row past that, and a modified map, carries `diff`, the `read_asset` call that compares it (for a map with the
work tree as the new side it compares with the open level: open the map first; UE 5.7 reads no map at a revision, so there a
map row carries no call and `note` says why). Changed files that are no assets (source, config) are only counted in
`note`. Nothing is loaded for the list itself; a Git LFS file touched without a change may be listed as modified.

**A merge-conflicted asset**: while git waits for a conflicted `.uasset` to be resolved (merge, rebase, cherry-pick, stash),
`revision` and `diff` take `ours`, `theirs` and `base`, its index stages (in a rebase git's `ours` is the branch rebased onto).
`revision=theirs diff=base` shows what their side changed, `revision=ours diff=base` what yours changed; `diff=theirs` alone
compares theirs with the live asset. The reply's first line says which side the work-tree file holds (git keeps ours for a
binary file) and which bytes the editor holds: a write starts from those, not from the file. When the editor holds a version
it loaded before git wrote the file, `reload_assets` with the path loads the file. A conflicted Git LFS asset's work-tree file
is pointer text with conflict markers, no asset: the sides still read from the local LFS store. The plugin resolves nothing:
take a side or re-apply the other side's changes with `write_asset` / `edit_asset`, save, then `git add` yourself. Outside a
conflict the side names are refused; a branch or tag called `ours` / `theirs` / `base` / `saved` reads by its full name
(`refs/heads/ours`). An asset added on both sides has no `base`; one deleted on a side has no side there.

**Unsaved changes**: `diff=saved` compares the asset's file on disk with what the editor holds, so `read_asset path=<asset>
diff=saved` lists the sections an unsaved change touched (with `section`, its lines) before you save or discard it;
`revision=saved` reads the file as saved. No git needed. An asset with no unsaved changes answers `No difference` at once
(`get_editor_state` lists the unsaved packages). Refused for an asset never saved. A map: the open level against its files,
actor files included (world.md, "Unsaved level edits").
