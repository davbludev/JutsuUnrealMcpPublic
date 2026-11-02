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

Montage `Sections`: `Loop @ 0.5 -> Loop` (seconds, optional next section). Montage and sequence
`Notifies`: `Track: Name` lines, each followed by `  0.25 AnimNotify_PlaySound {"Sound":"..."}`,
`  0.25-0.75 AnimNotifyState_Trail {...}` (a state's start-end) or `  0.5 "Footstep"` (skeleton
notify); one notify per start time on a track; a notify matches by track, time and class. `Sockets`: skeleton `Grip: hand_r {"RelativeLocation":{"X":10}}`,
Static Mesh `Grip {"Tag":"grip"}`. `[was="Old"]` renames a section or socket.
