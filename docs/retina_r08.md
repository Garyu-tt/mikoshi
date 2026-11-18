# R08: source-verified clustered sampler, no fabricated microtiles

## Real failure of R07

The real `ClusteredRetinalCircuitR239.accept` needs `sampler.tile_ids`.
The previous R07 implementation instantiated `StaggeredRetinalSamplerR228`,
which has no such method. A real execution on the legacy source host raised
`AttributeError` before any successful neural phase. Local mock-based tests
had not detected this incompatibility.

## Correct original dependency chain

`RetinalMosaic R180 -> NeuralRetina R182 -> FastNeuralRetina R188`

`StaggeredRetinalSampler R228 -> ClusteredRetinalSampler R238`

`R188 + R238 -> ClusteredRetinalCircuit R239`

R238 is an ORIGINAL historical source, not a new reimplementation. It exports
`ClusteredRetinalSamplerR238` and `tile_ids(epoch, phase)`.
The adapter requires the six original Python files via `MIKOSHI_RETINA_LEGACY_DIR`.
The new R238 source pin is SHA-256:
`168c85e01778ba3652488944fbd5be435f941db7d3708079dccfdf388732c3eb`.
All six source pins are checked before original code is imported.

## Authentic experimental evidence

On 2026-11-18, only in a temporary `/tmp/` Python 3.13 environment on
legacy mirbi-linux (NumPy 2.3.5), with original source files:

- R228 direct sampler with R239 failed: missing `tile_ids`.
- R238 sampler + R239 passed 20 phases of two 32x32 eyes.
- Each phase sampled eight full 8x8 tiles (512 receptors).
- The first four phases selected 2,048 unique receptor positions.
- After 20 phases, model produced 1,357 8-byte optic spike events.
- Tested UIDs were within the real optic axon range; offsets <= 33,000us.
- Meta flags stated `image_reconstructed=false`,
  `whole_visual_field_not_updated_this_phase=true`.

Inputs were **synthetic test irradiance** (0/255/80/220 intensity cycle), not
live camera imagery. Proof establishes original sampled neural execution,
NOT a full 920x920 speed result, Windows camera connection or full Engram
checkpoint/restart equivalence. VM121 deployment and Chromium UI remain undone.

## State safety, research

The original R239 Engram schema is now `mikoshi.retina-r239-state.v2`.
The six pinned sources and R238 sampling plan must match. R07 v1 specimens
are deliberately NOT auto-migrated, because the previous sampler construction
could not have produced an original R239 continuous run. The separate research
Engram still carries graph/history, not an invented biological state.

R257 stereo inference and physical spinal motor commands remain gated off.
LiDAR/rays remain distinct sensors; they must not be labeled as photons.

## Staging verification command

With originals staged on a trusted machine with dedicated NumPy environment:

```sh
MIKOSHI_RETINA_LEGACY_DIR=/path/to/verified/originals \
  python -m tools.smoke_r239_original
```

The script compares an uninterrupted R239 run with a resumed instance after
verified Engram restore using test RGB input; it does not read camera data.
Do not mark original checkpoint roundtrip as passed until this command succeeds.
