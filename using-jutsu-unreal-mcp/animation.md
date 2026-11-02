# Animation graphs, montages, notifies and sockets

Anim Blueprint graphs use the same text: `Function:AnimGraph`, a state's pose graph
`State:Locomotion/Idle`, a transition rule `Transition:Locomotion/Idle->Run`. Anim nodes are their
class without `AnimGraphNode_` (`SequencePlayer {"Node":{"Sequence":"/Game/A_Run.A_Run"}}`,
`BlendListByBool`, `LocalRefPose`); poses link like values; `StateMachine Locomotion` is a machine
(another name renames it). The result node (`Root`, `StateResult`, `TransitionResult`) stays:

```
sm StateMachine Locomotion
out Root
  Result = sm.Pose
```
```
speed Get Speed
fast Call KismetMathLibrary.Greater_DoubleDouble
  A = speed
  B = 10
out TransitionResult
  bCanEnterTransition = fast.ReturnValue
```

States, the entry and transitions are added in `Document`; their graphs then appear as sections.
A machine clause lists only what it changes: a transition's `from`/`to` name a state alias of the
clause or an existing state's name, so `{"find": {"name": "Locomotion"}, "transitions": {"back":
{"create": {"from": "Run", "to": "Idle"}}}}` needs no `states`. A transition, state or machine sets
its settings in `properties`: `{"CrossfadeDuration": 0.15}`. Supported: transition `PriorityOrder`, `CrossfadeDuration`, `BlendMode`, `CustomBlendCurve`,
`bAutomaticRuleBasedOnSequencePlayerInState`, `AutomaticRuleTriggerTime`, `MinTimeBeforeReentry`,
`SyncGroupNameToRequireValidMarkersRule`, `LogicType`, `Bidirectional`, `bDisabled`,
`bOnlyEvaluateWhenActive`; state `bAlwaysResetOnEntry`; machine `MaxTransitionsPerFrame`,
`MaxTransitionsRequests`, `bSkipFirstUpdateTransition`, `bReinitializeOnBecomingRelevant`,
`bCreateNotifyMetaData`, `bAllowConduitEntryStates`. The read lists only
settings changed from their defaults, so a fresh transition reads `"properties": []`.
Naming an optional property in a pin line (`PlayRate = 2`) exposes it as a pin; `PlayRate [hidden]`
(a line with no value) hides it again; `hidden` stays an ordinary value and node id.

Anim node properties show member by member; only instanced members (a Control Rig node's
`Node.AssetUserData`, an IK Rig node's `Node.GoalCreators`) stay out of the text and unchanged by a write. A `ControlRig` node takes its
rig in `{"Node":{"ControlRigClass":...}}` on UE 5.5-5.7 and `{"Node":{"ControlRigAssetReference":...}}`
on 5.8, and its rig-variable pins by name (`Speed = 2`). `Pin = @Owner.Path` binds a pin to a
property access path (a variable, a member chain, or a function as the last element); a bound pin
reads the same way. Node settings like `UpdateFunction`, `InitialUpdateFunction`, `BecomeRelevantFunction`
take a function reference; a `Function:` section whose entry is `FunctionEntry() [ThreadSafe]` is
thread-safe (flags `[Pure] [Const] [ThreadSafe] [Category "x"] [Keywords "y"]`, after the parentheses).

Cached poses: `SaveCachedPose Name` stores a pose, `UseCachedPose Name` links to it by that name
(a rename of the save node keeps the links). Pose-list nodes (`LayeredBoneBlend`, `BlendListByInt`,
`MultiWayBlend`) grow inputs when a pin line names one that does not exist yet (`BlendPoses_1 = x.Pose` and
`BlendWeights_1 = 0.5` on `LayeredBoneBlend`, `BlendPose_2 = x.Pose` on `BlendListByInt`); a pose output
holds one link, so each input takes its own node.

Anim layers: writing a `Function:<Layer>` that does not exist makes an anim layer (an animation graph
with its own `Root`) in an Anim Layer Interface, and in an Anim Blueprint when the text has a `Root` or
`LinkedInputPose` line; without one it is a plain function. Layers an Anim Blueprint implements from an interface are `Function:` sections too. Put
`LinkedInputPose` nodes on it for its inputs. A layer's machines, and machines nested in a state's
graph, are read in the Document with `"graph": "<Layer or State graph name>"`; name it in a `create`
clause to place the machine there. Cached-pose workflow: `SaveCachedPose Name` in one graph (usually the
AnimGraph), `UseCachedPose Name` in a layer or state graph of the same Blueprint.

In the Document a machine clause also takes `conduits` and `aliases` beside `states` (one key
namespace; a conduit's rule is its `State:` section; an alias takes `global: true` or `states: [keys]`).
Transitions to and from them are ordinary clauses. A transition with `"LogicType": "TLT_Custom"` gets a
section `Blend:Machine/From->To` (`TransitionPoseEvaluator` nodes `from`/`to` feed `out
CustomTransitionResult`); another logic type removes it. Settings the engine lane lacks are refused
with the list the lane has (`BlendProfile` on 5.5, `BlendProfileWrapper` from 5.6,
`bAllowInertializationForSelfTransitions` from 5.7). A `// note:` line in a Document read names
what it cannot show (a transition with an end that links to no state, conduit or alias). Not authorable here:
shared transition rules, anim notify events, and linked-layer slot setup; use `run_python` for those.

Montage `Sections`: `Loop @ 0.5 -> Loop` (seconds, optional next section). Montage and sequence
`Notifies`: `Track: Name` lines, each followed by `  0.25 AnimNotify_PlaySound {"Sound":"..."}`,
`  0.25-0.75 AnimNotifyState_Trail {...}` (a state's start-end) or `  0.5 "Footstep"` (skeleton
notify); one notify per start time on a track; a notify matches by track, time and class. `Sockets`: skeleton `Grip: hand_r {"RelativeLocation":{"X":10}}`,
Static Mesh `Grip {"Tag":"grip"}`. `[was="Old"]` renames a section or socket.
