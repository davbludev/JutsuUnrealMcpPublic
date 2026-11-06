# DataTable Rows

A DataTable's rows are `read_asset(table, "Rows")` text: one line per row, the row's name, then the columns that differ
from the row struct's defaults.

```
Sword: Label="Blade" Damage=12 Reach.X=3 Tags=["steel","sharp"]
Shield: Defense=5 Parts=[Weight=2, Weight=3 Note="rim"]
Idle:
```

Rows are written as these lines: there is no JSON form. A text that opens with `[` or `{` is refused, and the refusal names
the line form and the columns. For a bulk import from CSV text, `run_python` calls
`unreal.DataTableFunctionLibrary.fill_data_table_from_csv_string(table, csv)` (it replaces the table's rows; the first CSV column
is the row name); then `read_asset(table, "Rows")` shows what it made.

Workflow:

1. `create_asset` a `DataTable` with `parent` the row struct (a native `FTableRowBase` struct such as
   `/Script/GameplayTags.GameplayTagTableRow`, or a User Defined Struct path; make its columns with the struct's `Fields`).
2. `read_asset(table, "Rows")`: a `# note:` line lists every column of the row struct, also when the table is empty.
3. `write_asset(table, "Rows", text)` with the whole table, or `edit_asset` on single lines.

Rules:

- `RowName: Column=value Column=value`. Columns are separated by spaces, in any order, named like `set_properties` names fields (any
  case, display names). A column left out is at its default; `Idle:` is a row with every column at its default. A row name
  that is not an identifier is quoted: `"Iron-Sword": Damage=3`. A new row name cannot hold a space, quote, comma, tab or line break and
  cannot be `None` (the engine would strip or reject it): the refusal gives a fixed name such as `IronSword`.
- A value is one token. Text, String and Name columns take quotes: `Label="Blade"`. Numbers, `true`/`false`, enum names
  and asset paths are bare (`Rarity=Rare`, `Mesh=/Game/Props/SM_Chair.SM_Chair`); a true bool reads as a bare `Column` (`Locked`), and a bool whose default is true and is false reads as `Column=false`.
  Anything with spaces, commas or parentheses goes in `"..."`, or in the brackets of its own value.
- A nested struct column is dotted, one member per item (`Reach.X=3`); a vector, rotator or colour with several members is grouped
  (`Pos=(X=1,Y=2,Z=3)`). An array of structs is its element records in brackets, comma separated, `()` for an
  element at its defaults (`Parts=[Weight=2, (), Weight=3 Note="rim"]`); any other array is JSON (`Tags=["a","b"]`).
- The text is the whole table. A row no line names is removed (the reply names it), a new name adds a row, and the rows end in
  the order of the lines. Reading prints the stored order, so a written order is kept.
- `[was="Old"]` after a row renames it and keeps its data and its place: `Blade: Damage=12 [was="Sword"]`. One rename at
  a time: a line cannot keep a name that another line renames away.
- A row whose line reads as it did is not touched, so it keeps the localization keys of its texts; in a row whose line changes,
  a text column whose text stays the same keeps its key too.
- An unknown column is refused with the row struct's columns and the close one; a value that does not fit says what the column takes
  and gives an example. A refused write changes nothing.
- A name that differs from a row's only in case renames the row to that case.
- A Composite DataTable takes no writes: its rows come from its parent tables, so a write is refused and a read says so; edit the parents.
- A write that changes nothing answers `No change.`.
