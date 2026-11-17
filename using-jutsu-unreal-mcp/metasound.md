# MetaSound

## Graph

Build and rewire a MetaSound Source or Patch in its `Graph` section. Read it first: a new Source
already lists its interfaces and their members.

1. Find classes: `read_asset section=Kinds:Graph@wave` lists the classes whose class name, display name or the first line
   of whose description holds `wave` (case-insensitive), then `Kinds:Graph@UE.WavePlayer.Mono` one class with its
   inputs (type, default, enum entries) and outputs. Words that find few classes: `InterpTo`, `Crossfade`,
   `TriggerRepeat`, `WavePlayer` (`@value` came to 17k characters).
2. A complete minimal Source that plays a wave and a sine tone:

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
  `Level Output float` with `  Value = <id>.<output>`. An array input's default is a JSON array of
  its element type: `Gains Input Float:Array` with `  Default = [1, 0.5, 0]`.
- Stereo: replace `"UE.OutputFormat.Mono" Interface` by `"UE.OutputFormat.Stereo" Interface` and its
  member lines (`"UE.OutputFormat.Stereo.Audio:0" Output Audio`, `...Audio:1`), in one write. The
  write sets the Source's `OutputFormat` too. Setting `OutputFormat` to another format with
  `set_properties` swaps the interface but drops the links of its outputs.
- A loop or music without an end: leave out `"UE.Source.OneShot" Interface` and its member line
  (`"UE.Source.OneShot.OnFinished" Output Trigger`), in one write. The Source then never finishes by
  itself: play it on an audio component and stop it there. Writing both lines again adds it back.
  `"UE.Source" Interface` and its `OnPlay` stay on every Source.
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

The Graph writes partially: a line with a problem (an unknown class, input or output, a bad value, a link or flag
Unreal refuses) is skipped and named under `not applied:`, with the lines under its node and every line linking to it;
the node or member of its id stays as it was. Still refused whole: links that loop, a Source without exactly one output
format interface, an interface member left out while its interface stays, a variable left out while its nodes stay,
and the write that makes the asset a preset (next sections).

## Member settings

Flags after the line of a graph input, output or variable set what the MetaSound Editor shows for it:

```
Gain Input float [DisplayName="Master gain", Description="How loud, in dB", Advanced]
  Default = 0.5
Seed Input int32 [Constructor]
Level Output float [DisplayName="Out level"]
  Value = Gain
Hold Variable float [Description="Held value"]
```

`DisplayName` and `Description` are text, `Advanced` hides the pin until the node is expanded, `Constructor` makes it a
constructor pin (read once when the graph is created; it links only to constructor pins). A variable takes the two
text flags only. Writing a line without a flag takes it off. An interface's members (`UE.Source.OnPlay`) keep the
interface's settings and refuse flags. Change `Constructor` on both ends of a link in one write: a member line that
would leave a constructor pin linked to a reference pin is not applied, naming the link. On UE 5.5 a constructor input
cannot be linked to a constructor output at all (the engine refuses the link line).

## Presets

A preset plays another MetaSound's graph (same kind: a Source of a Source, a Patch of a Patch). Create the asset, then write
its Graph with the parent on the first line (that first write is whole: a bad line refuses it; later writes of the preset
skip a bad input line, that input keeping its default, and apply the rest):

```
Preset /Game/Audio/MS_Parent.MS_Parent
Gain Input float
  Default = 0.25
```

- The read lists the parent's inputs; the ones with `Default = <value>` have a default of their own and keep it when the
  parent changes. The others (`Pitch Input float`) take the parent's.
- To clear an override write the input without its `Default` (or leave its line out). Listing an input with a value
  equal to the parent's still overrides it. While a line's input name does not read (`"Gain`, `Gain:`), leaving a line
  out clears nothing.
- A new asset becomes a preset with this one write; an asset that already has nodes, variables or members of its own is
  refused (make the preset from a new asset). The parent is fixed after, and every write keeps the `Preset` line.
- A preset has no nodes, outputs or interfaces of its own: such lines, an input the parent lacks (the refusal lists the
  parent's; one written with another type says what type the parent's input has), and `Default` on a Trigger input are
  refused. To change the graph, edit the parent. A parent that plays this asset itself (a preset of it, or a node that
  uses it) is refused.
