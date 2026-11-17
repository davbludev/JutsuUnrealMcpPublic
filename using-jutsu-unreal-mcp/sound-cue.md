# Sound Cue

Sound Cue `Graph`: `<id> WavePlayer {"SoundWaveAssetPtr":"/Game/S_Step.S_Step"}`, `<id> Random`,
`Mixer`, `Attenuation`... (the SoundNode class without its prefix), inputs as `0 = <id>` (by index, or
the input's name such as `True` on a Branch), then `Output = <id>`. ` [inputs=N]` keeps unlinked
inputs; a Random node's `Weights` take one value per input (left out, each is 1).

The Graph writes partially: a line with a problem is skipped and named under `not applied:`, with the lines
under its node and every line linking to it; the node of its id stays as it was, inputs and output link included. Links that loop refuse the whole write.
