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

A write is validated like the Smart Object editor does; the reply ends with `validate:` lines.

An actor Blueprint's Smart Object component names the definition in `Components`:
`SO: SmartObjectComponent {"DefinitionRef":{"SmartObjectDefinition":"/Game/SO_Bench.SO_Bench","Parameters":{"Height":30}}}`.
