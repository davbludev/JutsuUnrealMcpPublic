# Control Rig

`Hierarchy` is one `Name: Type {json}` line per element, indented two spaces under its first parent:

```
root: Bone
  pelvis: Bone {"Transform":{"Location":[0,0,95]}}
    hips_ctrl: Control {"ControlType":"Position","LimitEnabled":[{"bMinimum":true,"bMaximum":true},{},{}],"MinimumValue":[-5,0,0],"MaximumValue":[5,0,0],"Offset":{"Location":[10,0,0]}}
root_ctrl: Control {"ShapeName":"Circle_Thick","ShapeColor":{"R":1,"G":0,"B":0,"A":1}}
  hips_space: Null {"Transform":{"Location":[0,0,90]}}
```

- Null and Control lines are written; every other line (bones, curves, sockets) stays as read.
- A control's `{json}`: `FRigControlSettings` members by name (`ControlType` first), then `Offset`,
  `ShapeTransform` and the initial `Value`. `MinimumValue`, `MaximumValue` and `Value` are in the
  control's type: a bool, a number, `[x,y]`, `[x,y,z]`, `[pitch,yaw,roll]` or a transform.
  `LimitEnabled` has one entry per channel (3 for Position, 9 for Transform).
- A transform is `{"Location":[x,y,z],"Rotation":[pitch,yaw,roll],"Scale":[x,y,z]}`.
- Re-indent a line to move it (a move drops its extra space-switch parents); `[was="Old"]`
  renames; a null or control left out is removed.

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

- `<id>` is the node's name; a new node takes the name you write.
- Types: `Unit <Struct>` (a rig unit or RigVM function, e.g. `RigVMFunction_MathFloatAdd`),
  `Template <Dispatch>(Pin: type)` (a dispatch such as `RigVMDispatch_ArrayMake(Values: float[])`;
  the types given and a link resolve it), `Get Var`, `Set Var`, `Call <LocalFunction>`,
  `Comment "text"`, `Reroute`. Other nodes read as `Node <Class>` and keep their line; their pins
  still take values and links.
- Values are RigVM text (`(X=1,Y=2,Z=3)`, `(Type=Bone,Name="hand_l")`); links and values may name
  sub-pins (`Value.Translation`); a pin takes a link or a value, not both.
- Writing a `Function:<Name>` that does not exist creates that local function. Its signature is
  `Entry FunctionEntry(Speed: float, Target: Transform)` (` [Pure]` appended for a pure one) and
  `Return FunctionResult(Result: float)`; changing them changes the signature, and every Call node
  follows it (the reply lists them). Empty text deletes the function, refused while anything calls it.

The `Document` section writes the rig's member variables (and the same nodes as JSON). A new rig
from a mesh:
`unreal.ControlRigBlueprintFactory.create_control_rig_from_skeletal_mesh_or_skeleton`.

## Sequencer

In a Level Sequence `Document`, a skeletal mesh actor's binding takes a track
`{"create": {"kind": "control_rig", "controlRig": "/Game/CR_Hero"}}`; its section is
`{"find": {}}` and keys go on control channels such as `root_ctrl.Location.X`.

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
   (`RigUnit_InverseExecution`) event.
4. Bake: create the target AnimSequence first, then `SequencerToolsFunctionLibrary.ExportAnimSequence`
   `{"World": <editor world path>, "Sequence": <sequence>, "AnimSequence": <anim>,
   "ExportOptions": {"class": "AnimSeqExportOption"}, "Binding": <step 1 ReturnValue>, "bCreateLink": false}`
   (`ExportOption` before UE 5.7).

Give Basic IK (`RigUnit_TwoBoneIKSimplePerItem`) a unit-length `SecondaryAxis`: an unnormalized one
rolls the bone once the solve starts from another pose, as it does in Sequencer.
