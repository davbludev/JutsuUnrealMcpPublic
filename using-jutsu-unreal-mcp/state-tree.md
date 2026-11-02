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
- State parameters: `Parameter Range: float = 5` lines first under a state. A `Linked` state's
  parameters are its subtree's: write a `Parameter` line only to override one (same name and type);
  leave it out to take the subtree's value back.
- Bindings: `Prop = <source>` under a node, or `Range = <source>` under a state's `Parameter` line.
  A line reads what the engine lets its target read, as the editor does: `Parameters.<name>` (the
  nearest bag: the state's, its parents', then the root's), `Context.Actor`, `Event.Tag` (in an `If`
  under a `Transition OnEvent`), `<node id>.Output` for the evaluators, global tasks, parent states'
  tasks and the nodes above it in its own state. A node never reads itself or a node below it. From UE 5.6 the engine's console variable
  `StateTree.Compiler.EnableBindingSelectionNodeToInstanceData` (on by default) decides whether an enter
  condition, a consideration or a state parameter may read a task's data; with it off they cannot.
  A refusal names why and lists the sources in reach. An input property of a node (a condition's
  `Left`) is bound, not given in `{values}`.
- Transitions: `Transition <Trigger> -> <state | Next | Succeeded | Failed | None>` with
  `Priority=`, `Delay=`, `Variance=`, `Event="Tag"`; conditions are `If` lines under it. UE 5.8 adds
  the targets `Parent`, `NextParent`, `NextSelectableParent`.
- Values use the plugin's JSON: enums by name, structs as objects, an instanced struct
  `{"struct": "...", members}`, a parameter bag `{"Speed": 2}`.

`Tree` is the editor's data as lines and the one that carries state parameters; `Document` is the
same tree as JSON. State colors, required enter events, tick rates, the prerequisites flag, event payloads,
output bindings and property functions are not lines and stay as they are; a read ends with a
`# note:` line for each state, transition or binding that keeps one (a write ignores notes).

A Blueprint's StateTree component takes the tree and its parameter overrides in `Components`:
`Brain: StateTreeComponent {"StateTreeRef":{"StateTree":"/Game/AI/ST_Guard.ST_Guard","Parameters":{"Speed":3}}}`.
