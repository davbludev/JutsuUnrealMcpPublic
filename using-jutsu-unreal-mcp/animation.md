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

A machine of the AnimGraph is section `Machine:<Name>`: its states, conduits, aliases, entry and
transitions, one line per item; their graphs then appear as sections. A machine in an anim layer is
`Machine:<Layer>/<Name>`, one inside a state's pose graph `Machine:<State>/<Name>`
(`Machine:<Machine>/<State>/<Name>` when another animation graph has that state's name; a layer's plain
name always names the layer). The outline lists them; a path naming no such graph or machine is refused
with the sections there are. The machine node itself is a `StateMachine <Name>` line in the graph that
holds it (`Function:<Layer>`, `State:<Machine>/<State>`).

```
machine [MaxTransitionsPerFrame=2]
entry Idle
state Idle
state Run [bAlwaysResetOnEntry=true]
conduit CanStop
alias Anywhere [global]
alias Moving [Walk, Run]
Idle -> Run [CrossfadeDuration=0.15]
Idle -> Run #2 [LogicType=TLT_Custom, rule=true]
```

Writing makes the machine match: an item or transition left out is removed with its `State:`,
`Transition:` or `Blend:` section; `state Jog [was="Walk"]` renames and keeps the pose graph. States,
conduits and aliases share one name namespace; an alias covers states. Settings are property names,
shown only where they differ from a newly placed item's; a mistyped name or enum value is refused
with the lane's choices. A second transition with the same ends is `#2` in graph order, as its
`Transition:` section; writing only `A -> B #2` keeps that one and removes the first (it then reads
`A -> B`). Notify events are settings by event name: a state's `StateEntered`, `StateLeft`,
`StateFullyBlended`, a transition's `TransitionStart`, `TransitionEnd`, `TransitionInterrupt`
(`state Run [StateEntered=OnRun, StateLeft="Left Run"]`); leaving one out, or `=None`, clears it. An
event that also holds a Notify object or notify state class (set in the editor) reads by its name
with a `# note:`; a write that would change it is refused. `rule=true` is a rule with no graph; once
the `Transition:` section links the rule pin, leave `rule` out. `[shared=CanMove]` on several
transitions gives them one shared rule: its graph is the `Transition:` section of the first of them in
graph order (the others have none; edit it there, it applies to all) and takes no `rule=`. Leaving
`shared=` out unshares: the transition gets a new empty rule (set `rule=` on the same line), unless
no other transition still shares the graph and it is the earliest leaving, which keeps the graph.
Shared rules read under names unique in the machine (the editor allows repeats and empty names): the
stored name, `Unnamed` for none, and `"Name #2"`, `#3` (first free number) where an earlier rule reads
so or another is stored so, with a `# note:`; write the read name to keep a rule, another to rename it.
The numbers can shift after a rule goes: read before the next write. Crossfade sharing is set in the editor, never by a write; a group reads as a `# note:`, and a write
changing its `CrossfadeDuration`, `BlendMode`, `CustomBlendCurve` or blend profile must give its lines
one value each. Values compare with case (`StateEntered=onidle` over `OnIdle` is a change).
`LogicType=TLT_Custom` adds the section `Blend:Machine/From->To` (`#2` like its `Transition:`;
`TransitionPoseEvaluator` nodes `from`/`to` feed `out CustomTransitionResult`); another logic type removes it.
Naming an optional property in a pin line (`PlayRate = 2`) exposes it as a pin; `PlayRate [hidden]`
(a line with no value) hides it again; `hidden` stays an ordinary value and node id.

Anim node properties show member by member. A `ControlRig` node takes its
rig in `{"Node":{"ControlRigClass":"/Game/CR_Arms.CR_Arms_C"}}` on UE 5.5-5.7 and
`{"Node":{"ControlRigAssetReference":{"BlueprintRigClass":"/Game/CR_Arms.CR_Arms_C"}}}` on 5.8; setting the rig
turns its public variables into pins named like them (`Speed = 2`). `Pin = @Owner.Path` binds a pin to a
property access path (a variable, a member chain, or a function as the last element); a bound pin
reads the same way. A node's `UpdateFunction`, `InitialUpdateFunction` and `BecomeRelevantFunction` sit
beside `Node`, not in it: `{"Node":{...},"UpdateFunction":{"MemberName":"UpdateSpeed"}}` names the
Blueprint's own function; the function is a `Function:` section whose entry is
`FunctionEntry(Context: ref const AnimUpdateContext, Node: ref const AnimNodeReference) [ThreadSafe]` (another signature
fails the compile; `FunctionEntry` flags: [SKILL.md](SKILL.md)).

Cached poses: `SaveCachedPose Name` stores a pose, `UseCachedPose Name` links to it by that name
(a rename of the save node keeps the links). Pose-list nodes (`LayeredBoneBlend`, `BlendListByInt`,
`MultiWayBlend`) grow inputs when a pin line names one that does not exist yet (`BlendPoses_1 = x.Pose` and
`BlendWeights_1 = 0.5` on `LayeredBoneBlend`, `BlendPose_2 = x.Pose` on `BlendListByInt`); a pose output
holds one link, so each input takes its own node.
`BlendListByEnum {"BoundEnum":"/Script/Engine.EMovementMode"}` gets one pose input per enum entry a pin line names
(`BlendPose_MOVE_Walking = x.Pose`, `BlendTime_MOVE_Walking = 0.5`; the entry by its name, C++ short name or display name; the
read prints `BlendPose_<Entry>`; `BlendPose_0` is the Default pose). An entry the enum lacks is refused listing its entries; an
exposed entry the text stops naming stays on the node (a new `BoundEnum` is a new node).

Anim layers: writing a `Function:<Layer>` that does not exist makes an anim layer (an animation graph
with its own `Root`) in an Anim Layer Interface, and in an Anim Blueprint when the text has a `Root` or
`LinkedInputPose` line; without one it is a plain function. Layers an Anim Blueprint implements from an interface are `Function:` sections too. Put
`LinkedInputPose` nodes on it for its inputs. A layer's machines are `Machine:<Layer>/<Name>` sections.

Not authorable as text: linked-layer slot setup; use `run_python` for it.

Montage `Sections`: `Loop @ 0.5 -> Loop` (seconds, optional next section). Montage and sequence
`Notifies`: `Track: Name` lines, each followed by `  0.25 AnimNotify_PlaySound {"Sound":"..."}`,
`  0.25-0.75 AnimNotifyState_Trail {...}` (a state's start-end) or `  0.5 "Footstep"` (skeleton
notify); a notify matches by track, time and class. `Sockets`: skeleton `Grip: hand_r {"RelativeLocation":{"X":10}}`,
Static Mesh `Grip {"Tag":"grip"}`. `[was="Old"]` renames a section or socket.

## Anim Sequence, Montage and Blend Space data

Event settings go on the notify line in one bracket after the properties, only what differs from the
defaults: `0.25 AnimNotify_PlaySound [tick=BranchingPoint, chance=0.5]`, `0.5-0.75
AnimNotifyState_MotionWarping {"RootMotionModifier":{"class":"RootMotionModifier_Scale"}} [lod=2]`,
`0.875 "Footstep" [server=false, follower=true]`. A flag left off puts its default back. `tick` matters in a montage only; `lod=N` drops the notify on meshes at LOD N and above. Moving a
notify's time (`0.5-0.75` to `0.4-0.75`) retimes the same event when it is the only unmatched one of its class on
the track, so its settings and subobject stay.

The rest is a `Properties` / `set_properties` write, `call_function` on `AnimationBlueprintLibrary`, or
`run_python` (`unreal.AnimationLibrary`):

- Create: `create_asset` `AnimSequence` / `AnimMontage` with `options {"TargetSkeleton": "...",
  "SourceAnimation": "..."}`. A sequence's frames and rate come from its controller in `run_python`
  (`get_editor_property('controller')`: `set_frame_rate`, `set_number_of_frames`).
- Root motion, additive type, compression, `RetargetSource`, `RateScale`: `Properties` of the sequence, or
  `SetRootMotionEnabled`, `SetRootMotionLockType`, `SetAdditiveAnimationType`.
- Montage slots and segments are the `SlotAnimTracks` property: `set_properties values
  {"SlotAnimTracks[0].AnimTrack.AnimSegments[0].AnimEndTime": 0.5}`. The write recomputes the montage's
  length (`SequenceLength`) and linkable elements, so `Sections` and `Notifies` check the new length.
- Sync markers: `AddAnimationSyncMarker(sequence, "LeftFoot", 0.5, "Feet")` (the notify track must exist:
  list it in `Notifies` first), `GetAnimationSyncMarkersForTrack`, `RemoveAnimationSyncMarkersByName` and
  `ByTrack`.
- Curves: `AddCurve`, `AddFloatCurveKey` / `AddFloatCurveKeys`, `RemoveCurve`. Curve metadata sits on the
  skeleton: `AddCurveMetaData`, `SetCurveMetaDataMaterial`, `SetCurveMetaDataMorphTarget`.
- Virtual bones: `AddVirtualBone(sequence, "pelvis", "hand_r")`, `RemoveVirtualBone`.
- Skeleton slot names and groups have no property or Python route (the skeleton's slot functions are not
  Blueprint-callable); a montage slot needs one the skeleton already lists.
- A Blend Space's `SampleData` and axes are `Properties` (or `set_properties`); the write validates and
  resamples the blend data.
