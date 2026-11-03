# MetaSound

## Graph

Build and rewire a MetaSound Source or Patch in its `Graph` section. Read it first: a new Source
already lists its interfaces and their members.

1. Find classes: `read_asset section=Kinds:Graph@wave` lists matching classes, then
   `Kinds:Graph@UE.WavePlayer.Mono` one class with its inputs (type, default, enum entries) and outputs.
2. Write the whole graph. A complete minimal Source that plays a wave and a sine tone:

```
"UE.OutputFormat.Mono" Interface
"UE.Source" Interface
"UE.Source.OneShot" Interface
"UE.Source.OnPlay" Input Trigger
wave UE.WavePlayer.Mono
  Play = "UE.Source.OnPlay"
  Wave Asset = "/Game/Audio/S_Step.S_Step"
tone UE.Sine.Audio
  Frequency = 440
mix UE.Add.Audio
  PrimaryOperand = wave."Out Mono"
  AdditionalOperands = tone
"UE.OutputFormat.Mono.Audio:0" Output Audio
  Value = mix
"UE.Source.OneShot.OnFinished" Output Trigger
  Value = wave."On Finished"
```

- Node ids you choose (`wave`, `tone`) are kept; a node made in the editor reads as `n` plus a GUID prefix.
- `<id>` alone links a node's first output (a read names it: `tone.Audio`); `<id>.<output>` another; quote a name with spaces or dots (`wave."Out Mono"`, `"UE.Source.OnPlay"`).
- To rewire an input, write its new source; a line left out unlinks it or resets its value.
- Your own graph members: `Gain Input float` with `  Default = 0.5`, then link `Gain` into an input;
  `Level Output float` with `  Value = <id>.<output>`.
- Stereo: replace `"UE.OutputFormat.Mono" Interface` by `"UE.OutputFormat.Stereo" Interface` and its
  member lines (`"UE.OutputFormat.Stereo.Audio:0" Output Audio`, `...Audio:1`), in one write.
- A value carried without a wire: a graph variable and its nodes.

```
Level Variable float
  Default = 0.25
store VariableSet Level
  Value = Gain
now VariableGet Level
late VariableGetDelayed Level
```

  Link `now` (or `late`, the value before this block's set) where the value is read. One `VariableSet`
  per variable; to remove a variable, leave out its line with its node lines.

## Document and presets

A MetaSound preset: create the asset, then write the `Document` section with
`"preset": {"parent": "<same-kind MetaSound>"}` and its input overrides as
`{"find": {"kind": "input", "name": "Gain"}, "default": 0.25}` nodes, in one write or later ones (a
later write may leave `preset` out). The Document's other fields may be left out. A MetaSound input
with a default: `{"create": {"kind": "input", "name": "Waves", "dataType": "WaveAsset:Array", "default": ["/Game/W.W"]}}` (`float`, lowercase).

A node's input defaults sit beside its `create` or `find`: `{"create": {...}, "defaults": {"Gain": 3}}`,
`{"find": {"authoringId": "Biquad1"}, "defaults": {"Gain": 3}}` on an existing node. An enum input
takes an entry's name, short, qualified or as displayed (`"Type": "Highpass"`); a wrong one fails
listing the entries, and the value reads back as the entry's number.
