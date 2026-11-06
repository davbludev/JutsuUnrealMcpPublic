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

- Node ids you choose (`wave`, `tone`) are kept, also on a copy made with `duplicate_asset`; a node made in the editor reads as `n` plus a GUID prefix.
- `<id>` alone links a node's first output (a read names it: `tone.Audio`); `<id>.<output>` another; quote a name with spaces or dots (`wave."Out Mono"`, `"UE.Source.OnPlay"`).
- To rewire an input, write its new source; a line left out unlinks it or resets its value. An enum
  input takes an entry's name (`Type = Highpass`).
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

  Link `now` (or `late`, the value before this block's set) where the value is read.

## Member settings

Flags after the line of a graph input, output or variable set what the MetaSound Editor shows for it:

```
Gain Input float [displayName="Master gain", description="How loud, in dB", advanced]
  Default = 0.5
Seed Input int32 [constructor]
Level Output float [displayName="Out level"]
  Value = Gain
Hold Variable float [description="Held value"]
```

`displayName` and `description` are text, `advanced` hides the pin until the node is expanded, `constructor` makes it a
constructor pin (read once when the graph is created; it links only to constructor pins). A variable takes the two
text flags only. Writing a line without a flag takes it off. An interface's members (`UE.Source.OnPlay`) keep the
interface's settings and refuse flags. Change `constructor` on both ends of a link in one write: a write that would
leave a constructor pin linked to a reference pin is refused naming the link. On UE 5.5 a constructor input cannot be
linked to a constructor output at all (the engine refuses it).

## Presets

A preset plays another MetaSound's graph (same kind: a Source of a Source, a Patch of a Patch). Create the asset, then write
its Graph with the parent on the first line:

```
Preset /Game/Audio/MS_Parent.MS_Parent
Gain Input float
  Default = 0.25
```

- The read lists the parent's inputs; the ones with `Default = <value>` have a default of their own and keep it when the
  parent changes. The others (`Pitch Input float`) take the parent's.
- To clear an override write the input without its `Default` (or leave its line out). Listing an input with a value
  equal to the parent's still overrides it.
- A new asset becomes a preset with this one write; an asset that already has nodes, variables or members of its own is
  refused (make the preset from a new asset). The parent is fixed after, and every write keeps the `Preset` line.
- A preset has no nodes, outputs or interfaces of its own: such lines, an input the parent lacks (the refusal lists the
  parent's; one written with another type says what type the parent's input has), and `Default` on a Trigger input are
  refused. To change the graph, edit the parent. A parent that plays this asset itself (a preset of it, or a node that
  uses it) is refused.
