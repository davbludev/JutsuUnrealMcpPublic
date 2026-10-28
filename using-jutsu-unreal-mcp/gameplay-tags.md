# Gameplay tags

Gameplay tags: path `GameplayTags` (no asset). `Tags` (DefaultGameplayTags.ini) or
`Tags:<File>.ini`: `Tag.Name [comment="..."]`, `[was="Old.Tag"]` renames with a redirect;
`Redirects`: `Old.Tag -> New.Tag` (DefaultGameplayTags.ini only; redirects inside Config/Tags files
are not shown). A write is usable at once, no restart; never edit the ini by hand.

## Tags on a GameplayEffect

A GameplayEffect (UE 5.3+) keeps its tags in `GEComponents`; write them there. The top-level
`InheritableGameplayEffectTags`, `InheritableOwnedTagsContainer`, `*TagRequirements` and similar
fields are read-only mirrors the engine rebuilds from the components on save.

    set_properties {"object": "/Game/GAS/GE_Burn", "values": {"GEComponents": [
      {"class": "AssetTagsGameplayEffectComponent", "InheritableAssetTags": {"Added": ["Effect.Burn"]}}]}}

Send `Added` and `Removed`; the engine computes `CombinedTags` from them and the parent effect's
tags. `GEComponents` is written whole: read it with `get_properties` first and send back every component
the effect keeps, with the change. Granted tags: `TargetTagsGameplayEffectComponent`
(`InheritableGrantedTagsContainer`); tag requirements: `TargetTagRequirementsGameplayEffectComponent`;
blocked ability tags: `BlockAbilityTagsGameplayEffectComponent`. A `set_properties` reply with
`warnings` names each value the engine did not keep, and where a mirrored field's data lives.
