# MetaSound

A MetaSound preset: create the asset, then write `"preset": {"parent": "<same-kind MetaSound>"}` with
input overrides as `{"find": {"kind": "input", "name": "Gain"}, "default": 0.25}` nodes. A MetaSound input
with a default: `{"create": {"kind": "input", "name": "Waves", "dataType": "WaveAsset:Array", "default": ["/Game/W.W"]}}` (`float`, lowercase).
