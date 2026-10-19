# MetaSound

A MetaSound preset: create the asset, then write `"preset": {"parent": "<same-kind MetaSound>"}` with
its input overrides as `{"find": {"kind": "input", "name": "Gain"}, "default": 0.25}` nodes, in one
write or later ones (a later write may leave `preset` out). A MetaSound input
with a default: `{"create": {"kind": "input", "name": "Waves", "dataType": "WaveAsset:Array", "default": ["/Game/W.W"]}}` (`float`, lowercase).

A node's input defaults sit beside its `create`: `{"create": {...}, "defaults": {"Gain": 3}}`. To
change one on an existing node, remove the node in one write, then create it again in the next with
its `defaults` and its links under `connections`. An enum input takes an entry's name, short,
qualified or as displayed (`"Type": "Highpass"`); a wrong one fails listing the entries, and the
value reads back as the entry's number. A MetaSound `remove`
takes no `destructive`: `"X": {"remove": {"authoringId": "X"}}`.
