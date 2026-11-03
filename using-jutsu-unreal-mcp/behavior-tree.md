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

- Classes are native names (`BTTask_Wait`), `/Script` paths, a Blueprint node's short name or its asset path.
  `read_asset(tree, "Kinds:Tree@Wait")` lists the classes that exist; a wrong name's refusal lists them too.
- A decorator or service is a `decorator ...` / `service ...` line under the node it belongs to, before that
  node's children. Tasks take no children. One composite is the root.
- A Simple Parallel's children are `main:` (one task) and `background:`.
- Settings are plain JSON by path. Bind a key with `{"BlackboardKey.SelectedKeyName": "Target"}`; a value that is a
  literal or a key is `{"WaitTime.DefaultValue": 5}` or `{"WaitTime.Key": "WaitFor"}`. A key the blackboard lacks is
  refused with the keys it has.
- Lines match existing nodes by `#id`, else by class and name, else by place. To insert a node in front of others
  keep their lines as they are and add yours; to move a node, move its line. Give a node an `#id` when you need to
  rename it and keep its settings.
- Renaming a key is a `was=` flag, never a delete and add:

```
Destination: Vector [was="Goal"]
```

  Every tree that uses the blackboard gets its bindings repaired and saved. Deleting a key line leaves the trees' bindings
  to it empty after their next save.
- Key settings: `[synced, useDefault, category="Combat", description="..."]`; `Enum<ENetRole>` takes a C++ enum
  name or an Enum asset path. Everything else about a key type (a default value) is `Properties`.
- `Document` is the same tree as JSON (`root`, `decorators`, `services`, `children`, `authoringId`); it keeps
  nodes it does not list unless `"exact": true`. Use `Tree` unless you need the JSON.
