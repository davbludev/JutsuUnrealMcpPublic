# PIE and editor sessions

## Log lines of a session

`stop_pie` reports the log from where `start_pie` began the session, and the `get_log after=<n>` its reply names starts
there. A session started by hand in the editor is reported from the `stop_pie` call. `wait` ends with
`Wait ok: <seconds>s`.

## Multiplayer PIE

`start_pie` with `netMode` `listen` (the first player hosts) or `client` (a hidden dedicated server) and `players` runs
every player in the editor process and lists them as `pie:0`, `pie:1`, ... (`pie:<n>` is the `UEDPIE_<n>_` of that
player's object paths; `pie` means the one in the level viewport).

- Pass `world: "pie:<n>"` to `get_properties`, `set_properties`, `call_function`, `list_actors`, `run_console_command`,
  `send_input` and `take_screenshot` to act in that player's game.
- `set_properties` in a PIE world changes the value and keeps the actor's runtime state; in Simulate, a write to the
  actor's own properties reruns its construction script (engine behaviour), a write to one of its components does not.
- `spawn_actor` in PIE (not Simulate) sets `properties` before the construction script and BeginPlay (`AutoPossessAI`,
  `AutoPossessPlayer` apply); keys on components the Blueprint adds are set after BeginPlay.
- Replication check: set a replicated property on the server's actor (`pie:0`), `wait` a second or two, then read it on
  a client's with that client's `world`.
- Find an actor in each world by `list_actors` `class`: a replicated actor's name can differ between worlds.
- Place fixtures in the level before `start_pie`.
- Drive a client with `send_input` and its `world` (a key or an Enhanced Input action), the way a player does.
- Log lines carry `pie:<n>` while several instances run.
- Keys and UI in shots need the game view on screen: with the level viewport's tab behind another tab, `start_pie`
  plays in a new window, a shot says `UI not captured` and a `send_input` key is refused, naming why. An `action`
  reaches the player either way.

## Navigation

Right after a level opens, the editor world's navigation build stays locked until loading settles (at least 2 s, no
assets still compiling): a `RebuildNavigation` then logs `navigation build is locked (flags: 0x20)`. `wait` a few
seconds and run it again, or query paths in PIE.

## Which editor answers

A headless `UnrealEditor-Cmd` run of the same project serves the MCP port too; `get_editor_state` `pid` tells which
process answered.
