# Gameplay Ability System

Gameplay Abilities (GA), Gameplay Effects (GE) and Gameplay Cue Notifies are Blueprints. Create them
with `create_asset` (`class` `GameplayEffect`, `GameplayAbility`, or a cue parent such as
`GameplayCueNotify_Static`, `GameplayCueNotify_Actor`), then author them as text:

- **`Defaults`** (`read_asset` / `write_asset` / `edit_asset`, section `Defaults`): the class defaults,
  one `Name = <json>` line per property that differs from the parent. This is where a GE's modifiers,
  executions, components and duration live, and a GA's tags, cost, cooldown and triggers.
- **Graphs** (`EventGraph`, functions): a GA's `ActivateAbility` logic, a cue's `OnExecute` and similar
  events, as the Blueprint graph text.
- **`Properties`** and `set_properties`/`get_properties` reach the same values by path
  (`Modifiers[0].ModifierOp`). Take `Defaults` to write several at once and to copy a read back; take
  `set_properties` for one member.

In a `Defaults` write a line you leave out is reset to the parent's value.

Attribute Sets are C++ classes or Blueprints: `create_asset` `class` `Blueprint`, `parent`
`/Script/GameplayAbilities.AttributeSet`, then `Variables` lines such as `Stamina: GameplayAttributeData`.

## Attribute references

Every attribute value (a modifier's `Attribute`, a capture's `AttributeToCapture`) takes one string:

    "Set.Attr"                              the attribute set class's name (a subclass of the declaring set works), then the attribute
    "Attr"                                  when exactly one loaded attribute set has it
    "/Script/MyGame.MyAttributeSet:Attr"    the full path

A read prints `Set.Attr` (the full path when two sets share a name). The cached name and owner the
engine keeps beside the path are filled for you: write the one string.

## Gameplay Effect

    Modifiers = [
      {"Attribute":"MyAttributeSet.Health","ModifierOp":"AddBase","ModifierMagnitude":{"MagnitudeCalculationType":"ScalableFloat","ScalableFloatMagnitude":{"Value":-25}}},
      {"Attribute":"MyAttributeSet.MoveSpeed","ModifierOp":"MultiplyAdditive","ModifierMagnitude":{"MagnitudeCalculationType":"SetByCaller","SetByCallerMagnitude":{"DataTag":"Data.Slow"}}},
      {"Attribute":"MyAttributeSet.Armor","ModifierOp":"AddFinal","ModifierMagnitude":{"MagnitudeCalculationType":"AttributeBased","AttributeBasedMagnitude":{"Coefficient":{"Value":0.5},"BackingAttribute":{"AttributeToCapture":"MyAttributeSet.Strength","AttributeSource":"Source","bSnapshot":false}}}},
      {"Attribute":"MyAttributeSet.Mana","ModifierOp":"AddBase","ModifierMagnitude":{"MagnitudeCalculationType":"CustomCalculationClass","CustomMagnitude":{"CalculationClassMagnitude":"/Game/GAS/MMC_ManaCost"}}}]
    DurationPolicy = "HasDuration"
    DurationMagnitude = {"MagnitudeCalculationType":"ScalableFloat","ScalableFloatMagnitude":{"Value":5}}
    Executions = [{"CalculationClass":"/Game/GAS/EC_Damage","CalculationModifiers":[]}]

- `ModifierOp`: `AddBase`, `MultiplyAdditive`, `DivideAdditive`, `MultiplyCompound`, `AddFinal`, `Override`.
- The `MagnitudeCalculationType` decides which sibling block is used: `ScalableFloat` ->
  `ScalableFloatMagnitude`, `AttributeBased` -> `AttributeBasedMagnitude`, `CustomCalculationClass` ->
  `CustomMagnitude`, `SetByCaller` -> `SetByCallerMagnitude` (`DataTag` or `DataName`). The other blocks
  keep their defaults and a read leaves them out.
- `EvaluationChannelSettings.Channel` (`Channel0` to `Channel9`) puts a modifier in an aggregation channel;
  an `AttributeBased` magnitude's `FinalChannel` is the channel its captured value is evaluated up to.
- Class values (`CalculationClass`, `CalculationClassMagnitude`, `CostGameplayEffectClass`) take the
  Blueprint's asset path (`/Game/GAS/EC_Damage`) or a native class path; a read prints the `_C` class path.
- `MaxDurationMagnitude` exists from UE 5.7; on 5.5 and 5.6 `get_properties` refuses it.

### Components

Tags, tag requirements, removal, immunity, granted abilities and additional effects live in
`GEComponents` (UE 5.3+), written whole with every component the effect keeps:

    GEComponents = [
      {"class":"AssetTagsGameplayEffectComponent","InheritableAssetTags":{"Added":["Effect.Burn"]}},
      {"class":"TargetTagsGameplayEffectComponent","InheritableGrantedTagsContainer":{"Added":["State.Burning"]}},
      {"class":"AdditionalEffectsGameplayEffectComponent","OnApplicationGameplayEffects":[{"EffectClass":"/Game/GAS/GE_Smoke"}]}]

Classes: `AssetTagsGameplayEffectComponent`, `TargetTagsGameplayEffectComponent`,
`TargetTagRequirementsGameplayEffectComponent` (`ApplicationTagRequirements`, `OngoingTagRequirements`,
`RemovalTagRequirements`), `BlockAbilityTagsGameplayEffectComponent`, `AbilitiesGameplayEffectComponent`
(`GrantAbilityConfigs`), `ImmunityGameplayEffectComponent`, `RemoveOtherGameplayEffectComponent`,
`AdditionalEffectsGameplayEffectComponent` (`OnApplicationGameplayEffects`, `OnCompleteAlways`,
`OnCompleteNormal`, `OnCompletePrematurely`). Send `Added` and `Removed` for a tag container; the engine
computes `CombinedTags`. Tags must exist: write them in the `GameplayTags` section first
([gameplay-tags.md](gameplay-tags.md)); an unregistered tag is dropped.

## Gameplay Ability

    AbilityTags = ["Ability.Fireball"]
    ActivationOwnedTags = ["State.Casting"]
    ActivationBlockedTags = ["State.Stunned"]
    CostGameplayEffectClass = "/Game/GAS/GE_FireballCost"
    CooldownGameplayEffectClass = "/Game/GAS/GE_FireballCooldown"
    AbilityTriggers = [{"TriggerTag":"Event.Fireball","TriggerSource":"GameplayEvent"}]
    InstancingPolicy = "InstancedPerActor"
    NetExecutionPolicy = "ServerOnly"

Ability tasks (`PlayMontageAndWait`, `WaitGameplayEvent`, ...) are latent nodes in the ability's graph;
write them with the Blueprint graph text and read the node line back for the pins.

## Gameplay Cue Notify

`create_asset` with a `GameplayCueNotify_*` parent, then `Defaults` for `GameplayCueTag` (a tag under
`GameplayCue.`) and the event graph for `OnExecute`, `OnActive`, `WhileActive` and `OnRemove`.
