# Control Rig

A Control Rig's `Document` section writes its variables, unit and variable nodes, pin defaults and
links, and finds existing hierarchy elements by type and name for pins that point at them. Its RigVM
graph sections are read-only text.

The hierarchy itself (adding controls and nulls, control type, offset, shape, color, limits) and
Sequencer Control Rig tracks have no tool or section; build them through `run_python`:

- New rig: `unreal.ControlRigBlueprintFactory.create_control_rig_from_skeletal_mesh_or_skeleton`.
- Hierarchy: `rig.get_hierarchy_controller()`, then `add_control` / `add_null` with their settings.
- Graph nodes the `Document` leaves out: `rig.get_controller_by_name(graph)` (a `RigVMController`),
  then `add_unit_node_from_struct_path`, `set_pin_default_value`, `add_link`.
- Sequencer: `unreal.ControlRigSequencerLibrary.find_or_create_control_rig_track`,
  `load_anim_sequence_into_control_rig_section_with_range` (UE 5.6+; on 5.5
  `load_anim_sequence_into_control_rig_section`); bake with `unreal.SequencerTools.export_anim_sequence`.

Give Basic IK (`RigUnit_TwoBoneIKSimplePerItem`) a unit-length `SecondaryAxis`: an unnormalized one
rolls the bone once the solve starts from another pose, as it does in Sequencer.
