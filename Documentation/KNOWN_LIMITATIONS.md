# Known limitations

- Editor only, Windows 64-bit, Unreal Engine 5.8. The plugin does not load in commandlets or packaged games.
- One Play In Editor session at a time, in the Editor process. Multiplayer and separate-process PIE are not driven.
- Client cancellation cannot stop an operation running on the game thread. After a timeout, read the affected state before retrying.
- `get_log` returns a bounded window of recent Output Log lines, not the complete log file.
- In the Editor, a streaming sublevel that is part of the world is always loaded: the engine forces an editor world's unload request back to loaded-not-visible. To stop showing a sublevel, hide it; to unload it, remove it from the world. Load and unload at runtime is PIE and packaged-game behaviour.
- Asset types without a text section of their own are read and written as `Properties`; some offer a read-only `Details` section.
- `run_python` and `run_console_command` execute with the Editor's privileges; see [Network and security](NETWORK_AND_SECURITY.md).
