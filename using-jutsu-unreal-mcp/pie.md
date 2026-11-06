# PIE and editor sessions

## Multiplayer PIE

`start_pie` with `netMode` `listen` (the first player hosts) or `client` (a hidden dedicated server) and `players` runs
every player in the editor process and lists them as `pie:0`, `pie:1`, ... (`pie:<n>` is the `UEDPIE_<n>_` of that
player's object paths; `pie` means the one in the level viewport).

- Pass `world: "pie:<n>"` to `get_properties`, `set_properties`, `call_function`, `list_actors`, `run_console_command`,
  `send_input` and `take_screenshot` to act in that player's game.
- Replication check: set a replicated property on the server's actor (`pie:0`), `wait` a second or two, then read it on
  a client's with that client's `world`.
- Find an actor in each world by `list_actors` `class`: a replicated actor's name can differ between worlds.
- Place fixtures in the level before `start_pie`.
- Drive a client with `send_input` and its `world` (a key or an Enhanced Input action), the way a player does.
- Log lines carry `pie:<n>` while several instances run.

## Navigation

Right after a level opens, the editor world's navigation build stays locked until loading settles (at least 2 s, no
assets still compiling): a `RebuildNavigation` then logs `navigation build is locked (flags: 0x20)`. `wait` a few
seconds and run it again, or query paths in PIE.

## Which editor answers

A headless `UnrealEditor-Cmd` run of the same project serves the MCP port too; `get_editor_state` `pid` tells which
process answered.
