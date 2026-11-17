# Gameplay tags

Gameplay tags: path `GameplayTags` (no asset). `Tags` (DefaultGameplayTags.ini) or
`Tags:<File>.ini`: `Tag.Name [comment="..."]`, `[was="Old.Tag"]` renames with a redirect;
`Redirects`: `Old.Tag -> New.Tag` (DefaultGameplayTags.ini only; redirects inside Config/Tags files
are not shown). A write is usable at once, no restart; never edit the ini by hand.

`Tags` and `Redirects` write partially: a bad line (not a valid tag, a tag twice, a rename with nothing to rename, a
redirect without `->`) is skipped and named under `not applied:`, the tag or redirect it names kept as it was (also the
old tag of a `was=` written without its quotes); a tag
left out that assets still use stays and is named too. The other lines are written. The ini files have no undo.
