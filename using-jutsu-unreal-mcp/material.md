# Materials

Material `Graph`: `<id> Multiply` with `A = <id>.RGB` inputs, then an `Output` block of
`BaseColor = <id>` lines. An unlinked input takes a value where Unreal stores one (`B = 0.5` is
Multiply's `ConstB`); anywhere else link a `Constant`/`Constant3Vector` node. A function call is
`c MaterialFunctionCall {"MaterialFunction":"/Game/MF_X.MF_X"}` with its inputs by name and `c.<Output>`;
a Named Reroute usage links `Declaration = <declaration id>`. `Kinds:Graph@<kind or id>` lists a
kind's inputs, which take values, and its outputs. Material instance `Parameters`, `Defaults`, `Properties`: `Name = <json>`;
an instanced subobject (input trigger, Blackboard key type) is `{"class": "InputTriggerPressed", ...}`;
struct array elements list only changed members (`{}`: all default).
