# StateTree

`Tree` is the whole StateTree as text:

```
Schema StateTreeComponentSchema {"ContextActorClass":"/Game/AI/BP_Guard.BP_Guard_C"}
Parameter Speed: float = 2
Color Danger [R=0.9, G=0.1, B=0.1]
GlobalTask "Global Wait": StateTreeDelayTask {"Duration":4}
State Root
  State Idle
    Task wait: StateTreeDelayTask {"Duration":1.5}
      Duration = Parameters.Speed
    Transition OnStateCompleted -> Patrol [Priority=High, Delay=0.5]
      If odds: StateTreeRandomCondition
        Function Threshold: StateTreeAddFloatPropertyFunction {"Right":0.1}
          Left = Parameters.Speed
  State Patrol [Selection=TrySelectChildrenAtRandom, Color=Danger, TickRate=0.5]
  Linked UseShared -> Shared
  LinkedAsset Combat -> /Game/AI/ST_Combat.ST_Combat
Subtree Shared
  State Inner
```

- States: `State|Group|Linked|LinkedAsset|Subtree Name [flags]`, children two spaces in; line
  order is sibling order (move a line to reorder). Flags are comma separated and shown only when they
  differ from the default; a flag left out goes back to its default; `[was="Old"]` renames. `Selection=`,
  `Tag="A.B"`, `Enabled=false`, `Weight=N`, `Color=Name` (a palette colour), `Prerequisites=false` (skip
  the enter conditions when a transition enters a child directly), `RequiredEvent` (the state is entered
  only while that event is present) with `Event="Tag"`, `EventPayload=Vector` (a struct name or path) and
  `ConsumeEvent=false`; from UE 5.6 `Description="..."`, `TasksCompletion=All` and `TickRate=0.5` (seconds,
  a custom tick rate; `TickRate=0` still counts); from UE 5.8 `CopyParameterBindings`. An unknown flag
  lists the state's flags. Re-indent a line to move a state, with its children and data, under another
  parent; same-named siblings read as `Name #2`.
- Palette: `Color <name> [R=, G=, B=]` lines (A when not 1) before the states are the tree's colours a state
  names with `Color=`; `[was="Old"]` renames, a colour left out is removed, and a state naming a colour
  that is not there is refused with the palette. The default colour, which a state without `Color` has,
  shows only once renamed or recoloured and is never removed.
- Nodes: `Enter|Task|Consideration|Evaluator|GlobalTask <id>: <type> {values}`. The id is the
  node's name; the type a node struct by name (or a Blueprint node class by path). `{values}` are
  the instance data, the node struct's own under `"Node"`. Conditions take `Operand=Or`, `Indent=N` and
  `EvaluationMode=ForcedTrue|ForcedFalse` (skip the condition and force its result); tasks take `Enabled=false`
  and, from UE 5.6, `ConsideredForCompletion=false` (a background task: the state does not wait for it).
- State parameters: `Parameter Range: float = 5` lines first under a state. A `Linked` state's
  parameters are its subtree's: write a `Parameter` line only to override one (same name and type);
  leave it out to take the subtree's value back.
- Bindings: `Prop = <source>` under a node, or `Range = <source>` under a state's `Parameter` line.
  A line reads what the engine lets its target read, as the editor does: `Parameters.<name>` (the
  nearest bag: the state's, its parents', then the root's), `Context.Actor`, `Event.Tag` (in an `If`
  under a `Transition OnEvent`), `EnterEvent.Tag` (the event a state requires with `RequiredEvent`, read by
  that state's nodes and its children's), `<node id>.Output` for the evaluators, global tasks, parent states'
  tasks and the nodes above it in its own state.
- Output bindings (UE 5.7+): a property the node writes (category `Output`) takes the same line,
  `Result = Parameters.Total`, and its value flows into that parameter (a state's or the tree's); the property
  decides the direction. UE 5.6 and below refuse it, naming the lane.
- Property functions (UE 5.7+): `Function <property>: <function struct> {values}` under the node (or `Parameter`
  line) whose property it feeds, e.g. `Function Duration: StateTreeMultiplyFloatPropertyFunction {"Right":3}`
  with `Left = Parameters.Speed` indented under it (or another `Function Left: ...`, to any depth). The function
  struct is a native property function by name (an unknown one lists the allowed); its authored inputs are the
  `{values}`, the rest are binding lines under it. A property takes one binding or one function; left out, the
  function is removed with what is under it; the same struct on the same property keeps its place and takes the
  new values, another struct replaces it. UE 5.6 and below refuse a `Function` line, naming the lane.
- Transitions: `Transition <Trigger> -> <state | Next | Succeeded | Failed | None>` with
  `Priority=`, `Delay=`, `Variance=`, `Event="Tag"`, `EventPayload=Vector`, `ConsumeEvent=false`; conditions are
  `If` lines under it. UE 5.8 adds the targets `Parent`, `NextParent`, `NextSelectableParent` and the flag
  `Reactivate=ForceChanged|ForceSustained` (the target state is re-entered, or kept running; a new value is
  refused unless the tree's editor schema allows it, which the component schema does not). An `OnEvent` transition
  needs `Event` or `EventPayload`.
- Values use the plugin's JSON: enums by name, structs as objects, an instanced struct
  `{"struct": "...", members}`, a parameter bag `{"Speed": 2}`.

`Tree` is the editor's data as lines and the one that carries state parameters. A binding the lines cannot show
stays as it is, and the read says so in a `# note:` line. A StateTree has no `Document` section.

A Blueprint's StateTree component takes the tree and its parameter overrides in `Components`:
`Brain: StateTreeComponent {"StateTreeRef":{"StateTree":"/Game/AI/ST_Guard.ST_Guard","Parameters":{"Speed":3}}}`.
