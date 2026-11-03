# Behavior Tree and Blackboard

A tree is `read_asset(tree, "Tree")` text; its keys are `read_asset(blackboard, "Keys")` text. Edit them
with `edit_asset` or write the whole text back; a write makes the asset match the text, so a line you
leave out is removed.

```
blackboard: /Game/AI/BB_Guard.BB_Guard
BTComposite_Selector "Root"
  decorator BTDecorator_Blackboard "Has target" {"BlackboardKey.SelectedKeyName":"Target"}
  service BTService_DefaultFocus {"Interval":0.7}
  BTComposite_Sequence "Attack"
    decorator expr "Can engage" = or(BTDecorator_Blackboard {"BlackboardKey.SelectedKeyName":"Target"}, not(BTDecorator_Cooldown {"CooldownDuration":4}))
    BTTask_MoveTo "Go" {"BlackboardKey.SelectedKeyName":"Target","AcceptableRadius.DefaultValue":150}
    BTComposite_SimpleParallel
      main: BTTask_Wait {"WaitTime.DefaultValue":3}
      background: BTComposite_Sequence
        BTTask_Wait
    BTT_FireWeapon "Fire"
  BTTask_RunEQSQuery "Find cover"
```

Workflow for a new AI:

1. `create_asset` a `BlackboardData`, then write its `Keys`: `Target: Object<Actor>`, `Goal: Vector`, `HasTarget: Bool`.
2. `create_asset` a `BehaviorTree` (its editor graph is built; no editor needs opening). Write `Tree` with the
   `blackboard:` line first and one root composite.
3. Read `Tree` back: it is the stored form. Settings you did not write are class defaults and do not show.

Rules worth knowing before the first write:

- `read_asset(tree, "Kinds:Tree@Wait")` lists the node classes that exist.
- Settings are plain JSON by path. Bind a key with `{"BlackboardKey.SelectedKeyName": "Target"}`; a value that is a
  literal or a key is `{"WaitTime.DefaultValue": 5}` or `{"WaitTime.Key": "WaitFor"}`.
- To insert a node in front of others keep their lines as they are and add yours; to move a node, move its line.
  Give a node an `#id` when you need to rename it and keep its settings.
- Renaming a key is a `was=` flag, never a delete and add:

```
Destination: Vector [was="Goal"]
```

- Key settings: `[synced, useDefault, category="Combat", description="..."]`; `Enum<ENetRole>` takes a C++ enum
  name or an Enum asset path, `Struct<Vector>` a struct. Everything else about a key type (a default value) is `Properties`.
- `Document` is the same tree as JSON; it keeps nodes it does not list unless `"exact": true`. Use `Tree` unless you
  need the JSON.
