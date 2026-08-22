# Installation

## Requirements

- Unreal Engine 5.8 installed through the Epic Games Launcher.
- Windows 64-bit Editor.
- A supported Streamable HTTP MCP client.
- The built-in Unreal plugin dependencies listed in [Dependencies](DEPENDENCIES.md).

## Fab/Launcher installation

Fab installs this Code Plugin as an engine plugin. Install the purchased or downloaded project version through the Fab/Launcher workflow, open a UE 5.8 project, and open **Edit > Plugins**. Search for **Jutsu Unreal MCP**, enable it, and restart the Editor when prompted.

After restart, open the **Jutsu MCP** item in the Level Editor status bar. It reports `Running`, `Stopped`, or `Error`, the active port, and the configured port. The **Start**, **Stop**, and **Restart** commands control the loopback listener. The plugin is disabled by default and does not run in commandlets.

## Configuration

Open **Edit > Editor Preferences > Plugins > Jutsu Unreal MCP** and set **Port** to a value from `1` through `65535`. The default is `19782`. Changing the setting does not interrupt a running listener; use **Restart** to apply it.

## Update or remove

Stop the server, close the Editor, then update or remove the engine plugin through the Fab/Launcher installation workflow. Do not mix a project-checkout copy with the engine-installed copy. Reopen the project and verify the plugin version and status-bar state after an update.
