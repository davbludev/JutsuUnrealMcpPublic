# Gameplay Ability System

Gameplay Abilities (GA), Gameplay Effects (GE) and Gameplay Cue Notifies are Blueprints. Create them
with `create_asset` (`class` `GameplayEffect`, `GameplayAbility`, or a cue parent such as
`GameplayCueNotify_Static`, `GameplayCueNotify_Actor`), then author them as text:

- **`Defaults`** (`read_asset` / `write_asset` / `edit_asset`, section `Defaults`): the class defaults,
  one `Name = value` line per property that differs from the parent, and an array of structs or objects
  (`Modifiers`, `Executions`, `GEComponents`, `AbilityTriggers`) as `Name =` with one indented line per
  element. This is where a GE's modifiers, executions, components and duration live, and a GA's tags,
  cost, cooldown and triggers.
- **Graphs** (`EventGraph`, functions): a GA's `ActivateAbility` logic, a cue's `OnExecute` and similar
  events, as the Blueprint graph text.
- **`Properties`** and `set_properties`/`get_properties` reach the same values by path
  (`Modifiers[0].ModifierOp`). Take `Defaults` to write several at once and to copy a read back; take
  `set_properties` for one member.

In a `Defaults` write a line you leave out is reset to the parent's value.

Attribute Sets are C++ classes or Blueprints: `create_asset` `class` `Blueprint`, `parent`
`/Script/GameplayAbilities.AttributeSet`, then `Variables` lines such as `Stamina: GameplayAttributeData`.

## Attribute references

Every attribute value (a modifier's `Attribute`, a capture's `AttributeToCapture`, a graph pin such as
`GetFloatAttribute`'s `Attribute = "MyAttributeSet.Health"`) takes one string:

    "Set.Attr"                              the attribute set class's name (a subclass of the declaring set works), then the attribute
    "Attr"                                  when exactly one loaded attribute set has it
    "/Script/MyGame.MyAttributeSet:Attr"    the full path

A read prints `Set.Attr` (the full path when two sets share a name). The cached name and owner the
engine keeps beside the path are filled for you: write the one string.

## Gameplay Effect

    Modifiers =
      Attribute=MyAttributeSet.Health Magnitude=-25
      Attribute=MyAttributeSet.MoveSpeed Op=MultiplyAdditive SetByCaller=Data.Slow
      Attribute=MyAttributeSet.Armor Op=AddFinal Coefficient=0.5 Capture=MyAttributeSet.Strength
      Attribute=MyAttributeSet.Mana Calculation=/Game/GAS/MMC_ManaCost
    DurationPolicy = "HasDuration"
    DurationMagnitude = {"ScalableFloatMagnitude":{"Value":5}}
    Executions =
      CalculationClass=/Game/GAS/EC_Damage

- One line is one element: `Field=value` items split at spaces, a value with spaces or commas in quotes. A
  modifier has short names: `Attribute`, `Op` (`ModifierOp`, default `AddBase`), `Kind` (the magnitude kind:
  `ScalableFloat` by default, `AttributeBased`, `CustomCalculationClass`, `SetByCaller`), and the value of
  each kind: `Magnitude` (ScalableFloat), `SetByCaller` (a data tag) or `SetByCallerName`, `Coefficient` and
  `Capture` (the captured attribute), `Calculation` (a calculation class). `SetByCaller`, `SetByCallerName`,
  `Capture` and `Calculation` set `Kind` themselves, and a read leaves it out (two of them for different kinds,
  or one with a contradicting `Kind`, are refused; a leftover value of another kind, such as a tag under
  `ScalableFloat`, reads by its long path). The long paths work too
  (`ModifierMagnitude.ScalableFloatMagnitude.Value=-25`), and any other field is written by name, nested members
  dotted. A field at its default is left out; `()` is an element with nothing changed. The lines are the whole
  array: a line you drop removes that element, and `Modifiers =` with no lines (or `Modifiers = []`) clears it.
  The JSON array form (`Modifiers = [{...}]`) is refused with this form named.
- A child Blueprint reads and writes each element against its parent's element at the same index: a line that
  repeats the parent's element is `()`, so list the elements in the parent's order.
- A mistake names its line and element: `line 3: Modifiers[1]: ... has no field 'Attribut' (fields: ...). Did
  you mean 'Attribute'?`, an unknown component class lists the component classes, a bad number says what a
  number is and gives an example.
- `EvaluationChannelSettings.Channel` (`Channel0` to `Channel9`) puts a modifier in an aggregation channel;
  an `AttributeBased` magnitude's `FinalChannel` is the channel its captured value is evaluated up to.
- Class values (`CalculationClass`, `CalculationClassMagnitude`, `CostGameplayEffectClass`) take the
  Blueprint's asset path (`/Game/GAS/EC_Damage`) or a native class path; a read prints the `_C` class path.
- `MaxDurationMagnitude` exists from UE 5.7; on 5.5 and 5.6 `get_properties` refuses it.

### Components

Tags, tag requirements, removal, immunity, granted abilities and additional effects live in
`GEComponents` (UE 5.3+), written whole with every component the effect keeps; each line leads with the
component class:

    GEComponents =
      AssetTagsGameplayEffectComponent InheritableAssetTags.Added=["Effect.Burn"]
      TargetTagsGameplayEffectComponent InheritableGrantedTagsContainer.Added=["State.Burning"]
      AdditionalEffectsGameplayEffectComponent OnApplicationGameplayEffects=[EffectClass=/Game/GAS/GE_Smoke]

An array inside a line is a bracket list of element records, split at commas
(`OnApplicationGameplayEffects=[EffectClass=/Game/GAS/GE_Smoke, EffectClass=/Game/GAS/GE_Fire]`).

Classes: `AssetTagsGameplayEffectComponent`, `TargetTagsGameplayEffectComponent`,
`TargetTagRequirementsGameplayEffectComponent` (`ApplicationTagRequirements`, `OngoingTagRequirements`,
`RemovalTagRequirements`), `BlockAbilityTagsGameplayEffectComponent`, `AbilitiesGameplayEffectComponent`
(`GrantAbilityConfigs`), `ImmunityGameplayEffectComponent`, `RemoveOtherGameplayEffectComponent`,
`AdditionalEffectsGameplayEffectComponent` (`OnApplicationGameplayEffects`, `OnCompleteAlways`,
`OnCompleteNormal`, `OnCompletePrematurely`). Send `Added` and `Removed` for a tag container; the engine
computes `CombinedTags`. Tags must exist: write them in the `GameplayTags` section first
([gameplay-tags.md](gameplay-tags.md)); a write naming an unregistered tag is refused.

## Gameplay Ability

    AbilityTags = ["Ability.Fireball"]
    ActivationOwnedTags = ["State.Casting"]
    ActivationBlockedTags = ["State.Stunned"]
    CostGameplayEffectClass = "/Game/GAS/GE_FireballCost"
    CooldownGameplayEffectClass = "/Game/GAS/GE_FireballCooldown"
    AbilityTriggers =
      TriggerTag=Event.Fireball TriggerSource=GameplayEvent
    InstancingPolicy = "InstancedPerActor"
    NetExecutionPolicy = "ServerOnly"

Ability tasks (`PlayMontageAndWait`, `WaitGameplayEvent`, ...) are latent nodes in the ability's graph;
write them with the Blueprint graph text and read the node line back for the pins.

## Gameplay Cue Notify

`create_asset` with a `GameplayCueNotify_*` parent, then `Defaults` for `GameplayCueTag` (a tag under
`GameplayCue.`) and the event graph for `OnExecute`, `OnActive`, `WhileActive` and `OnRemove`.
