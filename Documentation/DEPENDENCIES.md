# Dependencies

## Unreal Engine

This release supports Unreal Engine 5.8 on the Win64 Editor. The plugin enables the following UE-supplied plugins in `JutsuUnrealMcp.uplugin`: GameplayTagsEditor, GameplayAbilities, EnhancedInput, StateTree, GameplayStateTree, SmartObjects, EnvironmentQueryEditor, GameplayInteractions, ControlRig, IKRig, Niagara, Metasound, LevelSequenceEditor, PCG, AudioModulation, **PythonScriptPlugin** (Python Editor Script Plugin) and **EditorScriptingUtilities** (Editor Scripting Utilities).

All of them ship with Unreal Engine; no user-made plugin is required. The Python Editor Script Plugin supplies the Python interpreter that `run_python` uses. The module also links the UE modules declared by `Source/JutsuUnrealMcp/JutsuUnrealMcp.Build.cs`.

## Dependency maturity status

- `AudioModulation` is required because Jutsu links its editor-authoring module API.
- `GameplayInteractions` is an Experimental UE plugin.
- `NavCorridor`, reached transitively through Gameplay Interactions/navigation support, is Experimental.
- `PropertyBindingUtils`, used transitively by supported UE systems, is Beta.

Enable dependencies only through the Unreal Plugin Browser or the project configuration. If one is missing or disabled, follow [Troubleshooting](TROUBLESHOOTING.md) rather than copying a plugin from an unrelated project.

## External interoperability

MCP is an external open protocol and MCP client applications are not included. The plugin redistributes no third-party source, binary, executable, Python package, or asset. See [Third-party notices](THIRD_PARTY_NOTICES.md).
