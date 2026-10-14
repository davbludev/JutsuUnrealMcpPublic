# StateTree

`Tree` is the whole StateTree as text:

```
Schema StateTreeComponentSchema {"ContextActorClass":"/Game/AI/BP_Guard.BP_Guard_C"}
Parameter Speed: float = 2
GlobalTask "Global Wait": StateTreeDelayTask {"Duration":4}
State Root
  State Idle
    Task wait: StateTreeDelayTask {"Duration":1.5}
      Duration = Parameters.Speed
    Transition OnStateCompleted -> Patrol [Priority=High, Delay=0.5]
      If odds: StateTreeRandomCondition {"Threshold":0.25}
  State Patrol [Selection=TrySelectChildrenAtRandom]
  Linked UseShared -> Shared
  LinkedAsset Combat -> /Game/AI/ST_Combat.ST_Combat
Subtree Shared
  State Inner
```

- States: `State|Group|Linked|LinkedAsset|Subtree Name [markers]`, children two spaces in; line
  order is sibling order (move a line to reorder). Markers: `Selection=`, `Tag="A.B"`,
  `Enabled=false`, `Weight=N`, UE 5.6+ `Description="..."`, `TasksCompletion=All`;
  `[was="Old"]` renames. Re-indent a line to move a state, with its children and data, under
  another parent; same-named siblings read as `Name #2`.
- Nodes: `Enter|Task|Consideration|Evaluator|GlobalTask <id>: <type> {values}`. The id is the
  node's name; the type a node struct by name (or a Blueprint node class by path). `{values}` are
  the instance data, the node struct's own under `"Node"`. Conditions take `Operand=Or`, `Indent=N`.
- Bindings under a node: `Prop = Parameters.Speed`, `Context.Actor`, or `<node id>.Output`.
- Transitions: `Transition <Trigger> -> <state | Next | Succeeded | Failed | None>` with
  `Priority=`, `Delay=`, `Variance=`, `Event="Tag"`; conditions are `If` lines under it.
- Values use the plugin's JSON: enums by name, structs as objects, an instanced struct
  `{"struct": "...", members}`, a parameter bag `{"Speed": 2}`.

State colors, required events, tick rates, state parameters and output bindings are not in the
text and stay as they are.

A Blueprint's StateTree component takes the tree and its parameter overrides in `Components`:
`Brain: StateTreeComponent {"StateTreeRef":{"StateTree":"/Game/AI/ST_Guard.ST_Guard","Parameters":{"Speed":3}}}`.
