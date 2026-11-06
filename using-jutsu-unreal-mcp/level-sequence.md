# Level Sequence

A Level Sequence is text in three kinds of section: `Sequence` (playback range, bindings, event
keys), one `Binding:<Name>` per binding (its tracks, sections and keys), and `Director` with
`Function:<Name>` (the director Blueprint's graphs). `read_asset(path)` lists them. Build in this
order: `Sequence` (the bindings exist), then `Binding:<Name>`, then `Director`.

## Sequence

```
Playback [0-120]
Drone: spawn /Game/BP_Drone
Hero: actor "Hero Light"
Prop [was="Crate"]: actor "Crate 2"
event [0-120]
  Event: 12=OnLand, 48=Boom
```

- `Playback [start-end]`: display-rate frames (the read's `# note: display rate` names the rate), end
  exclusive.
- One line per binding, `<Name>: <what it binds>`; names are unique ignoring case, a name with `:`,
  `[` or quotes is quoted. Bindings read sorted by name.
  - `actor "<label>"`: a possessable of the actor with that label in the open map. A missing or
    ambiguous label is refused with the map's candidates.
  - `spawn <class or Blueprint asset path>`: a spawnable made the way the editor makes one (with its
    `spawn` track).
  - `spawn actor "<label>"`: a spawnable from that actor's template; it reads back as `spawn <its class>`.
  - `unbound` is what a possessable whose actor is gone reads as; write it back to keep it.
- `[was="Old"]` renames a binding (same binding, same tracks); the old name is free again in the same
  write. A binding line that switches between `actor` and `spawn`, or a spawnable's class, is a new
  binding: write it under a new name. Bindings left out are removed with their tracks.
- Master tracks follow the bindings in the track grammar below. `event` is the one master track kind
  written; other kinds (camera cuts, audio, fade) read as a `# note: keeps ...` line and stay.
- A track block under `Sequence` for any other kind is refused with a pointer to `Binding:<Name>`.

## Binding:<Name>

```
transform [0-120]
  Location.X: 0=0, 60=300 linear
  Rotation.Z: 0=0, 120=90
float_property CustomTimeDilation [0-48] ease 6/6
  CustomTimeDilation: 0=1, 24=0.5 linear
spawn
  Spawned: 0=true, 60=false
control_rig /Game/Rigs/CR_Hero
  root_ctrl.Location.X: 0=25
```

- Track line: `<kind> [<property path>] [<start>-<end>] [ease <in>/<out>]`. Channel lines are indented two
  spaces: `<channel>: frame=value [interpolation], ...`.
- Kinds: `transform`, `bool_property`, `integer_property`, `float_property`, `double_property`,
  `string_property`, `byte_property` (a byte or enum property; keys are enum names), `spawn` (a
  spawnable's, it comes with the binding and stays when its line is left out), `control_rig`
  ([control-rig.md](control-rig.md)). A property kind names the property on the bound object:
  `float_property CustomTimeDilation`, a Blueprint variable with a space quoted (`float_property "My Speed"`).
  A mistyped kind, property or channel is refused with the valid names.
- Channels: `Location.X/Y/Z`, `Rotation.X/Y/Z`, `Scale.X/Y/Z` for `transform`; a property track's only
  channel carries the property's name; `Spawned` on `spawn`. A refusal lists a track's channels.
- Keys follow the widget `Animations` spelling: a float or double key takes `constant` or `linear` after
  the value (cubic when omitted), bool, integer, byte and enum keys hold their value and take
  `constant`; `true`/`false`, enum names, strings quoted.
- Frames are display-rate frames everywhere (keys, ranges, ease, playback): whole frames print as
  integers, a tick between two frames prints as the shortest decimal that reads back, and a written
  frame that is not a whole tick is refused naming the nearest two. Write what the read printed.
- `[start-end]` is the section range (end exclusive; `*` leaves a side open; no range at all is an
  unbounded section). Keys sit inside their section. `ease <in>/<out>` is the blend in/out in frames,
  each a number or `auto`.
- Another section of one track repeats the track line with its own range. A track, section, channel or
  key left out is removed. `(empty)` clears the binding's tracks.
- `Binding:<Name>` for a name `Sequence` does not list is refused naming the bindings; writing one
  binding never touches another.

## Events and the Director

The master `event` track keys fire custom events of the sequence's director Blueprint:

```
event [0-30]
  Event: 2=OnLand, 5=Boom, 8="Big Bang"
```

- One `Event:` line per section; a key is `frame=<custom event name>` (quoted when the name has a
  space, comma, `=` or quote). Keys sit inside the section range and one frame holds one key; an event
  key takes no interpolation.
- A name the Director has as a custom event is bound. A new name creates an empty custom event in the
  Director (the director is created when missing), and the reply says
  `warning: created empty director event <Name>; write its body in Director`. A name the Director
  already uses for a function, variable or graph is refused before anything is created.
- Write the body in section `Director` (the director's EventGraph, Blueprint graph text, see
  [SKILL.md](SKILL.md)) or `Function:<Name>`:

  ```
  land CustomEvent OnLand()
    then -> say
  say Call KismetSystemLibrary.PrintString
    InString = "Landed"
  ```

  Writing `Director` creates the director when the sequence has none; `read_asset` lists it as
  `no director yet` until then. The director lives inside the sequence's package.
- Custom events outlive their keys: leaving a key, a section or the whole event track out keeps the
  events in the Director. A key whose custom event is gone reads `frame=(unbound)`; write it back to
  keep it, or name the event it should fire. A `Director` write that takes away a custom event
  keys fire replies `warning: event keys at frames <frames> no longer fire <Name>; ...`:
  write the event back in `Director`, or rewrite those keys in `Sequence`.
- A binding's own event track and a repeater section are kept as notes; event lines in a
  `Binding:<Name>` section are refused toward `Sequence`.
- Director writes follow the Blueprint rules: `stop_pie` first.

## Writes

A write is parsed and resolved first; a refusal changes nothing and names the line. A write equal to
the read replies `No change.`. One write is one undo step and the asset is saved. A success reply is
`ok`, then `ids: <written>=<stored>` for a name stored differently, `removed:` items, and `warning:`
for what needs a follow-up. A `# note:`
line in a read names what the text does not show; writes skip it, and what it names stays.

A Level Sequence has no `Document` section: both directions refuse it and name `Sequence`.
Operations the text has no form for (playing a sequence, loading an animation onto a rig, baking)
go through `call_function` on the engine's libraries.
