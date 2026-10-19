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
Naming an optional property in a pin line (`PlayRate = 2`) exposes it as a pin.

Montage `Sections`: `Loop @ 0.5 -> Loop` (seconds, optional next section). Montage and sequence
`Notifies`: `Track: Name` lines, each followed by `  0.25 AnimNotify_PlaySound {"Sound":"..."}`,
`  0.25-0.75 AnimNotifyState_Trail {...}` (a state's start-end) or `  0.5 "Footstep"` (skeleton
notify); one notify per start time on a track; a notify matches by track, time and class. `Sockets`: skeleton `Grip: hand_r {"RelativeLocation":{"X":10}}`,
Static Mesh `Grip {"Tag":"grip"}`. `[was="Old"]` renames a section or socket.
