# User structs, enums, String Tables, curves

User struct `Fields`, one line per field: `Count: int = 3` (the Variables types of [blueprint.md](blueprint.md) but `map`,
`softclass<Actor>` too; names read quoted as there). User enum `Entries`, one name per line. String Table
`Entries`, `Key = "Text"`.

A struct that failed to compile (a field whose type is gone, a recursive field) says so: its outline head reads `, has compile errors`
and both the outline and `Fields` end with `# note: this struct has compile errors: <engine error>`; a healthy struct has none.
`, not compiled` / `this struct is not compiled` means it is dirty. Blueprints that use a broken struct fail for that reason.

Struct `Fields` and enum `Entries` write partially: a bad line (type, default, a `was` that names nothing, a name twice)
is skipped and named under `not applied:`, its field or entry stays as it was (a failed `[was="Old"]` keeps `Old`), and
the other lines are written; only fields and entries no line names are removed. An enum entry name holds no space or
`"',/.:|&!~@#(){}[]=;^%$` and backtick. An enum a
Blueprint uses keeps its entries: a write that removes one is refused whole. On UE 5.7 and 5.8, undoing an enum write in the editor (Ctrl+Z) hits an engine assert
and crashes the editor (an engine bug): to take one back, write the old entries again.

A String Table text elsewhere reads `"LOCTABLE(\"/Game/ST_X.ST_X\", \"Key\")"`; that string written binds a text to the
table key, a read line written back keeps the binding, and a new plain string writes a literal.

Curve assets (`CurveFloat`, `CurveVector`, `CurveLinearColor`) have a `Keys` section: one key per line,
`0.5: 1 linear`, `1: 2 cubic user arrive=0.5 leave=0.5` (`constant`/`linear`/`cubic`; cubic may add
`smart_auto`, or `user`/`break` with `arrive=` `leave=`, and `arrive_weight=` `leave_weight=`). Vector and
colour curves put keys under `X:` / `R:` channel headers; a channel left out is cleared. `Keys` writes partially: a bad
key line keeps the key at its time (every key of its channel when the time does not read); an unknown channel header skips the
keys under it and keeps the channels no header lists.
`get_float_value(t)` (`call_function`) evaluates a curve.
