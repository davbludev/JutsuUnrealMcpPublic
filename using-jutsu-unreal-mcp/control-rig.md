# Control Rig

`Hierarchy` is an optional `Preview` line, then one `Name: Type {json} [flags]` line per element, indented two
spaces under its first parent:

```
Preview /Game/Characters/SK_Hero
root: Bone
  pelvis: Bone {"Transform":{"Location":[0,0,95]}}
    hips_ctrl: Control {"ControlType":"Position","LimitEnabled":[{"bMinimum":true,"bMaximum":true},{},{}],"MinimumValue":[-5,0,0],"MaximumValue":[5,0,0],"Offset":{"Location":[10,0,0]}}
    grip: Socket [color=(R=1,G=0.5,B=0,A=1), description="Hand grip"]
root_ctrl: Control {"ShapeName":"Circle_Thick","ShapeColor":{"R":1,"G":0,"B":0,"A":1}}
  hips_space: Null {"Transform":{"Location":[0,0,90]}}
weight: Curve [value=0.5]
arm: Connector [description="Left arm", type=Secondary, optional]
```

- Null, Control, Curve, Socket, Connector and user-made Bone lines are written; a bone
  imported from a mesh and anything else stays as read. A curve or connector stands at the root.
- `Preview /Game/SK_Hero` sets the preview mesh; a write without the line clears it. A rig whose bones
  were imported only takes a mesh of that skeleton or a compatible one (the refusal names the skeleton it expects); the mesh it has already always writes back.
- A rig made empty takes a mesh's bones with `@import /Game/SKM_Hero` as the whole text (a mesh or
  skeleton path, with a `Preview` line beside it if you want one); read, then write the rest as lines.
- `[flags]`: a Socket takes `color=(R=..,G=..,B=..,A=..)` and `description="..."`; a Connector takes
  `description`, `type=Primary|Secondary`, `optional`, `array` (UE 5.6+), `postConstruction` (UE 5.7+), `rules`; a Curve takes
  `value=0.5`. Only a `Secondary` connector is `optional`, an `array` or `postConstruction`; name one `Primary` connector (the default type) at most. Flags are the whole state: one left out goes back to its default. `[was="Old"]` goes in the
  same block.
- `"ExtraParents":["space_b"]` in a transform line adds space-switch parents by line name.
- A control's `{json}`: `FRigControlSettings` members by name (`ControlType` first), then `Offset`,
  `ShapeTransform` and the initial `Value`. `MinimumValue`, `MaximumValue` and `Value` are in the
  control's type: a bool, a number, `[x,y]`, `[x,y,z]`, `[pitch,yaw,roll]` or a transform.
  `LimitEnabled` has one entry per channel.
- A transform is `{"Location":[x,y,z],"Rotation":[pitch,yaw,roll],"Scale":[x,y,z]}`.
- Re-indent a line to move it (the indent is the first parent only); `[was="Old"]` renames; a line
  left out is removed.

## Graphs

`Rig` and `Function:<Name>` are node text, like Blueprint graphs:

```
Begin Unit RigUnit_BeginExecution
  ExecutePin -> SetBone
GetBone Unit RigUnit_GetTransform
  Item = (Type=Bone,Name="Bone01")
Offset Unit RigVMFunction_MathVectorAdd
  A = GetBone.Transform.Translation
  B = (X=0,Y=0,Z=10)
SetBone Unit RigUnit_SetTransform
  Item = (Type=Bone,Name="Bone01")
  Value.Translation = Offset.Result
```

- `<id>` is the node's name; a new node takes the name you write. A name that is not letters, digits
  and `_` is quoted, as id and as link target: `"To World" Unit RigUnit_ToWorldSpace_Transform`,
  `Value = "To World".World`, `ExecutePin -> "To World"`.
- Types: `Unit <Struct>` (a rig unit or RigVM function, e.g. `RigVMFunction_MathFloatAdd`),
  `Template <Dispatch>(Pin: type)` (a dispatch such as `RigVMDispatch_ArrayMake(Values: float[])`;
  the types given and a link resolve it), `Get Var`, `Set Var`, `Call <LocalFunction>`,
  `Call /Game/CR_Lib:Function` (a public function of another Control Rig), `Comment "text"`,
  `Reroute`, `Collapse(A, B)`. Other nodes read as `Node <Class>` and keep their line; their pins still take values
  and links.
- A collapse node reads `Pair Collapse`; its inner nodes are the section `Collapse:Pair`, written like `Rig`. Make one by
  writing the nodes and a `Pair Collapse(A, B)` line naming them in the same text (the text is the graph before the collapse;
  links to outside nodes follow into the new node). The new node's pins exist only after the write: read, then write them.
  Leave its line out to delete it with its inner graph; to expand it, write its inner nodes' lines in its place and relink them.
- Aggregate pins (a `Sequence`'s outputs, an Add's inputs) are text: naming the node's next one
  creates it (`C -> Next`, `C = 2`), in order, and leaving one out removes it. `D ->` is an execute output that links nothing. An aggregate node reads as its
  unit (`Seq Unit RigVMFunction_Sequence`); its pins past the second always print a line.
- Values are RigVM text (`(X=1,Y=2,Z=3)`, `(Type=Bone,Name="hand_l")`); links and values may name
  sub-pins (`Value.Translation`, an array element's `Effectors.0.Bone`).
- Writing a `Function:<Name>` that does not exist creates that local function. Its signature is
  `Entry FunctionEntry(Speed: float, Target: Transform)` (` [Pure]` appended for a pure one, ` [Public]` for one other rigs may call, both ` [Pure, Public]`) and
  `Return FunctionResult(Result: float)`; changing them changes the signature, and every Call node
  follows it. Empty text deletes the function. Dropping `[Public]` is refused while other assets call it.

The rig's member variables are the `Variables` section. A new rig from a mesh: `create_asset` class `ControlRig`, then `@import`.

## Control Rig in an Anim Blueprint

A `ControlRig` node in an anim graph, and the lane's spelling of its rig: see [animation.md](animation.md).

## IK Rig and Retargeter

An IK Rig has `Chains` (`Arm UpperArm Hand HandGoal`: name, start bone, end bone, optional goal),
`Goals` (`HandGoal Hand solvers=0`) and `Solvers`, one line per solver in stack order:
`set_transform disabled alpha=0.5`, or any other type with its bones and settings,
`full_body_ik start=pelvis {"MassMultiplier":2,"goals":{"HandGoal":{"StrengthAlpha":0.5}},"bones":{"spine_01":{}}}`
(`goals` holds per-goal settings, `bones` the bones that carry settings). Write Solvers before the
Goals that connect to them.

A Retargeter has `Chains`: `[Operation ]TargetChain SourceChain` (the operation column on UE 5.6 and
later), and `Ops`, its stack in order:
`Name type [parent=Op] [disabled] [{settings}]` (`parent=` on UE 5.6 and later).

## Sequencer

A Level Sequence takes a rig as a `control_rig` track line in section `Binding:<Name>` of a binding
whose actor has a skeletal mesh component (bindings and the track grammar: [level-sequence.md](level-sequence.md)).
The line names the Control Rig Blueprint by asset path; `layered` follows it for a rig that layers over
the animation below it (that rig needs a Backwards Solve event). The track has one section, unbounded
unless the line gives a range, and its channels are named after the controls, so a control's
keys are `<control>.Location.X`, `.Rotation.Y`, `.Scale.Z` for a transform control and the bare control name for a
float control:

```
control_rig /Game/CR_Hero [0-60]
  root_ctrl.Location.X: 0=25, 10=40 linear
  weight_ctrl: 0=0.5
```

A mistyped rig or control is refused with the right names; a binding holds one track per rig, switched
between plain and `layered` by rewriting its line. A loaded animation reads back as keys on every
control channel and writes back as `No change.`; space and constraint keys the channels do not name read as
a `# note:` and stay.

Loading an animation into the section and baking go through `call_function`, each step using the
previous step's result:

1. `MovieSceneSequenceExtensions.FindBindingByName` `{"Sequence": <sequence>, "Name": <binding>}`:
   its `ReturnValue` is the binding.
2. `ControlRigSequencerEditorLibrary.GetControlRigs` `{"LevelSequence": <sequence>}`: the track is
   `ReturnValue[0].Track`; `MovieSceneTrackExtensions.GetSections` `{"Track": <track>}` gives the section.
3. Load: `ControlRigSequencerEditorLibrary.LoadAnimSequenceIntoControlRigSectionWithRange`
   `{"MovieSceneSection": <section>, "AnimSequence": <anim>, "SkelMeshComp": <component path>,
   "InStartFrame": {"Value": 0}, "bUseCustomAnimRange": false, "AnimStartRange": {"Value": 0},
   "AnimEndRange": {"Value": 0}}` (UE 5.5: `LoadAnimSequenceIntoControlRigSection` with
   `InStartFrame` only). It returns false unless the rig has a Backwards Solve
   (`RigUnit_InverseExecution`) event. Before UE 5.7 it adds its keys beside the section's own, so write
   the track line without channels first (`control_rig <rig>`), which clears its keys.
4. Bake: create the target AnimSequence first, then `SequencerToolsFunctionLibrary.ExportAnimSequence`
   `{"World": <editor world path>, "Sequence": <sequence>, "AnimSequence": <anim>,
   "ExportOptions": {"class": "AnimSeqExportOption"}, "Binding": <step 1 ReturnValue>, "bCreateLink": false}`
   (`ExportOption` before UE 5.7).

Give Basic IK (`RigUnit_TwoBoneIKSimplePerItem`) a unit-length `SecondaryAxis`: an unnormalized one
rolls the bone once the solve starts from another pose, as it does in Sequencer.
