# Widget Blueprints

A Widget Blueprint has the Blueprint sections (`Variables`, `EventGraph`, `Function:Name`) plus
`WidgetTree` and `Animations`. Build in this order: `Variables` and the `Function:` graphs a binding
reads, then `WidgetTree`, then `Animations` and the `EventGraph`.

## WidgetTree

```
Root: CanvasPanel
  HealthBar: ProgressBar @{"LayoutData":{"Anchors":{"Minimum":{"X":0,"Y":1},"Maximum":{"X":0,"Y":1}},"Offsets":{"Left":40,"Top":-40,"Right":300,"Bottom":24},"Alignment":{"X":0,"Y":1}}} [bind Percent=GetHealthPercent]
  Score: TextBlock @{"LayoutData":{"Anchors":{"Minimum":{"X":1,"Y":0},"Maximum":{"X":1,"Y":0}},"Offsets":{"Left":-40,"Top":40,"Right":0,"Bottom":0},"Alignment":{"X":1,"Y":0}},"bAutoSize":true} [bind Text=Stats.Label]
  Crosshair: Image @{"LayoutData":{"Anchors":{"Minimum":{"X":0.5,"Y":0.5},"Maximum":{"X":0.5,"Y":0.5}},"Offsets":{"Left":0,"Top":0,"Right":16,"Bottom":16},"Alignment":{"X":0.5,"Y":0.5}}}
  Menu: VerticalBox
    PlayButton: Button
      PlayLabel: TextBlock {"Text":"Play"}
    QuitButton: Button
      QuitLabel: TextBlock {"Text":"Quit"}
```

- A line is `Name: Class {widget properties} @{slot properties} [bind ...]`, two spaces per level,
  children in order. Both JSON parts hold only values that differ from the class defaults.
- Canvas slot: `LayoutData` holds `Anchors` (`Minimum`/`Maximum`, 0-1 of the parent), `Offsets` and
  `Alignment` (the widget's own pivot, 0-1). With a point anchor (`Minimum` = `Maximum`), `Left`/`Top`
  is the position from the anchor and `Right`/`Bottom` the size; `"bAutoSize":true` sizes the widget
  to its content instead. A struct value is written whole, so give `LayoutData` all three members.
- Other panels' slots take their own members: `@{"Padding":{"Left":8}}`.
- A widget that a graph names (a `ComponentEvent`, a `Get` of the widget) or that you reach in PIE
  through `get_properties` is a Blueprint variable: add `"bIsVariable":true` to its `{...}`. Button,
  ProgressBar and Image are variables by default, so their read leaves it out; TextBlock and panels
  need it written.

## Widget property bindings

`[bind Property=Source, ...]` at the end of a widget line is the Details panel's Bind: the property
shows the source's value every frame. The source is a pure function without parameters returning the
property's type, a variable, or a member path through struct and object variables (`Stats.Score`).
The clause is the widget's whole set: leave it out to remove the bindings. A refusal lists the
widget's bindable properties or the sources of a matching type.

A binding function is a `Function:` graph whose entry runs to its result, `[Pure]` included:

```
e FunctionEntry() [Pure]
  then -> r
r FunctionResult(ReturnValue: float)
  ReturnValue = g.Health
g Get Health
```

Write the function before the `WidgetTree` that binds it; a source through a widget added in the same
`WidgetTree` write binds on a second write.

## Graph events on widgets

`ComponentEvent PlayButton.OnClicked` in the widget's `EventGraph` handles a button click (the widget
must be a variable, see above). A refusal lists the widgets with events and each widget's events.

## Animations

```
Toast [0-1]
  Panel.RenderOpacity: 0=0 linear, 0.3=1
  Panel.RenderTransform.Translation.X: 0=-200, 0.3=0
  Title.ColorAndOpacity.G: 0=1, 0.5=0.8, 1=1
  Panel.Visibility: 0=Visible, 1=Collapsed
  Panel.Slot.Padding.Left: 0=0, 0.5=12
```

- `Name [start-end]` per animation (seconds; `[was="Old"]` renames), then one line per keyed channel:
  `Widget[.Slot].<PropertyPath>[.<Channel>]: seconds=value, ...`.
- Channels: colours `R/G/B/A`, margins `Left/Top/Right/Bottom`, widget transform `Translation.X/Y`,
  `Angle`, `Scale.X/Y`, `Shear.X/Y`; a struct member is a path (`Slot.LayoutData.Offsets.Left`). Any
  float, double, bool, integer, byte or enum property keys too. A refusal lists the animatable
  properties or the channels.
- Float and double keys take `constant` or `linear` after the value (cubic when omitted). Bool,
  integer, byte and enum keys hold their value until the next key and take only `constant`; enum keys
  are names, bools `true`/`false`.
- Channel lines key widgets of the `WidgetTree` and their slots. The user widget's own tracks read as
  channel lines named by its preview widget (`WBP_Menu_C_0.RenderOpacity`); in an animation that
  already has them, key more of its properties under that name. To fade or move the whole widget in a
  new animation, key its root panel (`Root.RenderOpacity`). Other tracks (events, materials) are kept
  and named by a `# note:` line.
- Left-out keys, channels and animations are removed.

React to an animation's end with `Event OnAnimationFinished` in the `EventGraph`.

## In PIE

Make and show a widget with `call_function`, each call after `start_pie` answered:

1. `call_function(object="GameplayStatics", function="GetPlayerController", args={"PlayerIndex": 0})`:
   `ReturnValue` is the controller's path. The world context fills itself in.
2. `call_function(object="WidgetBlueprintLibrary", function="Create", args={"WidgetType":
   "/Game/UI/WBP_HUD.WBP_HUD_C", "OwningPlayer": <controller>})`: `ReturnValue` is the widget's path.
   It stays valid until PIE stops (or until 256 newer returned objects push it out).
3. `call_function(object=<widget>, function="AddToViewport")`.

- Live values: `set_properties(object=<widget>, values={"Health": 0.25})` sets a widget variable.
  `get_properties(object=<widget>, properties=["<ChildName>"])` names the child's `path`. `get_properties` on a bound
  property returns `bindings`, which names the call that reads the shown value (on a live widget,
  `call_function` on the source function), since the stored value is not what shows.
- Play an animation: `call_function(object=<widget>, function="PlayAnimation", args={"InAnimation":
  <path from get_properties(object=<widget>, properties=["Toast"])>})`.
- Press a button with the keyboard: focus it with `call_function(object="WidgetBlueprintLibrary",
  function="SetInputMode_UIOnlyEx", args={"PlayerController": <controller>, "InWidgetToFocus":
  <the button's path>})`; then `send_input(key="Enter")` clicks the focused button.
- Make plain item objects (list view items, data objects) with `GameplayStatics.SpawnObject` from
  `call_function`, or with a `GenericCreateObject` node in a graph.
- In `run_python` the library is `unreal.WidgetLibrary` (`unreal.WidgetLibrary.get_all_widgets_of_class`).
