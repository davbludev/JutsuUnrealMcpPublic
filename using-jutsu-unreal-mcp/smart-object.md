# Smart Object Definition

`Definition` is the whole definition as text:

```
ActivityTags = ["Activity.Sit"]
Parameter Height: float = 20
Behavior GameplayInteractionSmartObjectBehaviorDefinition {"StateTreeReference":{"StateTree":"/Game/AI/ST_Sit.ST_Sit"}}
Slot Left {"Offset":{"Y":-50},"Rotation":{"Yaw":90}}
  Behavior GameplayInteractionSmartObjectBehaviorDefinition {"StateTreeReference":{"StateTree":"/Game/AI/ST_Sit.ST_Sit"}}
  Data SmartObjectSlotEntranceAnnotation {"SelectionPriority":"High"}
    Bind TrajectoryStartHeightOffset = Parameters.Height
  Data SmartObjectSlotLinkAnnotation {"LinkedSlot":"Right"}
Slot Right {"bEnabled":false}
  Bind Offset.Z = Parameters.Height
```

- `Name = <json>`: the definition's own values (tags, user tag filter, `Preconditions`), as in
  `Properties`; world conditions are instanced structs `{"struct": "...", members}`.
- `Parameter Name: type [= value]`, `[was="Old"]` renames (as StateTree parameters).
- `Behavior <class> {json}`: default behaviors at the top, a slot's under it. A Gameplay
  Interaction behavior names its StateTree in `StateTreeReference`, with `"Parameters"` overrides.
- `Slot <name> {json} [was="Old"]`: slots in order (line order is slot order); a slot keeps its id
  through renames and moves, so references and bindings follow. `Data <struct> {json}` under a slot
  adds annotations; a slot reference is the other slot's name.
- `Bind <path> = Parameters.<name>` under the item it targets.
- `Definition` writes partially: a line with a problem is skipped and named under `not applied:`, and the other lines
  are written. What it names stays as it is: a value line its value, a `Parameter` line its parameter, a `Behavior` or `Data`
  line its item, a `Slot` line its slot with everything under it (those lines are skipped with it), a `Bind` line its binding;
  a `Parameter` or `Slot` line keeps the items its name and its `was=` name, the `was=` read even when the rest of the
  line does not read; a `was=` unquoted or with its quote not closed (`[was="Old]`) skips its line so, and so does a
  value Unreal refuses. A line that needs a skipped one is skipped too: a binding to a parameter it meant to add, a
  reference to a slot it meant to add, a rename of or onto an item it names. For `Parameter` and `Slot` lines, also: a
  line whose name an earlier line has (also a skipped one), two lines with one `was=`, a line keeping a name another
  renames away (rename first, reuse the old name in a later write), a new or renamed item under the name of one that
  stays. A text none of whose lines applies is refused and changes nothing.

An actor Blueprint's Smart Object component names the definition in `Components`:
`SO: SmartObjectComponent {"DefinitionRef":{"SmartObjectDefinition":"/Game/SO_Bench.SO_Bench","Parameters":{"Height":30}}}`.
