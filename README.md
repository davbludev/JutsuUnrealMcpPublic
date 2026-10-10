# Jutsu Unreal MCP

An Unreal Editor plugin that serves an MCP endpoint to a coding agent on the same machine. The
agent reads and edits assets as text, sets properties, calls functions, runs Python and console
commands, places actors, and plays and captures PIE.

## Install

1. Get **Jutsu Unreal MCP** on Fab and install it to your engine (Unreal Engine 5.5–5.8, Windows)
   through the Epic Games Launcher.
2. Open your project, enable **Jutsu Unreal MCP** in **Edit > Plugins** and restart the Editor.
3. The **Jutsu MCP** item in the status bar below the viewport shows the server: a green dot means
   it is running. Click it to change the port, copy the URL, or start, stop and restart the server.
4. Add the copied URL to your agent as a Streamable HTTP MCP server:

   ```text
   http://127.0.0.1:19782/mcp
   ```

The server listens on loopback only, with no authentication: any process on the machine can run
Python and console commands in the Editor through it. Do not expose the port through forwarding, a
proxy, a VPN or a container bridge.

## Agent skill

[`using-jutsu-unreal-mcp`](using-jutsu-unreal-mcp/SKILL.md) teaches an agent the asset-text formats
and the working ways around common mistakes. Copy the folder into your agent's skills directory (for
Claude Code, `~/.claude/skills/`).

## Support

Open a [GitHub Issue](https://github.com/davbludev/JutsuUnrealMcpPublic/issues) with your Unreal
Engine version, the status-bar state and port, the tool call, and the reply.

Jutsu Unreal MCP is an independent product and is not affiliated with, sponsored by, or endorsed by
Epic Games.
