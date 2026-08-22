# Dependencies

## Unreal Engine

The initial Fab target is Unreal Engine 5.8 on Win64 Editor. The plugin declares the following required UE-supplied plugin dependencies in `JutsuUnrealMcp.uplugin`: GameplayTagsEditor, GameplayAbilities, EnhancedInput, StateTree, GameplayStateTree, SmartObjects, EnvironmentQueryEditor, GameplayInteractions, ControlRig, IKRig, Niagara, Metasound, LevelSequenceEditor, PCG, and AudioModulation.

All current plugin dependencies are expected to be present in the UE 5.8 installation; no user-made Unreal plugin is required. The module also links the UE modules declared by `Source/JutsuUnrealMcp/JutsuUnrealMcp.Build.cs`.

## Dependency maturity status

- `AudioModulation` is required and enabled because Jutsu links its public editor-authoring module API. Disabling it makes the corresponding Jutsu module dependency invalid.
- `PCG` is a mandatory UE 5.8 built-in dependency for PCG graph and component authoring.
- `GameplayInteractions` is an Experimental UE plugin.
- `NavCorridor`, reached transitively through Gameplay Interactions/navigation support, is Experimental.
- `PropertyBindingUtils`, used transitively by supported UE systems, is Beta.

Enable the listed dependencies only through the Unreal Plugin Browser or the supported project configuration. If a dependency is missing or disabled, use the troubleshooting steps rather than copying a plugin from an unrelated project.

## External interoperability

MCP is an external open protocol and MCP client applications are not included. The plugin redistributes no third-party source, binary, executable, Python package, or asset. See [Third-party notices](THIRD_PARTY_NOTICES.md).
